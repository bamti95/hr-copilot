"""채용공고 분석용 지식 소스의 등록, 인덱싱, 검색을 담당한다.

법령, 가이드, 사례 문서를 업로드하거나 시드 데이터로 적재한 뒤,
텍스트 추출과 청킹, 임베딩 생성을 거쳐 검색 가능한 지식 베이스로 만든다.
"""

from __future__ import annotations

import hashlib
import asyncio
import logging
import math
import mimetypes
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.document_types import ALLOWED_EXTENSIONS, FILES_PREFIX, READ_CHUNK_SIZE
from common.file_storage import (
    build_public_file_path,
    build_stored_filename,
    get_extension,
    get_upload_root,
    resolve_absolute_path,
    strip_extension,
)
from common.file_util import extract_text_from_file
from core.database import AsyncSessionLocal
from models.ai_job import AiJob, AiJobStatus, AiJobTargetType, AiJobType
from models.job_posting_knowledge_chunk import (
    JobPostingKnowledgeChunk,
    JobPostingKnowledgeChunkType,
)
from models.job_posting_knowledge_source import (
    JobPostingKnowledgeSource,
    JobPostingKnowledgeSourceType,
    KnowledgeProcessStatus,
)
from repositories.job_posting_knowledge_repository import (
    JobPostingKnowledgeChunkRepository,
    JobPostingKnowledgeSourceRepository,
)
from schemas.job_posting import (
    JobPostingAiJobResponse,
    KnowledgeChunkListResponse,
    KnowledgeChunkResponse,
    KnowledgeIndexResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    KnowledgeSeedResponse,
    KnowledgeSourceCreateRequest,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)
from services.job_posting_embedding_service import (
    EMBEDDING_DIM,
    current_embedding_model_name,
    embed_text as embed_text_with_model,
)


SOURCE_DATA_DIR = Path("backend/sample_data/source_data")
KNOWLEDGE_UPLOAD_DIR = "job_posting_knowledge"
LOCAL_EMBEDDING_MODEL = "BAAI/bge-m3"
MAX_CHUNK_CHARS = 1000
MIN_CHUNK_CHARS = 180
SEED_SOURCE_EXTENSIONS = {".pdf", ".txt"}
logger = logging.getLogger(__name__)


class JobPostingKnowledgeService:
    """채용공고 지식 베이스 운영 서비스다."""

    @staticmethod
    def _job_response(job: AiJob, message: str) -> JobPostingAiJobResponse:
        """AI 작업 엔터티를 API 응답 형태로 변환한다."""
        return JobPostingAiJobResponse(
            job_id=job.id,
            status=job.status,
            job_type=job.job_type,
            target_type=job.target_type,
            target_id=job.target_id,
            progress=job.progress,
            current_step=job.current_step,
            error_message=job.error_message,
            request_payload=job.request_payload,
            result_payload=job.result_payload,
            message=message,
        )

    @staticmethod
    async def upload_source(
        *,
        db: AsyncSession,
        upload_file: UploadFile,
        source_type: str | None,
        title: str | None,
        version_label: str | None,
        source_url: str | None,
        actor_id: int | None,
    ) -> KnowledgeSourceResponse:
        """지식 소스 파일을 업로드하고 메타데이터를 등록한다."""
        saved = await _save_knowledge_upload(upload_file)
        request = KnowledgeSourceCreateRequest(
            source_type=source_type,
            title=title or saved["title"],
            source_name=saved["original_file_name"],
            source_url=source_url,
            version_label=version_label,
            file_path=saved["file_path"],
            file_ext=saved["file_ext"],
            mime_type=saved["mime_type"],
            file_size=saved["file_size"],
            metadata={"upload_mode": "manager_upload"},
        )
        source = await JobPostingKnowledgeService.create_or_update_source(
            db=db,
            request=request,
            actor_id=actor_id,
        )
        return KnowledgeSourceResponse.from_entity(source)

    @staticmethod
    async def create_or_update_source(
        *,
        db: AsyncSession,
        request: KnowledgeSourceCreateRequest,
        actor_id: int | None,
    ) -> JobPostingKnowledgeSource:
        """같은 파일 경로가 있으면 갱신하고, 없으면 새 소스를 만든다."""
        source_repo = JobPostingKnowledgeSourceRepository(db)
        source_type = request.source_type or infer_source_type(
            request.title or request.source_name or request.file_path
        )
        title = request.title or request.source_name or Path(request.file_path).name
        existing = await source_repo.find_by_file_path(request.file_path)
        if existing:
            existing.source_type = source_type
            existing.title = title
            existing.source_name = request.source_name
            existing.source_url = request.source_url
            existing.version_label = request.version_label
            existing.file_ext = request.file_ext
            existing.mime_type = request.mime_type
            existing.file_size = request.file_size
            existing.metadata_json = request.metadata
            source = existing
        else:
            source = JobPostingKnowledgeSource(
                source_type=source_type,
                title=title,
                source_name=request.source_name,
                source_url=request.source_url,
                version_label=request.version_label,
                file_path=request.file_path,
                file_ext=request.file_ext,
                mime_type=request.mime_type,
                file_size=request.file_size,
                extract_status=KnowledgeProcessStatus.PENDING.value,
                index_status=KnowledgeProcessStatus.PENDING.value,
                chunk_count=0,
                metadata_json=request.metadata,
                created_by=actor_id,
            )
            await source_repo.add(source)
        await source_repo.flush()
        await db.commit()
        await source_repo.refresh(source)
        return source

    @staticmethod
    async def index_source(
        *,
        db: AsyncSession,
        source_id: int,
    ) -> KnowledgeIndexResponse:
        """한 개의 지식 소스를 추출, 청킹, 임베딩까지 인덱싱한다."""
        source_repo = JobPostingKnowledgeSourceRepository(db)
        chunk_repo = JobPostingKnowledgeChunkRepository(db)
        source = await source_repo.find_by_id_not_deleted(source_id)
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source was not found.",
            )

        source.extract_status = KnowledgeProcessStatus.PROCESSING.value
        source.index_status = KnowledgeProcessStatus.PROCESSING.value
        await db.commit()

        try:
            result = await asyncio.to_thread(
                extract_text_from_file,
                source.file_path or "",
                source.file_ext,
            )
            source.extracted_text = result.extracted_text
            source.extract_status = result.extract_status
            source.metadata_json = {
                **(source.metadata_json or {}),
                "extract_meta": result.extract_meta,
                "extract_strategy": result.extract_strategy,
                "extract_quality_score": result.extract_quality_score,
            }
            llm_error = (result.extract_meta or {}).get("llm_error")
            if llm_error:
                logger.warning(
                    "Job posting knowledge LLM normalization failed source_id=%s error=%s",
                    source_id,
                    llm_error,
                )
            if result.extract_status != KnowledgeProcessStatus.SUCCESS.value or not result.extracted_text:
                source.index_status = KnowledgeProcessStatus.FAILED.value
                source.chunk_count = 0
                source.metadata_json = {
                    **(source.metadata_json or {}),
                    "index_error": "Text extraction failed or produced empty text.",
                }
                logger.warning(
                    "Job posting knowledge extraction failed source_id=%s strategy=%s meta=%s",
                    source_id,
                    result.extract_strategy,
                    result.extract_meta,
                )
                await db.commit()
                await source_repo.refresh(source)
                return KnowledgeIndexResponse(
                    source=KnowledgeSourceResponse.from_entity(source),
                    chunk_count=0,
                )

            await chunk_repo.delete_by_source_id(source.id)
            chunks = await asyncio.to_thread(
                build_chunks_for_source,
                source,
                result.extracted_text,
            )
            for chunk in chunks:
                await chunk_repo.add(chunk)
            source.chunk_count = len(chunks)
            source.index_status = KnowledgeProcessStatus.SUCCESS.value
            await db.commit()
            await source_repo.refresh(source)
            return KnowledgeIndexResponse(
                source=KnowledgeSourceResponse.from_entity(source),
                chunk_count=len(chunks),
            )
        except Exception as exc:
            logger.exception(
                "Job posting knowledge indexing failed source_id=%s",
                source_id,
            )
            await db.rollback()
            source = await source_repo.find_by_id_not_deleted(source_id)
            if source is not None:
                source.extract_status = KnowledgeProcessStatus.FAILED.value
                source.index_status = KnowledgeProcessStatus.FAILED.value
                source.metadata_json = {
                    **(source.metadata_json or {}),
                    "index_error": str(exc),
                }
                await db.commit()
                await source_repo.refresh(source)
                return KnowledgeIndexResponse(
                    source=KnowledgeSourceResponse.from_entity(source),
                    chunk_count=0,
                )
            raise

    @staticmethod
    async def submit_index_source_job(
        *,
        db: AsyncSession,
        source_id: int,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        """지식 소스 인덱싱 백그라운드 작업을 생성한다."""
        source_repo = JobPostingKnowledgeSourceRepository(db)
        source = await source_repo.find_by_id_not_deleted(source_id)
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source was not found.",
            )
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_KNOWLEDGE_INDEXING.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.KNOWLEDGE_SOURCE.value,
            target_id=source.id,
            progress=2,
            current_step="knowledge_index_job_created",
            request_payload={
                "mode": "SOURCE",
                "source_id": source.id,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobPostingKnowledgeService._job_response(
            job,
            "지식 소스 인덱싱 작업이 시작되었습니다.",
        )

    @staticmethod
    async def submit_seed_source_data_job(
        *,
        db: AsyncSession,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        """sample_data 기반 시드 적재 작업을 생성한다."""
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_KNOWLEDGE_INDEXING.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.KNOWLEDGE_SOURCE.value,
            progress=2,
            current_step="knowledge_seed_job_created",
            request_payload={"mode": "SEED_SOURCE_DATA"},
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobPostingKnowledgeService._job_response(
            job,
            "샘플 지식 소스 일괄 인덱싱 작업이 시작되었습니다.",
        )

    @staticmethod
    async def get_index_job(
        *,
        db: AsyncSession,
        job_id: int,
    ) -> JobPostingAiJobResponse:
        """지식 인덱싱 작업의 단건 상태를 조회한다."""
        result = await db.execute(
            select(AiJob).where(
                AiJob.id == job_id,
                AiJob.job_type == AiJobType.JOB_POSTING_KNOWLEDGE_INDEXING.value,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge indexing job was not found.",
            )
        return JobPostingKnowledgeService._job_response(job, "지식 소스 인덱싱 작업 상태입니다.")

    @staticmethod
    async def get_active_index_job(
        *,
        db: AsyncSession,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse | None:
        """현재 진행 중인 지식 인덱싱 작업이 있으면 반환한다."""
        conditions = [
            AiJob.job_type == AiJobType.JOB_POSTING_KNOWLEDGE_INDEXING.value,
            AiJob.status.in_(
                [
                    AiJobStatus.QUEUED.value,
                    AiJobStatus.RUNNING.value,
                    AiJobStatus.RETRYING.value,
                ]
            ),
        ]
        if actor_id is not None:
            conditions.append(AiJob.requested_by == actor_id)

        result = await db.execute(
            select(AiJob)
            .where(*conditions)
            .order_by(desc(AiJob.created_at), desc(AiJob.id))
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None
        return JobPostingKnowledgeService._job_response(
            job,
            "Knowledge indexing job status.",
        )

    @staticmethod
    async def run_index_job(job_id: int) -> None:
        """백그라운드 인덱싱 작업의 실제 실행 진입점이다."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AiJob).where(AiJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                logger.warning("Knowledge indexing job not found: %s", job_id)
                return

            try:
                payload = job.request_payload or {}
                mode = payload.get("mode")
                job.status = AiJobStatus.RUNNING.value
                job.progress = 10
                job.current_step = "knowledge_index_started"
                job.started_at = job.started_at or datetime.now(timezone.utc)
                await db.commit()

                if mode == "SOURCE":
                    result_payload = await JobPostingKnowledgeService.index_source(
                        db=db,
                        source_id=int(payload["source_id"]),
                    )
                    if result_payload.source.index_status != KnowledgeProcessStatus.SUCCESS.value:
                        raise ValueError(
                            (
                                result_payload.source.metadata or {}
                            ).get("index_error")
                            or "Knowledge source indexing failed."
                        )
                    job.target_id = result_payload.source.id
                    job.result_payload = {
                        "source_id": result_payload.source.id,
                        "chunk_count": result_payload.chunk_count,
                        "extract_status": result_payload.source.extract_status,
                        "index_status": result_payload.source.index_status,
                    }
                elif mode == "SEED_SOURCE_DATA":
                    seed_result = await JobPostingKnowledgeService.seed_source_data(
                        db=db,
                        actor_id=job.requested_by,
                    )
                    job.result_payload = seed_result.model_dump(mode="json")
                else:
                    raise ValueError(f"Unsupported knowledge indexing mode: {mode}")

                job.status = AiJobStatus.SUCCESS.value
                job.progress = 100
                job.current_step = "knowledge_index_completed"
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as exc:
                logger.exception("Knowledge indexing job failed. job_id=%s", job_id)
                await db.rollback()
                result = await db.execute(select(AiJob).where(AiJob.id == job_id))
                failed_job = result.scalar_one_or_none()
                if failed_job is not None:
                    failed_job.status = AiJobStatus.FAILED.value
                    failed_job.progress = 100
                    failed_job.current_step = "knowledge_index_failed"
                    failed_job.error_message = str(exc)
                    failed_job.completed_at = datetime.now(timezone.utc)
                    await db.commit()

    @staticmethod
    async def list_sources(
        *,
        db: AsyncSession,
        page: int,
        size: int,
        source_type: str | None,
        keyword: str | None,
    ) -> KnowledgeSourceListResponse:
        """등록된 지식 소스 목록을 페이지 단위로 반환한다."""
        repo = JobPostingKnowledgeSourceRepository(db)
        total_count = await repo.count_list(source_type=source_type, keyword=keyword)
        rows = await repo.find_list(
            page=page,
            size=size,
            source_type=source_type,
            keyword=keyword,
        )
        total_pages = math.ceil(total_count / size) if total_count else 0
        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def list_chunks(
        *,
        db: AsyncSession,
        source_id: int,
        limit: int,
    ) -> KnowledgeChunkListResponse:
        """특정 소스에 속한 청크 목록을 조회한다."""
        source_repo = JobPostingKnowledgeSourceRepository(db)
        source = await source_repo.find_by_id_not_deleted(source_id)
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source was not found.",
            )
        chunk_repo = JobPostingKnowledgeChunkRepository(db)
        chunks = await chunk_repo.find_by_source_id(source_id, limit=limit)
        return KnowledgeChunkListResponse(
            items=[KnowledgeChunkResponse.from_entity(chunk) for chunk in chunks],
            total_count=len(chunks),
        )

    @staticmethod
    async def seed_source_data(
        *,
        db: AsyncSession,
        actor_id: int | None,
    ) -> KnowledgeSeedResponse:
        """sample_data/source_data의 문서를 지식 소스로 일괄 등록한다."""
        indexed_sources: list[KnowledgeSourceResponse] = []
        total_chunks = 0
        seed_files = collect_seed_source_files(SOURCE_DATA_DIR)
        latest_flags = compute_latest_flags(seed_files)
        for path in seed_files:
            public_file = _ensure_seed_file_under_upload_root(path)
            effective_date = extract_effective_date_from_text(path.name)
            request = KnowledgeSourceCreateRequest(
                source_type=infer_source_type(path.name),
                title=canonical_source_title(path),
                source_name=path.name,
                file_path=public_file,
                file_ext=path.suffix.removeprefix(".").lower(),
                mime_type=mimetypes.guess_type(path.name)[0] or "text/plain",
                file_size=path.stat().st_size,
                metadata={
                    "upload_mode": "seed_source_data",
                    "original_path": path.as_posix(),
                    "doc_id": build_seed_doc_id(path),
                    "effective_date": effective_date,
                    "is_latest": latest_flags.get(path.as_posix(), True),
                },
            )
            source = await JobPostingKnowledgeService.create_or_update_source(
                db=db,
                request=request,
                actor_id=actor_id,
            )
            result = await JobPostingKnowledgeService.index_source(db=db, source_id=source.id)
            indexed_sources.append(result.source)
            total_chunks += result.chunk_count

        return KnowledgeSeedResponse(
            indexed_sources=indexed_sources,
            total_sources=len(indexed_sources),
            total_chunks=total_chunks,
        )

    @staticmethod
    async def search_knowledge(
        *,
        db: AsyncSession,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        """지식 청크를 키워드와 벡터 기준으로 검색한다."""
        query_terms = extract_query_terms(request.query)
        query_embedding = embed_text(request.query)
        chunk_repo = JobPostingKnowledgeChunkRepository(db)
        pool = await chunk_repo.find_search_pool(
            query_terms=query_terms,
            limit=max(request.limit * 30, 200),
        )
        if not pool:
            pool = await chunk_repo.find_search_pool(query_terms=[], limit=500)

        search_mode = request.search_mode.upper()
        scored: list[dict[str, Any]] = []
        for chunk in pool:
            keyword_score, matched_terms = calculate_keyword_score(
                query_terms=query_terms,
                chunk=chunk,
            )
            vector_score = cosine_similarity(
                query_embedding,
                normalize_embedding(chunk.embedding),
            )
            if search_mode == "KEYWORD":
                hybrid_score = keyword_score
            elif search_mode == "VECTOR":
                hybrid_score = vector_score
            else:
                hybrid_score = (keyword_score * 0.45) + (vector_score * 0.55)
            source = getattr(chunk, "knowledge_source", None)
            source_priority = document_priority(getattr(source, "source_type", "") or "")
            scored.append(
                {
                    "chunk": chunk,
                    "keyword_score": round(keyword_score, 4),
                    "vector_score": round(vector_score, 4),
                    "hybrid_score": round(hybrid_score + (0.01 / source_priority), 4),
                    "matched_terms": matched_terms,
                }
            )

        scored.sort(key=lambda item: item["hybrid_score"], reverse=True)
        results = [
            KnowledgeSearchResult(
                chunk=KnowledgeChunkResponse.from_entity(item["chunk"]),
                keyword_score=item["keyword_score"],
                vector_score=item["vector_score"],
                hybrid_score=item["hybrid_score"],
                matched_terms=item["matched_terms"],
            )
            for item in scored[: request.limit]
        ]
        return KnowledgeSearchResponse(
            query=request.query,
            search_mode=search_mode,
            embedding_model=current_embedding_model_name(),
            result_count=len(results),
            results=results,
        )


def infer_source_type(name: str | None) -> str:
    text = (name or "").lower()
    if "지도점검" in text or "점검결과" in text:
        return JobPostingKnowledgeSourceType.INSPECTION_CASE.value
    if "가이드북" in text:
        return JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value
    if "업무 매뉴얼" in text or "매뉴얼" in text:
        return JobPostingKnowledgeSourceType.LEGAL_MANUAL.value
    if "법률" in text or "시행령" in text or "시행규칙" in text:
        return JobPostingKnowledgeSourceType.LAW_TEXT.value
    if "risk" in text or "dataset" in text:
        return JobPostingKnowledgeSourceType.EXCEL_RISK_DATASET.value
    return JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value


def build_chunks_for_source(
    source: JobPostingKnowledgeSource,
    extracted_text: str,
) -> list[JobPostingKnowledgeChunk]:
    sections = split_legal_text(extracted_text, source.source_type)
    chunks: list[JobPostingKnowledgeChunk] = []
    doc_id = resolve_doc_id(source)
    section_counters: dict[str, int] = {}
    for index, section in enumerate(sections):
        content = section["content"].strip()
        if not content:
            continue
        section_ref = section.get("article_ref") or section.get("chunk_key") or f"section-{index + 1}"
        section_counters[section_ref] = section_counters.get(section_ref, 0) + 1
        chunk_no = section_counters[section_ref]
        chunk_key = f"{doc_id}::{section_ref}::{chunk_no:02d}"
        content_hash = hashlib.sha256(f"{source.id}:{index}:{content}".encode("utf-8")).hexdigest()
        chunk = JobPostingKnowledgeChunk(
            knowledge_source_id=source.id,
            chunk_type=section["chunk_type"],
            chunk_key=chunk_key,
            chunk_index=len(chunks),
            page_start=section.get("page_start"),
            page_end=section.get("page_end"),
            section_title=section.get("section_title"),
            content=content,
            summary=summarize_chunk(content),
            issue_code=infer_issue_code(content),
            risk_category=infer_risk_category(content),
            severity=infer_severity(content),
            law_name=infer_law_name(content, source.title),
            article_no=infer_article_no(content),
            penalty_guide=infer_penalty_guide(content),
            violation_text=None,
            violation_reason=None,
            correction_suggestion=None,
            tags=infer_tags(content),
            metadata_json={
                "doc_id": doc_id,
                "doc_name": source.title,
                "source_title": source.title,
                "source_type": source.source_type,
                "doc_type": map_doc_type(source.source_type),
                "article_ref": section.get("article_ref"),
                "section_title": section.get("section_title"),
                "effective_date": extract_effective_date(source),
                "is_latest": resolve_is_latest(source),
                "page": section.get("page_start"),
                "topic_tags": infer_tags(content),
                "document_priority": document_priority(source.source_type),
                "chunking_strategy": section.get("chunking_strategy"),
            },
            embedding_model=current_embedding_model_name(),
            embedding=embed_text(content),
            content_hash=content_hash,
            token_count=estimate_token_count(content),
            use_tf="Y",
            del_tf="N",
        )
        chunks.append(chunk)
    return chunks


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")[:255]


def summarize_chunk(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:280]


def infer_law_name(text: str, fallback: str | None) -> str | None:
    for law_name in [
        "채용절차의 공정화에 관한 법률",
        "남녀고용평등과 일ㆍ가정 양립 지원에 관한 법률",
        "고용상 연령차별금지 및 고령자고용촉진에 관한 법률",
        "장애인고용촉진 및 직업재활법",
        "근로기준법",
    ]:
        if law_name in text or law_name in (fallback or ""):
            return law_name
    return fallback[:255] if fallback else None


def infer_issue_code(text: str) -> str | None:
    checks = [
        ("FALSE_JOB_AD", ["거짓 채용광고", "거짓 구인광고", "허위"]),
        ("UNFAVORABLE_CONDITION_CHANGE", ["근로조건", "불리", "변경"]),
        ("IRRELEVANT_PERSONAL_INFO", ["혼인", "가족", "키", "체중", "용모", "사진", "출신지역"]),
        ("GENDER_DISCRIMINATION", ["남녀", "성별", "여성", "남성"]),
        ("AGE_DISCRIMINATION", ["연령", "나이", "고령자"]),
        ("PHYSICAL_CONDITION", ["신체", "용모", "키", "체중"]),
        ("WORKING_CONDITION_AMBIGUITY", ["야근", "연장근로", "출장", "수당"]),
    ]
    for code, keywords in checks:
        if any(keyword in text for keyword in keywords):
            return code
    return None


def infer_risk_category(text: str) -> str | None:
    code = infer_issue_code(text)
    if code in {
        "FALSE_JOB_AD",
        "UNFAVORABLE_CONDITION_CHANGE",
        "IRRELEVANT_PERSONAL_INFO",
        "GENDER_DISCRIMINATION",
        "AGE_DISCRIMINATION",
        "PHYSICAL_CONDITION",
        "WORKING_CONDITION_AMBIGUITY",
    }:
        return "LEGAL"
    return "GUIDE"


def infer_severity(text: str) -> str | None:
    if any(keyword in text for keyword in ["징역", "벌금", "과태료", "금지"]):
        return "HIGH"
    if any(keyword in text for keyword in ["권고", "개선", "노력"]):
        return "MEDIUM"
    return None


def infer_penalty_guide(text: str) -> str | None:
    sentences = re.split(r"(?:\.\s+|。\s+|다\.\s+|\n+)", text)
    for sentence in sentences:
        if any(keyword in sentence for keyword in ["징역", "벌금", "과태료", "시정명령"]):
            return sentence[:500]
    return None


def infer_tags(text: str) -> list[str]:
    tags = []
    for tag, keywords in {
        "거짓채용광고": ["거짓 채용광고", "허위"],
        "개인정보": ["혼인", "가족", "출신지역", "사진"],
        "신체조건": ["키", "체중", "용모", "신체"],
        "성별차별": ["성별", "남녀", "여성", "남성"],
        "연령차별": ["연령", "나이", "고령자"],
        "근로조건": ["근로조건", "수당", "연장근로", "출장"],
    }.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    return tags


def document_priority(source_type: str) -> int:
    priorities = {
        JobPostingKnowledgeSourceType.LAW_TEXT.value: 1,
        JobPostingKnowledgeSourceType.LEGAL_MANUAL.value: 2,
        JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value: 3,
        JobPostingKnowledgeSourceType.INSPECTION_CASE.value: 4,
    }
    return priorities.get(source_type, 9)


def estimate_token_count(text: str) -> int:
    return max(1, len(text) // 3)


def extract_query_terms(query: str) -> list[str]:
    terms = re.findall(r"[0-9A-Za-z가-힣]+", query.lower())
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        if len(term) < 2 or term in seen:
            continue
        seen.add(term)
        result.append(term)
    return result[:20]


def calculate_keyword_score(
    *,
    query_terms: list[str],
    chunk: JobPostingKnowledgeChunk,
) -> tuple[float, list[str]]:
    if not query_terms:
        return 0.0, []
    haystack = " ".join(
        [
            chunk.content or "",
            chunk.summary or "",
            chunk.issue_code or "",
            chunk.risk_category or "",
            chunk.law_name or "",
            chunk.article_no or "",
            " ".join(chunk.tags or []),
        ]
    ).lower()
    matched_terms = [term for term in query_terms if term in haystack]
    if not matched_terms:
        return 0.0, []
    coverage = len(matched_terms) / max(len(query_terms), 1)
    density = min(
        1.0,
        sum(haystack.count(term) for term in matched_terms)
        / max(len(query_terms) * 2, 1),
    )
    return round((coverage * 0.7) + (density * 0.3), 4), matched_terms


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if not left_norm or not right_norm:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def normalize_embedding(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, tuple):
        return [float(item) for item in value]
    if hasattr(value, "tolist"):
        return [float(item) for item in value.tolist()]
    try:
        return [float(item) for item in value]
    except TypeError:
        return []


def embed_text(text: str) -> list[float]:
    return embed_text_with_model(text)


def split_legal_text(text: str, source_type: str) -> list[dict[str, Any]]:
    normalized = normalize_chunk_source_text(text)
    if not normalized:
        return []
    if source_type == JobPostingKnowledgeSourceType.LAW_TEXT.value:
        return split_by_article(normalized)
    if source_type == JobPostingKnowledgeSourceType.INSPECTION_CASE.value:
        return split_by_case_blocks(normalized)
    return split_by_heading_or_window(normalized)


def split_by_article(text: str) -> list[dict[str, Any]]:
    article_pattern = re.compile(
        r"(?=^\s*제\s*\d+\s*조(?:\s*의\s*\d+)?(?:\s*\([^)]+\))?)",
        re.MULTILINE,
    )
    parts = [part.strip() for part in article_pattern.split(text) if part.strip()]
    if len(parts) <= 1:
        parts = split_to_limit(text)

    sections: list[dict[str, Any]] = []
    for fallback_index, part in enumerate(parts, start=1):
        article_ref = infer_article_no(part) or f"article-{fallback_index}"
        section_title = first_line(part)
        for content in split_legal_article_detail(part):
            sections.append(
                {
                    "chunk_type": JobPostingKnowledgeChunkType.LEGAL_CLAUSE.value,
                    "chunk_key": article_ref,
                    "article_ref": article_ref,
                    "section_title": section_title,
                    "content": with_section_prefix(section_title, content),
                    "chunking_strategy": "law_article_then_paragraph_item",
                }
            )
    return sections


def split_by_case_blocks(text: str) -> list[dict[str, Any]]:
    case_pattern = re.compile(
        r"(?=^\s*(?:사례|Case|CASE|점검\s*사례|위반\s*사례)\s*[\dIVXivx가-힣-]*)",
        re.MULTILINE,
    )
    parts = [part.strip() for part in case_pattern.split(text) if part.strip()]
    if len(parts) <= 1:
        parts = split_to_limit(text)

    sections: list[dict[str, Any]] = []
    for idx, part in enumerate(parts, start=1):
        case_ref = f"case-{idx}"
        section_title = first_line(part) or f"사례 {idx}"
        for content in split_to_limit(part):
            sections.append(
                {
                    "chunk_type": JobPostingKnowledgeChunkType.INSPECTION_CASE.value,
                    "chunk_key": case_ref,
                    "article_ref": case_ref,
                    "section_title": section_title,
                    "content": with_section_prefix(section_title, content),
                    "chunking_strategy": "case_one_case_then_limit",
                }
            )
    return sections


def split_by_heading_or_window(text: str) -> list[dict[str, Any]]:
    blocks: list[str] = []
    current: list[str] = []
    for line in (line.strip() for line in text.splitlines()):
        if not line:
            continue
        if is_guide_heading(line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    if not blocks:
        blocks = [text]

    sections: list[dict[str, Any]] = []
    for idx, block in enumerate(blocks, start=1):
        guide_ref = f"guide-{idx}"
        section_title = first_line(block)
        for content in split_to_limit(block):
            sections.append(
                {
                    "chunk_type": JobPostingKnowledgeChunkType.LEGAL_GUIDE.value,
                    "chunk_key": guide_ref,
                    "article_ref": guide_ref,
                    "section_title": section_title,
                    "content": with_section_prefix(section_title, content),
                    "chunking_strategy": "guide_heading_then_limit",
                }
            )
    return sections


def split_legal_article_detail(article_text: str) -> list[str]:
    if len(article_text) <= MAX_CHUNK_CHARS:
        return [article_text]
    detail_pattern = re.compile(
        r"(?=^\s*(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+\.\s|[가-힣]\.\s|\(\d+\)|\d+\)|[가-힣]\)))",
        re.MULTILINE,
    )
    parts = [part.strip() for part in detail_pattern.split(article_text) if part.strip()]
    if len(parts) <= 1:
        return split_to_limit(article_text)
    return split_to_limit_blocks(parts)


def split_to_limit(text: str) -> list[str]:
    return split_to_limit_blocks([text])


def split_to_limit_blocks(parts: list[str]) -> list[str]:
    expanded: list[str] = []
    for part in parts:
        if len(part) <= MAX_CHUNK_CHARS:
            if len(part) >= MIN_CHUNK_CHARS or not expanded:
                expanded.append(part)
            elif len(expanded[-1]) + len(part) + 2 <= MAX_CHUNK_CHARS:
                expanded[-1] = f"{expanded[-1]}\n\n{part}"
            else:
                expanded.append(part)
            continue

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", part) if p.strip()]
        if len(paragraphs) <= 1:
            paragraphs = [p.strip() for p in re.split(r"(?<=[.!?。다])\s+", part) if p.strip()]

        current = ""
        for paragraph in paragraphs or [part]:
            if len(paragraph) > MAX_CHUNK_CHARS:
                if current:
                    expanded.append(current)
                    current = ""
                expanded.extend(split_by_hard_limit(paragraph))
                continue
            if len(current) + len(paragraph) + 2 <= MAX_CHUNK_CHARS:
                current = f"{current}\n\n{paragraph}".strip()
            else:
                if current:
                    expanded.append(current)
                current = paragraph
        if current:
            expanded.append(current)
    return expanded


def split_by_hard_limit(text: str) -> list[str]:
    return [
        text[index:index + MAX_CHUNK_CHARS].strip()
        for index in range(0, len(text), MAX_CHUNK_CHARS)
        if text[index:index + MAX_CHUNK_CHARS].strip()
    ]


def normalize_chunk_source_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def is_guide_heading(line: str) -> bool:
    if len(line) > 90:
        return False
    return bool(
        re.match(
            r"^(?:제\s*\d+\s*[장절]|[0-9]+(?:\.[0-9]+)*[.)]?\s+|[가-힣][.)]\s+|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.)]?\s+|□\s*|○\s*)",
            line,
        )
    )


def with_section_prefix(section_title: str | None, content: str) -> str:
    title = (section_title or "").strip()
    if not title:
        return content.strip()
    content = content.strip()
    if content.startswith(title) or content.startswith(f"[{title}]"):
        return content
    return f"[{title}]\n{content}"


def infer_article_no(text: str) -> str | None:
    match = re.search(r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?", text)
    if not match:
        return None
    return f"제{match.group(1)}조" + (f"의{match.group(2)}" if match.group(2) else "")


def resolve_doc_id(source: JobPostingKnowledgeSource) -> str:
    metadata = source.metadata_json or {}
    value = metadata.get("doc_id") or metadata.get("docId")
    if value:
        return str(value)
    prefix_by_type = {
        JobPostingKnowledgeSourceType.LAW_TEXT.value: "LAW",
        JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value: "GUIDE",
        JobPostingKnowledgeSourceType.LEGAL_MANUAL.value: "MANUAL",
        JobPostingKnowledgeSourceType.INSPECTION_CASE.value: "CASE",
    }
    prefix = prefix_by_type.get(source.source_type, "DOC")
    return f"{prefix}_{source.id:03d}"


def map_doc_type(source_type: str) -> str:
    if source_type == JobPostingKnowledgeSourceType.LAW_TEXT.value:
        return "법령"
    if source_type == JobPostingKnowledgeSourceType.INSPECTION_CASE.value:
        return "사례"
    return "가이드"


def extract_effective_date(source: JobPostingKnowledgeSource) -> str | None:
    metadata = source.metadata_json or {}
    value = metadata.get("effective_date") or metadata.get("effectiveDate")
    if value:
        return str(value)
    if source.version_label:
        match = re.search(r"\d{4}[-.]\d{1,2}[-.]\d{1,2}|\d{4}[-.]\d{1,2}|\d{4}", source.version_label)
        if match:
            return match.group(0).replace(".", "-")
    return None


def resolve_is_latest(source: JobPostingKnowledgeSource) -> bool:
    metadata = source.metadata_json or {}
    value = metadata.get("is_latest") if "is_latest" in metadata else metadata.get("isLatest")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "y", "yes", "1", "latest"}
    return True


def collect_seed_source_files(root_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in root_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SEED_SOURCE_EXTENSIONS
    )


def canonical_source_title(path: Path) -> str:
    title = strip_extension(path.name)
    title = re.sub(r"\([^)]*\d{4,}[^)]*\)", "", title)
    title = re.sub(r"\([^)]*제\d+호[^)]*\)", "", title)
    title = re.sub(r"\s{2,}", " ", title)
    return title.strip(" _-") or strip_extension(path.name)


def build_seed_doc_id(path: Path) -> str:
    source_type = infer_source_type(path.name)
    prefix_map = {
        JobPostingKnowledgeSourceType.LAW_TEXT.value: "LAW",
        JobPostingKnowledgeSourceType.INSPECTION_CASE.value: "CASE",
        JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value: "GUIDE",
        JobPostingKnowledgeSourceType.LEGAL_MANUAL.value: "MANUAL",
    }
    prefix = prefix_map.get(source_type, "DOC")
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", canonical_source_title(path)).strip("_")
    return f"{prefix}_{slug or 'SOURCE'}"


def extract_effective_date_from_text(text: str) -> str | None:
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(20\d{2})[-.](\d{1,2})[-.](\d{1,2})", text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return None


def compute_latest_flags(paths: list[Path]) -> dict[str, bool]:
    latest_by_group: dict[tuple[str, str], tuple[str | None, str]] = {}
    for path in paths:
        source_type = infer_source_type(path.name)
        group_key = (source_type, canonical_source_title(path).lower())
        effective_date = extract_effective_date_from_text(path.name)
        sort_key = effective_date or ""
        current = latest_by_group.get(group_key)
        current_sort_key = current[0] or "" if current is not None else ""
        if current is None or sort_key >= current_sort_key:
            latest_by_group[group_key] = (sort_key or None, path.as_posix())

    latest_paths = {selected_path for _, selected_path in latest_by_group.values()}
    return {path.as_posix(): path.as_posix() in latest_paths for path in paths}


async def _save_knowledge_upload(upload_file: UploadFile) -> dict[str, Any]:
    """업로드 파일을 지식 저장 디렉터리에 저장한다."""
    if upload_file.filename is None or not upload_file.filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file name is missing.")
    extension = get_extension(upload_file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {extension or 'none'}",
        )

    target_dir = get_upload_root() / KNOWLEDGE_UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    original_file_name = Path(upload_file.filename).name
    stored_file_name = build_stored_filename(original_file_name)
    target_path = target_dir / stored_file_name
    file_size = 0
    try:
        with target_path.open("wb") as buffer:
            while True:
                chunk = await upload_file.read(READ_CHUNK_SIZE)
                if not chunk:
                    break
                buffer.write(chunk)
                file_size += len(chunk)
    finally:
        await upload_file.close()

    return {
        "title": strip_extension(original_file_name),
        "original_file_name": original_file_name,
        "file_path": build_public_file_path(target_path),
        "file_ext": extension,
        "mime_type": upload_file.content_type or mimetypes.guess_type(original_file_name)[0],
        "file_size": file_size,
    }


def _ensure_seed_file_under_upload_root(path: Path) -> str:
    """시드 문서를 업로드 루트 아래 복사해 동일한 경로 체계를 맞춘다."""
    upload_root = get_upload_root()
    target_dir = upload_root / KNOWLEDGE_UPLOAD_DIR / "seed_source_data"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / path.name
    if not target_path.exists() or target_path.stat().st_size != path.stat().st_size:
        target_path.write_bytes(path.read_bytes())
    return f"{FILES_PREFIX}/{target_path.relative_to(upload_root).as_posix()}"
