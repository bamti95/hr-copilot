from __future__ import annotations

import hashlib
import logging
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.document_types import ALLOWED_EXTENSIONS, READ_CHUNK_SIZE
from common.file_storage import (
    build_public_file_path,
    build_stored_filename,
    get_extension,
    get_upload_root,
    strip_extension,
)
from common.file_util import extract_text_from_file
from core.database import AsyncSessionLocal
from models.ai_job import AiJob, AiJobStatus, AiJobTargetType, AiJobType
from models.job_posting import JobPosting, JobPostingInputSource, JobPostingStatus
from models.job_posting_analysis_report import (
    JobPostingAnalysisReport,
    JobPostingAnalysisStatus,
    JobPostingAnalysisType,
)
from repositories.job_posting_knowledge_repository import JobPostingKnowledgeChunkRepository
from repositories.job_posting_repository import (
    JobPostingAnalysisReportRepository,
    JobPostingRepository,
)
from services.job_posting_report_service import (
    build_evidence_sufficiency,
    build_structured_compliance_report,
    calculate_evidence_strength,
)
from services.job_posting_retrieval_service import JobPostingRetrievalService
from services.job_posting_trace_service import JobPostingTraceRecorder, record_timed_node
from services.job_posting_embedding_service import (
    current_embedding_model_name,
    current_reranker_model_name,
)
from schemas.job_posting import (
    JobPostingAiJobResponse,
    JobPostingAnalyzeResponse,
    JobPostingAnalyzeTextRequest,
    JobPostingCreateRequest,
    JobPostingListResponse,
    JobPostingResponse,
    JobPostingAnalysisReportResponse,
)


PIPELINE_VERSION = "job-posting-compliance-rag-v1"
ANALYSIS_VERSION = "2026-05-12"
MODEL_NAME = "rule-rag-baseline"
JOB_POSTING_UPLOAD_DIR = "job_postings"
logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], Awaitable[None]]


@dataclass(slots=True)
class RiskPattern:
    issue_type: str
    severity: str
    pattern: re.Pattern[str]
    reason: str
    replacement: str
    query_terms: list[str]


RISK_PATTERNS = [
    RiskPattern(
        issue_type="GENDER_DISCRIMINATION",
        severity="HIGH",
        pattern=re.compile(r"(여성|남성|남자|여자)\s*(지원자|개발자|인재)?\s*(우대|선호|한정|지원 가능)"),
        reason="직무 수행과 무관하게 특정 성별을 우대하거나 제한하는 표현입니다.",
        replacement="성별과 무관하게 직무 경험과 역량을 기준으로 평가합니다.",
        query_terms=["성별", "남녀", "차별", "모집"],
    ),
    RiskPattern(
        issue_type="AGE_DISCRIMINATION",
        severity="HIGH",
        pattern=re.compile(r"(만\s*\d+\s*세\s*(이하|이상)|\d{2,4}\s*(세대|중심)|젊은\s*(감각|조직|인재)|20대|30대|2030)"),
        reason="합리적 이유 없이 특정 연령대만 선호하거나 제한하는 표현입니다.",
        replacement="연령과 무관하게 관련 경험, 문제 해결력, 직무 역량을 기준으로 평가합니다.",
        query_terms=["연령", "나이", "차별", "고령자"],
    ),
    RiskPattern(
        issue_type="IRRELEVANT_PERSONAL_INFO",
        severity="HIGH",
        pattern=re.compile(r"(혼인\s*여부|자녀\s*계획|가족\s*관계|부모.*직업|동거\s*가족|출신지역|재산|최근\s*사진|사진\s*첨부)"),
        reason="채용 직무와 직접 관련 없는 개인정보 제출을 요구하는 표현입니다.",
        replacement="지원서에는 직무 역량 확인에 필요한 경력, 경험, 포트폴리오 정보만 제출하도록 안내합니다.",
        query_terms=["혼인", "가족", "개인정보", "사진", "출신지역"],
    ),
    RiskPattern(
        issue_type="PHYSICAL_CONDITION",
        severity="HIGH",
        pattern=re.compile(r"(키\s*\d+|체중|몸무게|용모|외모|호감형|단정한\s*이미지|신뢰감\s*있는\s*인상|세련된\s*외형|체력|건강하고|지구력)"),
        reason="직무 수행과 직접 관련 없는 외모, 신체조건 또는 건강 상태를 평가 요소로 삼는 표현입니다.",
        replacement="외모나 신체조건 대신 고객 커뮤니케이션 역량과 직무 수행 경험을 평가합니다.",
        query_terms=["신체", "용모", "키", "체중", "개인정보"],
    ),
    RiskPattern(
        issue_type="FALSE_JOB_AD",
        severity="CRITICAL",
        pattern=re.compile(r"(실제\s*기본급|실제\s*업무|실제\s*입사|공고에는|공고상|최대\s*\d|성과급.*최대|정규직.*계약직|위촉계약|프리랜서)"),
        reason="공고상 처우, 고용형태 또는 직무 내용이 실제 운영 조건과 다르게 이해될 수 있는 표현입니다.",
        replacement="연봉, 성과급, 고용형태, 실제 업무 범위를 구분하여 정확히 안내합니다.",
        query_terms=["거짓 채용광고", "근로조건", "채용광고", "변경"],
    ),
    RiskPattern(
        issue_type="UNFAVORABLE_CONDITION_CHANGE",
        severity="HIGH",
        pattern=re.compile(r"(입사\s*후.*전환|평가\s*후\s*전환|고용조건.*다시\s*협의|계약\s*평가|프로젝트\s*종료\s*후)"),
        reason="공고에서 제시한 조건을 입사 후 불리하게 변경할 여지가 있습니다.",
        replacement="공고의 고용형태와 입사 후 적용 조건을 동일하게 명시하고 변경 가능 조건을 사전에 안내합니다.",
        query_terms=["근로조건", "불리", "변경", "채용광고"],
    ),
    RiskPattern(
        issue_type="WORKING_CONDITION_AMBIGUITY",
        severity="HIGH",
        pattern=re.compile(r"(야근\s*가능|온콜|주말\s*미팅|장기\s*출장|수시로\s*발생|포괄임금|수당.*입사\s*후|기준.*입사\s*후)"),
        reason="야근, 출장, 온콜 등 근로조건 부담 요소가 기준 없이 제시되어 지원자가 조건을 알기 어렵습니다.",
        replacement="연장근로, 출장, 온콜 발생 가능성과 보상 기준을 구체적으로 안내합니다.",
        query_terms=["근로조건", "연장근로", "수당", "출장"],
    ),
    RiskPattern(
        issue_type="SALARY_MISSING",
        severity="MEDIUM",
        pattern=re.compile(r"(연봉|급여|처우).*(협의|별도\s*안내|내규|합격\s*후)"),
        reason="연봉 범위가 명확하지 않아 처우 예측 가능성이 낮습니다.",
        replacement="연봉 범위와 산정 기준을 명확히 기재합니다.",
        query_terms=["연봉", "근로조건", "채용공고"],
    ),
    RiskPattern(
        issue_type="JOB_DESCRIPTION_VAGUE",
        severity="MEDIUM",
        pattern=re.compile(r"(업무\s*전반|관련\s*업무|회사.*필요한\s*업무|상황에\s*따라\s*달라집니다|입사\s*후\s*조정)"),
        reason="주요 업무가 포괄적으로만 제시되어 실제 직무 범위를 판단하기 어렵습니다.",
        replacement="주요 업무, 협업 대상, 산출물을 구체적으로 구분해 설명합니다.",
        query_terms=["채용공고", "직무", "업무내용"],
    ),
    RiskPattern(
        issue_type="CULTURE_RED_FLAG",
        severity="MEDIUM",
        pattern=re.compile(r"(가족\s*같은|가족처럼|열정|희생|불굴|강한\s*승부욕|끝까지\s*책임)"),
        reason="모호한 문화 표현이 과도하게 강조되어 지원자가 업무 강도를 불명확하게 받아들일 수 있습니다.",
        replacement="조직문화는 협업 방식, 의사결정 방식, 피드백 체계 등 구체적 운영 방식으로 설명합니다.",
        query_terms=["공정채용", "채용공고", "문화"],
    ),
    RiskPattern(
        issue_type="BENEFIT_VAGUE",
        severity="LOW",
        pattern=re.compile(r"(최고\s*수준의\s*성장|자유로운\s*복지|성장\s*친화적|업계\s*최고)"),
        reason="복지나 성장 기회가 구체적 기준 없이 추상적으로 제시되어 신뢰도가 낮습니다.",
        replacement="복지 항목의 이용 조건, 지원 범위, 적용 대상을 구체적으로 안내합니다.",
        query_terms=["채용공고", "복지", "공정채용"],
    ),
    RiskPattern(
        issue_type="REPEATED_POSTING",
        severity="LOW",
        pattern=re.compile(r"(동일\s*공고|반복\s*게시|상시로\s*반복|장기간\s*반복)"),
        reason="동일 공고 반복 게시가 채용 안정성이나 이탈 리스크로 해석될 수 있습니다.",
        replacement="반복 게시 사유, 채용 인원, 충원 배경을 명확히 안내합니다.",
        query_terms=["채용공고", "반복", "공정채용"],
    ),
]


class JobPostingService:
    @staticmethod
    def _job_response(job: AiJob, message: str) -> JobPostingAiJobResponse:
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
    async def create_posting(
        *,
        db: AsyncSession,
        request: JobPostingCreateRequest,
        actor_id: int | None,
    ) -> JobPostingResponse:
        repo = JobPostingRepository(db)
        entity = await upsert_posting(db=db, repo=repo, request=request, actor_id=actor_id)
        await db.commit()
        await repo.refresh(entity)
        return JobPostingResponse.from_entity(entity)

    @staticmethod
    async def list_postings(
        *,
        db: AsyncSession,
        page: int,
        size: int,
        keyword: str | None,
    ) -> JobPostingListResponse:
        repo = JobPostingRepository(db)
        total_count = await repo.count_list(keyword=keyword)
        rows = await repo.find_list(page=page, size=size, keyword=keyword)
        total_pages = math.ceil(total_count / size) if total_count else 0
        return JobPostingListResponse(
            items=[JobPostingResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_posting(
        *,
        db: AsyncSession,
        posting_id: int,
    ) -> JobPostingResponse:
        repo = JobPostingRepository(db)
        entity = await repo.find_by_id_not_deleted(posting_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )
        return JobPostingResponse.from_entity(entity)

    @staticmethod
    async def analyze_text(
        *,
        db: AsyncSession,
        request: JobPostingAnalyzeTextRequest,
        actor_id: int | None,
    ) -> JobPostingAnalyzeResponse:
        posting_repo = JobPostingRepository(db)
        posting = await upsert_posting(
            db=db,
            repo=posting_repo,
            request=request,
            actor_id=actor_id,
        )
        await posting_repo.flush()
        report = await run_rule_rag_analysis(
            db=db,
            posting=posting,
            analysis_type=request.analysis_type,
            actor_id=actor_id,
        )
        await db.commit()
        await posting_repo.refresh(posting)
        await db.refresh(report)
        return JobPostingAnalyzeResponse(
            job_posting=JobPostingResponse.from_entity(posting),
            report=JobPostingAnalysisReportResponse.from_entity(report),
        )

    @staticmethod
    async def analyze_existing(
        *,
        db: AsyncSession,
        posting_id: int,
        analysis_type: str,
        actor_id: int | None,
    ) -> JobPostingAnalysisReportResponse:
        posting_repo = JobPostingRepository(db)
        posting = await posting_repo.find_by_id_not_deleted(posting_id)
        if posting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )
        report = await run_rule_rag_analysis(
            db=db,
            posting=posting,
            analysis_type=analysis_type,
            actor_id=actor_id,
        )
        await db.commit()
        await db.refresh(report)
        return JobPostingAnalysisReportResponse.from_entity(report)

    @staticmethod
    async def analyze_pdf_file(
        *,
        db: AsyncSession,
        file_path: str,
        file_ext: str | None,
        job_title: str,
        company_name: str | None,
        actor_id: int | None,
    ) -> JobPostingAnalyzeResponse:
        extracted = extract_text_from_file(file_path, file_ext)
        if extracted.extract_status != "SUCCESS" or not extracted.extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract text from uploaded job posting PDF.",
            )
        request = JobPostingAnalyzeTextRequest(
            input_source=JobPostingInputSource.MANUAL.value,
            company_name=company_name,
            job_title=job_title,
            posting_text=extracted.extracted_text,
            raw_payload={
                "file_path": file_path,
                "file_ext": file_ext,
                "extract_meta": extracted.extract_meta,
            },
            normalized_payload={
                "extract_strategy": extracted.extract_strategy,
                "extract_quality_score": extracted.extract_quality_score,
            },
        )
        return await JobPostingService.analyze_text(
            db=db,
            request=request,
            actor_id=actor_id,
        )

    @staticmethod
    async def analyze_upload_file(
        *,
        db: AsyncSession,
        upload_file: UploadFile,
        job_title: str | None,
        company_name: str | None,
        actor_id: int | None,
    ) -> JobPostingAnalyzeResponse:
        saved = await save_job_posting_upload(upload_file)
        return await JobPostingService.analyze_pdf_file(
            db=db,
            file_path=saved["file_path"],
            file_ext=saved["file_ext"],
            job_title=job_title or saved["title"],
            company_name=company_name,
            actor_id=actor_id,
        )

    @staticmethod
    async def submit_analyze_text_job(
        *,
        db: AsyncSession,
        request: JobPostingAnalyzeTextRequest,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        posting_repo = JobPostingRepository(db)
        posting = await upsert_posting(
            db=db,
            repo=posting_repo,
            request=request,
            actor_id=actor_id,
        )
        await posting_repo.flush()
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.JOB_POSTING.value,
            target_id=posting.id,
            progress=2,
            current_step="analysis_job_created",
            request_payload={
                "mode": "TEXT",
                "posting_id": posting.id,
                "analysis_type": request.analysis_type,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobPostingService._job_response(
            job,
            "채용공고 점검 작업이 시작되었습니다.",
        )

    @staticmethod
    async def submit_existing_analysis_job(
        *,
        db: AsyncSession,
        posting_id: int,
        analysis_type: str,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        posting_repo = JobPostingRepository(db)
        posting = await posting_repo.find_by_id_not_deleted(posting_id)
        if posting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.JOB_POSTING.value,
            target_id=posting.id,
            progress=2,
            current_step="analysis_job_created",
            request_payload={
                "mode": "EXISTING",
                "posting_id": posting.id,
                "analysis_type": analysis_type,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobPostingService._job_response(
            job,
            "채용공고 재점검 작업이 시작되었습니다.",
        )

    @staticmethod
    async def submit_analyze_file_job(
        *,
        db: AsyncSession,
        upload_file: UploadFile,
        job_title: str | None,
        company_name: str | None,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        saved = await save_job_posting_upload(upload_file)
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.JOB_POSTING.value,
            progress=2,
            current_step="analysis_file_saved",
            request_payload={
                "mode": "FILE",
                "file_path": saved["file_path"],
                "file_ext": saved["file_ext"],
                "job_title": job_title or saved["title"],
                "company_name": company_name,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobPostingService._job_response(
            job,
            "채용공고 파일 점검 작업이 시작되었습니다.",
        )

    @staticmethod
    async def get_analysis_job(
        *,
        db: AsyncSession,
        job_id: int,
    ) -> JobPostingAiJobResponse:
        result = await db.execute(
            select(AiJob).where(
                AiJob.id == job_id,
                AiJob.job_type == AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting analysis job was not found.",
            )
        return JobPostingService._job_response(job, "채용공고 점검 작업 상태입니다.")

    @staticmethod
    async def list_reports(
        *,
        db: AsyncSession,
        posting_id: int,
        limit: int,
    ) -> list[JobPostingAnalysisReportResponse]:
        posting_repo = JobPostingRepository(db)
        posting = await posting_repo.find_by_id_not_deleted(posting_id)
        if posting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )
        report_repo = JobPostingAnalysisReportRepository(db)
        rows = await report_repo.find_by_posting_id(posting_id, limit=limit)
        return [JobPostingAnalysisReportResponse.from_entity(row) for row in rows]

    @staticmethod
    async def get_report(
        *,
        db: AsyncSession,
        report_id: int,
    ) -> JobPostingAnalysisReportResponse:
        repo = JobPostingAnalysisReportRepository(db)
        entity = await repo.find_by_id_not_deleted(report_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis report was not found.",
            )
        return JobPostingAnalysisReportResponse.from_entity(entity)

    @staticmethod
    async def run_analysis_job(job_id: int) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AiJob).where(AiJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                logger.warning("Job posting analysis job not found: %s", job_id)
                return

            try:
                payload = job.request_payload or {}
                mode = payload.get("mode")
                actor_id = job.requested_by
                job.status = AiJobStatus.RUNNING.value
                job.progress = 10
                job.current_step = "analysis_started"
                job.started_at = job.started_at or datetime.now(timezone.utc)
                await db.commit()

                async def update_progress(progress: int, current_step: str) -> None:
                    job.progress = max(job.progress, min(progress, 99))
                    job.current_step = current_step
                    await db.commit()

                if mode in {"TEXT", "EXISTING"}:
                    posting_repo = JobPostingRepository(db)
                    posting = await posting_repo.find_by_id_not_deleted(
                        int(payload["posting_id"])
                    )
                    if posting is None:
                        raise ValueError("Job posting was not found.")
                    job.progress = 35
                    job.current_step = "posting_loaded"
                    await db.commit()
                    report = await run_rule_rag_analysis(
                        db=db,
                        posting=posting,
                        analysis_type=payload.get("analysis_type") or JobPostingAnalysisType.FULL.value,
                        actor_id=actor_id,
                        progress_callback=update_progress,
                    )
                    report.ai_job_id = job.id
                    job.target_id = posting.id
                elif mode == "FILE":
                    extracted = extract_text_from_file(
                        payload.get("file_path") or "",
                        payload.get("file_ext"),
                    )
                    if extracted.extract_status != "SUCCESS" or not extracted.extracted_text:
                        raise ValueError("Failed to extract text from uploaded job posting file.")
                    job.progress = 30
                    job.current_step = "file_text_extracted"
                    await db.commit()
                    request = JobPostingAnalyzeTextRequest(
                        input_source=JobPostingInputSource.MANUAL.value,
                        company_name=payload.get("company_name"),
                        job_title=payload.get("job_title") or "채용공고",
                        posting_text=extracted.extracted_text,
                        raw_payload={
                            "file_path": payload.get("file_path"),
                            "file_ext": payload.get("file_ext"),
                            "extract_meta": extracted.extract_meta,
                        },
                        normalized_payload={
                            "extract_strategy": extracted.extract_strategy,
                            "extract_quality_score": extracted.extract_quality_score,
                        },
                    )
                    posting_repo = JobPostingRepository(db)
                    posting = await upsert_posting(
                        db=db,
                        repo=posting_repo,
                        request=request,
                        actor_id=actor_id,
                    )
                    await posting_repo.flush()
                    job.target_id = posting.id
                    job.progress = 45
                    job.current_step = "posting_saved"
                    await db.commit()
                    report = await run_rule_rag_analysis(
                        db=db,
                        posting=posting,
                        analysis_type=JobPostingAnalysisType.FULL.value,
                        actor_id=actor_id,
                        progress_callback=update_progress,
                    )
                    report.ai_job_id = job.id
                else:
                    raise ValueError(f"Unsupported job posting analysis mode: {mode}")

                job.status = AiJobStatus.SUCCESS.value
                job.progress = 100
                job.current_step = "analysis_completed"
                job.result_payload = {
                    "job_posting_id": report.job_posting_id,
                    "job_posting_analysis_report_id": report.id,
                    "risk_level": report.risk_level,
                    "analysis_status": report.analysis_status,
                }
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as exc:
                logger.exception("Job posting analysis job failed. job_id=%s", job_id)
                await db.rollback()
                result = await db.execute(select(AiJob).where(AiJob.id == job_id))
                failed_job = result.scalar_one_or_none()
                if failed_job is not None:
                    failed_job.status = AiJobStatus.FAILED.value
                    failed_job.progress = 100
                    failed_job.current_step = "analysis_failed"
                    failed_job.error_message = str(exc)
                    failed_job.completed_at = datetime.now(timezone.utc)
                    await db.commit()


async def upsert_posting(
    *,
    db: AsyncSession,
    repo: JobPostingRepository,
    request: JobPostingCreateRequest,
    actor_id: int | None,
) -> JobPosting:
    posting_hash = hash_posting_text(request.posting_text)
    existing = await repo.find_by_hash(posting_hash)
    if existing:
        existing.company_name = request.company_name
        existing.job_title = request.job_title
        existing.target_job = request.target_job
        existing.career_level = request.career_level
        existing.location = request.location
        existing.employment_type = request.employment_type
        existing.salary_text = request.salary_text
        existing.raw_payload = request.raw_payload
        existing.normalized_payload = request.normalized_payload
        return existing

    entity = JobPosting(
        input_source=request.input_source,
        source_platform=request.source_platform,
        external_posting_id=request.external_posting_id,
        external_url=request.external_url,
        company_name=request.company_name,
        job_title=request.job_title,
        target_job=request.target_job,
        career_level=request.career_level,
        location=request.location,
        employment_type=request.employment_type,
        salary_text=request.salary_text,
        posting_text=request.posting_text,
        posting_text_hash=posting_hash,
        raw_payload=request.raw_payload,
        normalized_payload=request.normalized_payload,
        posting_status=JobPostingStatus.DRAFT.value,
        created_by=actor_id,
    )
    await repo.add(entity)
    return entity


async def run_rule_rag_analysis(
    *,
    db: AsyncSession,
    posting: JobPosting,
    analysis_type: str,
    actor_id: int | None,
    progress_callback: ProgressCallback | None = None,
) -> JobPostingAnalysisReport:
    started_at = datetime.now(timezone.utc)
    report = JobPostingAnalysisReport(
        job_posting_id=posting.id,
        analysis_status=JobPostingAnalysisStatus.RUNNING.value,
        analysis_type=analysis_type or JobPostingAnalysisType.FULL.value,
        analysis_version=ANALYSIS_VERSION,
        model_name=MODEL_NAME,
        prompt_version="rule-rag-v1",
        pipeline_version=PIPELINE_VERSION,
        requested_by=actor_id,
        started_at=started_at,
        created_by=actor_id,
    )
    report_repo = JobPostingAnalysisReportRepository(db)
    await report_repo.add(report)
    await report_repo.flush()
    trace = JobPostingTraceRecorder(
        db=db,
        manager_id=actor_id,
        job_posting_id=posting.id,
        report_id=report.id,
    )

    try:
        if progress_callback is not None:
            await progress_callback(50, "detecting_risk_phrases")
        node_started_at = time.perf_counter()
        issues = detect_issues(posting.posting_text)
        await record_timed_node(
            trace,
            node_name="detect_risk_phrases",
            request_json={"posting_id": posting.id, "text_length": len(posting.posting_text)},
            output_json={"issue_count": len(issues), "issues": issues},
            elapsed_started_at=node_started_at,
        )

        if progress_callback is not None:
            await progress_callback(58, "generating_retrieval_queries")
        node_started_at = time.perf_counter()
        retrieval_queries = [
            {
                "issue_type": issue["issue_type"],
                "flagged_text": issue["flagged_text"],
                "query_terms": issue["query_terms"],
            }
            for issue in issues
        ]
        await record_timed_node(
            trace,
            node_name="generate_retrieval_queries",
            request_json={"issue_count": len(issues)},
            output_json={"queries": retrieval_queries},
            elapsed_started_at=node_started_at,
        )

        retrieval_service = JobPostingRetrievalService(db)
        evidence_items: list[dict[str, Any]] = []
        total_issues = max(len(issues), 1)
        for issue_index, issue in enumerate(issues):
            if progress_callback is not None:
                retrieve_progress = 62 + int((issue_index / total_issues) * 18)
                await progress_callback(
                    retrieve_progress,
                    f"retrieving_evidence_{issue_index + 1}_of_{len(issues)}",
                )
            node_started_at = time.perf_counter()
            evidences = await retrieval_service.retrieve_for_issue(
                issue=issue,
                limit=12,
            )
            evidence_payloads = [evidence.to_payload() for evidence in evidences]
            await record_timed_node(
                trace,
                node_name="bm25_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "query_terms": issue["query_terms"],
                },
                output_json={
                    "candidate_count": len(evidence_payloads),
                    "top_candidates": evidence_payloads[:5],
                },
                elapsed_started_at=node_started_at,
            )
            vector_trace_started_at = time.perf_counter()
            await trace.record(
                node_name="vector_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "embedding_model": current_embedding_model_name(),
                },
                output_json={
                    "candidate_count": len(evidence_payloads),
                    "top_vector_scores": [
                        item.get("vector_score") for item in evidence_payloads[:5]
                    ],
                },
                elapsed_ms=int((time.perf_counter() - vector_trace_started_at) * 1000),
            )
            merge_trace_started_at = time.perf_counter()
            await trace.record(
                node_name="merge_hybrid_results",
                request_json={
                    "issue_type": issue["issue_type"],
                    "reranker_model": current_reranker_model_name(),
                },
                output_json={
                    "candidate_count": len(evidence_payloads),
                    "top_hybrid_scores": [
                        item.get("hybrid_score") for item in evidence_payloads[:5]
                    ],
                },
                elapsed_ms=int((time.perf_counter() - merge_trace_started_at) * 1000),
            )
            issue["sources"] = evidence_payloads[:5]
            evidence_items.extend(evidence_payloads[:5])

        if progress_callback is not None:
            await progress_callback(82, "checking_evidence_sufficiency")
        node_started_at = time.perf_counter()
        sufficiency = build_evidence_sufficiency(issues=issues)
        await record_timed_node(
            trace,
            node_name="check_evidence_sufficiency",
            request_json={"issue_count": len(issues)},
            output_json=sufficiency,
            elapsed_started_at=node_started_at,
        )

        if progress_callback is not None:
            await progress_callback(87, "reranking_evidence")
        node_started_at = time.perf_counter()
        reranked_evidence_items = sorted(
            evidence_items,
            key=lambda item: item.get("rerank_score") or item.get("hybrid_score") or 0,
            reverse=True,
        )
        await record_timed_node(
            trace,
            node_name="rerank_evidence",
            request_json={"evidence_count": len(evidence_items)},
            output_json={"top_evidence": reranked_evidence_items[:10]},
            elapsed_started_at=node_started_at,
        )

        if progress_callback is not None:
            await progress_callback(92, "generating_structured_report")
        node_started_at = time.perf_counter()
        risk_level = calculate_risk_level_with_evidence(issues)
        violation_count = sum(1 for issue in issues if issue["category"] == "LEGAL")
        warning_count = max(0, len(issues) - violation_count)
        evidence_strength = calculate_evidence_strength(issues)
        final_report = build_structured_compliance_report(
            posting=posting,
            issues=issues,
            risk_level=risk_level,
            evidence_strength=evidence_strength,
            evidence_items=reranked_evidence_items[:20],
        )
        await record_timed_node(
            trace,
            node_name="generate_structured_report",
            request_json={
                "posting_id": posting.id,
                "issue_count": len(issues),
                "evidence_count": len(reranked_evidence_items),
            },
            output_json=final_report,
            elapsed_started_at=node_started_at,
            model_name="structured-output-local",
        )

        if progress_callback is not None:
            await progress_callback(96, "saving_report_and_trace")
        node_started_at = time.perf_counter()
        report.analysis_status = JobPostingAnalysisStatus.SUCCESS.value
        report.risk_level = risk_level
        report.issue_count = len(issues)
        report.violation_count = violation_count
        report.warning_count = warning_count
        report.confidence_score = evidence_strength
        report.detected_issue_types = sorted({issue["issue_type"] for issue in issues})
        report.retrieval_summary = {
            "pipeline": PIPELINE_VERSION,
            "query_count": len(issues),
            "evidence_count": len(reranked_evidence_items),
            "retrieval_mode": "hybrid_full_text_pgvector",
            "query_rewrite_mode": "issue_template_expansion",
            "rerank_mode": "three_axis_slot_rerank",
            "sufficiency": sufficiency,
        }
        report.summary_text = final_report["summary"]
        report.parsed_sections = parse_posting_sections(posting.posting_text)
        report.overall_score = final_report["overall_score"]
        report.risk_score = final_report["risk_score"]
        report.attractiveness_score = final_report["attractiveness_score"]
        report.issue_summary = issues
        report.matched_evidence = reranked_evidence_items[:20]
        report.compliance_warnings = [
            issue for issue in issues if issue["category"] == "LEGAL"
        ]
        report.improvement_suggestions = [
            {
                "issue_type": issue["issue_type"],
                "flagged_text": issue["flagged_text"],
                "recommended_revision": issue["recommended_revision"],
                "evidence_strength": (
                    final_report["issues"][index]["evidence_strength"]
                    if index < len(final_report["issues"])
                    else "INSUFFICIENT"
                ),
            }
            for index, issue in enumerate(issues)
        ]
        report.rewrite_examples = [
            {
                "before": issue["flagged_text"],
                "after": issue["recommended_revision"],
            }
            for issue in issues
        ]
        report.final_report = final_report
        report.completed_at = datetime.now(timezone.utc)
        await record_timed_node(
            trace,
            node_name="save_report_and_logs",
            request_json={"report_id": report.id},
            output_json={
                "analysis_status": report.analysis_status,
                "risk_level": report.risk_level,
                "evidence_strength": evidence_strength,
            },
            elapsed_started_at=node_started_at,
        )
    except Exception as exc:
        logger.exception(
            "Job posting analysis failed posting_id=%s report_id=%s",
            posting.id,
            report.id,
        )
        await trace.record(
            node_name="pipeline_failed",
            request_json={"posting_id": posting.id, "report_id": report.id},
            output_json=None,
            call_status="failed",
            error_message=str(exc),
            elapsed_ms=0,
        )
        report.analysis_status = JobPostingAnalysisStatus.FAILED.value
        report.error_message = str(exc)
        report.completed_at = datetime.now(timezone.utc)
    return report


def detect_issues(posting_text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for risk_pattern in RISK_PATTERNS:
        for match in risk_pattern.pattern.finditer(posting_text):
            flagged = normalize_flagged_text(match.group(0))
            key = (risk_pattern.issue_type, flagged)
            if key in seen:
                continue
            seen.add(key)
            issues.append(
                {
                    "issue_type": risk_pattern.issue_type,
                    "severity": risk_pattern.severity,
                    "category": (
                        "LEGAL"
                        if risk_pattern.issue_type
                        in {
                            "FALSE_JOB_AD",
                            "UNFAVORABLE_CONDITION_CHANGE",
                            "GENDER_DISCRIMINATION",
                            "AGE_DISCRIMINATION",
                            "PHYSICAL_CONDITION",
                            "IRRELEVANT_PERSONAL_INFO",
                            "WORKING_CONDITION_AMBIGUITY",
                        }
                        else "BRANDING"
                    ),
                    "flagged_text": flagged,
                    "why_risky": risk_pattern.reason,
                    "recommended_revision": risk_pattern.replacement,
                    "confidence": confidence_by_severity(risk_pattern.severity),
                    "query_terms": risk_pattern.query_terms,
                    "sources": [],
                }
            )
    return issues


def rank_evidence(issue: dict[str, Any], chunks: list[Any]) -> list[dict[str, Any]]:
    ranked = []
    issue_terms = set(issue.get("query_terms") or [])
    for chunk in chunks:
        content = chunk.content or ""
        score = 0.1
        if chunk.issue_code == issue["issue_type"]:
            score += 0.55
        for term in issue_terms:
            if term and term in content:
                score += 0.08
        source = getattr(chunk, "knowledge_source", None)
        ranked.append(
            {
                "chunk_id": chunk.id,
                "source_id": chunk.knowledge_source_id,
                "title": getattr(source, "title", None),
                "source_type": getattr(source, "source_type", None),
                "chunk_type": chunk.chunk_type,
                "section_title": chunk.section_title,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "law_name": chunk.law_name,
                "article_no": chunk.article_no,
                "content": content[:800],
                "score": round(min(score, 1.0), 4),
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def calculate_risk_level(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "CLEAN"
    legal_count = sum(1 for issue in issues if issue["category"] == "LEGAL")
    if any(issue["issue_type"] == "FALSE_JOB_AD" for issue in issues) or legal_count >= 3:
        return "CRITICAL"
    if legal_count >= 2 or (legal_count >= 1 and len(issues) >= 3):
        return "HIGH"
    if legal_count >= 1 or len(issues) >= 2:
        return "MEDIUM"
    return "LOW"


def calculate_risk_level_with_evidence(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "CLEAN"
    legal_with_law = 0
    legal_without_law = 0
    for issue in issues:
        if issue.get("category") != "LEGAL":
            continue
        sources = issue.get("sources") or []
        has_law = any(source.get("law_name") or source.get("article_no") for source in sources)
        if has_law:
            legal_with_law += 1
        else:
            legal_without_law += 1

    if any(issue.get("issue_type") == "FALSE_JOB_AD" for issue in issues) and legal_with_law:
        return "CRITICAL"
    if legal_with_law >= 3:
        return "CRITICAL"
    if legal_with_law >= 1 and len(issues) >= 3:
        return "HIGH"
    if legal_with_law >= 1 or legal_without_law >= 1:
        return "MEDIUM"
    if len(issues) >= 2:
        return "LOW"
    return "LOW"


def calculate_confidence(
    issues: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
) -> int:
    if not issues:
        return 92
    base = sum(issue["confidence"] for issue in issues) / len(issues)
    evidence_bonus = min(8, len(evidence_items))
    return int(min(95, base + evidence_bonus))


def build_final_report(
    *,
    posting: JobPosting,
    issues: list[dict[str, Any]],
    risk_level: str,
    confidence: int,
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    issue_payloads = []
    for issue in issues:
        item = {key: value for key, value in issue.items() if key != "query_terms"}
        item["related_laws"] = [
            {
                "law_name": source.get("law_name"),
                "article_no": source.get("article_no"),
                "source_title": source.get("title"),
            }
            for source in item.get("sources", [])
            if source.get("law_name") or source.get("article_no")
        ]
        item["possible_penalty"] = next(
            (
                source.get("content")
                for source in item.get("sources", [])
                if any(word in (source.get("content") or "") for word in ["벌금", "과태료", "징역", "시정명령"])
            ),
            None,
        )
        issue_payloads.append(item)

    if not issues:
        summary = "법적 위반 및 주요 지원율 하락 요인이 발견되지 않는 정상 공고입니다."
    else:
        summary = f"{posting.job_title} 공고에서 {len(issues)}개 리스크가 탐지되었습니다."

    risk_score = {"CLEAN": 0, "LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 90}[risk_level]
    return {
        "risk_level": risk_level,
        "summary": summary,
        "issues": issue_payloads,
        "retrieval": {
            "evidence_count": len(evidence_items),
            "pipeline": PIPELINE_VERSION,
        },
        "overall_score": max(0, 100 - risk_score),
        "risk_score": risk_score,
        "attractiveness_score": max(0, 92 - len([i for i in issues if i["category"] == "BRANDING"]) * 12),
        "confidence": confidence,
        "disclaimer": "본 결과는 채용공고 문구의 법률 및 공정채용 가이드 리스크를 사전 점검하기 위한 참고용 분석입니다. 최종 법률 판단 및 공고 게시 결정은 내부 검토 또는 전문가 자문을 통해 확인해야 합니다.",
    }


def parse_posting_sections(posting_text: str) -> dict[str, Any]:
    return {
        "text_length": len(posting_text),
        "line_count": len([line for line in posting_text.splitlines() if line.strip()]),
        "has_salary": bool(re.search(r"(연봉|급여|처우)", posting_text)),
        "has_employment_type": bool(re.search(r"(정규직|계약직|인턴|프리랜서|위촉)", posting_text)),
    }


def hash_posting_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_flagged_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def confidence_by_severity(severity: str) -> int:
    return {"CRITICAL": 90, "HIGH": 84, "MEDIUM": 72, "LOW": 62}.get(severity, 70)


async def save_job_posting_upload(upload_file: UploadFile) -> dict[str, Any]:
    if upload_file.filename is None or not upload_file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file name is missing.",
        )
    extension = get_extension(upload_file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {extension or 'none'}",
        )

    target_dir = get_upload_root() / JOB_POSTING_UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    original_file_name = Path(upload_file.filename).name
    target_path = target_dir / build_stored_filename(original_file_name)
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
        "file_path": build_public_file_path(target_path),
        "file_ext": extension,
        "file_size": file_size,
    }
