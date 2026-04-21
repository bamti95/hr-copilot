import asyncio
import logging
import math
import re
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.file_util import (
    build_download_response,
    delete_file_by_path,
    extract_text_from_file,
    resolve_absolute_path,
    save_upload_file_pairs,
)
from core.database import AsyncSessionLocal
from models.candidate import ApplyStatus, Candidate
from models.document import Document
from repositories.candidate_repository import CandidateRepository
from schemas.candidate import (
    ApplyStatusCountRow,
    CandidateCreateRequest,
    CandidateDeleteResponse,
    CandidateDocumentDeleteResponse,
    CandidateDocumentDetailResponse,
    CandidateDetailResponse,
    CandidateDocumentResponse,
    CandidateDocumentUploadResponse,
    CandidateListResponse,
    CandidatePagination,
    CandidateResponse,
    CandidateStatisticsResponse,
    CandidateStatusPatchRequest,
    CandidateStatusPatchResponse,
    CandidateUpdateRequest,
    TargetJobCountRow,
)

logger = logging.getLogger(__name__)
DOCUMENT_EXTRACTION_CONCURRENCY = 2


def _assert_extra_email_rules(email: str) -> None:
    normalized = email.strip()
    if "@" not in normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format.",
        )
    local, _, domain = normalized.partition("@")
    if not local or not domain or "." not in domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format.",
        )


def _assert_phone_format(phone: str) -> None:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10 or len(digits) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format.",
        )


def _phone_digits(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def _expand_document_types(document_types: list[str], file_count: int) -> list[str]:
    normalized_types = [
        document_type.strip()
        for document_type in document_types
        if document_type.strip()
    ]
    if not normalized_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one document_type is required.",
        )

    if len(normalized_types) == 1 and file_count > 1:
        return normalized_types * file_count

    if len(normalized_types) != file_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_types count must be 1 or match files count.",
        )

    return normalized_types


class CandidateService:
    @staticmethod
    async def run_document_extraction(document_ids: list[int]) -> None:
        if not document_ids:
            return

        semaphore = asyncio.Semaphore(DOCUMENT_EXTRACTION_CONCURRENCY)

        async def process_document(document_id: int) -> None:
            async with semaphore:
                async with AsyncSessionLocal() as db:
                    repo = CandidateRepository(db)
                    document = await repo.find_document_by_id_any(document_id)
                    if not document or document.deleted_at is not None:
                        logger.info(
                            "Skipping extraction for document_id=%s because document is missing or deleted",
                            document_id,
                        )
                        return

                    try:
                        extraction = await asyncio.to_thread(
                            extract_text_from_file,
                            document.file_path,
                            document.file_ext,
                        )
                        document.extracted_text = extraction.extracted_text
                        document.extract_status = extraction.extract_status

                        if extraction.extract_status == "FAILED":
                            logger.warning(
                                "Background extraction finished without text for document_id=%s file_path=%s strategy=%s source_type=%s quality=%.4f",
                                document_id,
                                document.file_path,
                                extraction.extract_strategy,
                                extraction.source_type,
                                extraction.extract_quality_score,
                            )
                        else:
                            logger.info(
                                "Background extraction succeeded for document_id=%s file_path=%s text_length=%s strategy=%s source_type=%s document_type=%s quality=%.4f",
                                document_id,
                                document.file_path,
                                len(extraction.extracted_text or ""),
                                extraction.extract_strategy,
                                extraction.source_type,
                                extraction.document_type,
                                extraction.extract_quality_score,
                            )

                        await db.commit()
                    except Exception:
                        logger.exception(
                            "Background extraction failed for document_id=%s",
                            document_id,
                        )
                        document.extract_status = "FAILED"
                        document.extracted_text = None
                        await db.commit()

        await asyncio.gather(*(process_document(document_id) for document_id in document_ids))

    @staticmethod
    async def create_candidate(
        db: AsyncSession,
        request: CandidateCreateRequest,
        actor_id: int | None,
    ) -> CandidateResponse:
        _assert_extra_email_rules(str(request.email))
        _assert_phone_format(request.phone)

        repo = CandidateRepository(db)
        if await repo.find_active_by_email(str(request.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        phone_digits = _phone_digits(request.phone)
        if await repo.find_active_by_phone_digits(phone_digits):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 전화번호입니다.",
            )

        entity = Candidate(
            name=request.name.strip(),
            email=str(request.email).strip(),
            phone=request.phone.strip(),
            birth_date=request.birth_date,
            apply_status=ApplyStatus.APPLIED.value,
            created_by=actor_id,
        )
        await repo.add(entity)
        await repo.flush()
        await db.commit()
        await repo.refresh(entity)
        return CandidateResponse.model_validate(entity)

    @staticmethod
    async def list_candidates(
        db: AsyncSession,
        page: int,
        limit: int,
        apply_status: ApplyStatus | None,
        search: str | None,
    ) -> CandidateListResponse:
        repo = CandidateRepository(db)
        status_str = apply_status.value if apply_status else None
        total_items = await repo.count_list(apply_status=status_str, search=search)
        rows = await repo.find_list(
            page=page,
            limit=limit,
            apply_status=status_str,
            search=search,
        )
        total_pages = math.ceil(total_items / limit) if total_items else 0
        return CandidateListResponse(
            candidates=[CandidateResponse.model_validate(row) for row in rows],
            pagination=CandidatePagination(
                current_page=page,
                total_pages=total_pages,
                total_items=total_items,
                items_per_page=limit,
            ),
        )

    @staticmethod
    async def get_statistics(db: AsyncSession) -> CandidateStatisticsResponse:
        repo = CandidateRepository(db)
        total = await repo.count_active_candidates()
        status_rows = await repo.count_by_apply_status()
        status_map = dict(status_rows)
        by_apply_status = [
            ApplyStatusCountRow(
                apply_status=status_item.value,
                count=status_map.get(status_item.value, 0),
            )
            for status_item in ApplyStatus
        ]
        job_rows = await repo.count_by_target_job_distinct_candidates()
        job_rows_sorted = sorted(job_rows, key=lambda row: (-row[1], row[0]))
        by_target_job = [
            TargetJobCountRow(target_job=job, count=count)
            for job, count in job_rows_sorted
        ]
        with_session = await repo.count_distinct_active_candidates_with_session()
        without_session = max(0, total - with_session)
        return CandidateStatisticsResponse(
            total_candidates=total,
            by_apply_status=by_apply_status,
            by_target_job=by_target_job,
            active_without_interview_session_count=without_session,
        )

    @staticmethod
    async def get_candidate(
        db: AsyncSession,
        candidate_id: int,
    ) -> CandidateDetailResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        documents = await repo.find_active_documents_by_candidate_id(candidate_id)
        return CandidateDetailResponse(
            **CandidateResponse.model_validate(entity).model_dump(),
            documents=[
                CandidateDocumentResponse.model_validate(document)
                for document in documents
            ],
        )

    @staticmethod
    async def get_candidate_document(
        db: AsyncSession,
        candidate_id: int,
        document_id: int,
    ) -> CandidateDocumentDetailResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        document = await repo.find_active_document_by_id(candidate_id, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        return CandidateDocumentDetailResponse.model_validate(document)

    @staticmethod
    async def update_candidate(
        db: AsyncSession,
        candidate_id: int,
        request: CandidateUpdateRequest,
    ) -> CandidateResponse:
        _assert_extra_email_rules(str(request.email))
        _assert_phone_format(request.phone)

        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        if await repo.find_active_by_email_excluding_id(str(request.email), candidate_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        phone_digits = _phone_digits(request.phone)
        if await repo.find_active_by_phone_digits_excluding_id(phone_digits, candidate_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 전화번호입니다.",
            )

        entity.name = request.name.strip()
        entity.email = str(request.email).strip()
        entity.phone = request.phone.strip()
        entity.birth_date = request.birth_date
        entity.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await repo.refresh(entity)
        return CandidateResponse.model_validate(entity)

    @staticmethod
    async def patch_status(
        db: AsyncSession,
        candidate_id: int,
        request: CandidateStatusPatchRequest,
    ) -> CandidateStatusPatchResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        try:
            next_status = ApplyStatus(request.apply_status.strip())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid apply status.",
            ) from exc

        entity.apply_status = next_status.value
        entity.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await repo.refresh(entity)
        return CandidateStatusPatchResponse(
            id=entity.id,
            apply_status=entity.apply_status,
        )

    @staticmethod
    async def delete_candidate(
        db: AsyncSession,
        candidate_id: int,
        actor_id: int | None,
    ) -> CandidateDeleteResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_any(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )
        if entity.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate is already deleted.",
            )

        now = datetime.now(timezone.utc)
        entity.deleted_at = now
        entity.deleted_by = actor_id
        entity.updated_at = now

        await db.commit()
        await repo.refresh(entity)
        return CandidateDeleteResponse(
            id=entity.id,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        )

    @staticmethod
    async def upload_candidate_documents(
        db: AsyncSession,
        candidate_id: int,
        document_types: list[str],
        files: list[UploadFile],
        actor_id: int | None,
    ) -> CandidateDocumentUploadResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required.",
            )

        expanded_document_types = _expand_document_types(document_types, len(files))
        saved_files = await save_upload_file_pairs(
            candidate_id=candidate_id,
            document_file_pairs=list(zip(expanded_document_types, files, strict=True)),
        )
        saved_paths = [resolve_absolute_path(saved.file_path) for saved in saved_files]
        created_documents: list[Document] = []

        try:
            for document_type, saved in zip(
                expanded_document_types,
                saved_files,
                strict=True,
            ):
                document = Document(
                    document_type=document_type.strip().upper(),
                    title=saved.title,
                    original_file_name=saved.original_file_name,
                    stored_file_name=saved.stored_file_name,
                    file_path=saved.file_path,
                    file_ext=saved.file_ext,
                    mime_type=saved.mime_type,
                    file_size=saved.file_size,
                    candidate_id=candidate_id,
                    extracted_text=None,
                    extract_status="PENDING",
                    created_by=actor_id,
                )
                await repo.add(document)
                created_documents.append(document)

            await repo.flush()
            await db.commit()

            for document in created_documents:
                await repo.refresh(document)

        except Exception:
            await db.rollback()
            for saved_path in saved_paths:
                try:
                    saved_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

        return CandidateDocumentUploadResponse(
            candidate_id=candidate_id,
            count=len(created_documents),
            documents=[
                CandidateDocumentResponse.model_validate(document)
                for document in created_documents
            ],
        )

    @staticmethod
    async def download_candidate_document(
        db: AsyncSession,
        candidate_id: int,
        document_id: int,
    ) -> FileResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        document = await repo.find_active_document_by_id(candidate_id, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        return build_download_response(
            file_path=document.file_path,
            download_name=document.original_file_name,
            media_type=document.mime_type,
        )

    @staticmethod
    async def delete_candidate_document(
        db: AsyncSession,
        candidate_id: int,
        document_id: int,
        actor_id: int | None,
    ) -> CandidateDocumentDeleteResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        document = await repo.find_active_document_by_id(candidate_id, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        now = datetime.now(timezone.utc)
        document.deleted_at = now
        document.deleted_by = actor_id

        await db.commit()
        await repo.refresh(document)
        delete_file_by_path(document.file_path)
        return CandidateDocumentDeleteResponse(id=document.id, deleted_at=now)

    @staticmethod
    async def replace_candidate_document(
        db: AsyncSession,
        candidate_id: int,
        document_id: int,
        document_type: str,
        upload_file: UploadFile,
        actor_id: int | None,
    ) -> CandidateDocumentResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )

        document = await repo.find_active_document_by_id(candidate_id, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        [saved_file] = await save_upload_file_pairs(
            candidate_id=candidate_id,
            document_file_pairs=[(document_type, upload_file)],
        )
        old_file_path = document.file_path

        try:
            document.document_type = document_type.strip().upper()
            document.title = saved_file.title
            document.original_file_name = saved_file.original_file_name
            document.stored_file_name = saved_file.stored_file_name
            document.file_path = saved_file.file_path
            document.file_ext = saved_file.file_ext
            document.mime_type = saved_file.mime_type
            document.file_size = saved_file.file_size
            document.extracted_text = None
            document.extract_status = "PENDING"
            document.deleted_at = None
            document.deleted_by = None
            document.created_by = actor_id if actor_id is not None else document.created_by

            await db.commit()
            await repo.refresh(document)

        except Exception:
            await db.rollback()
            delete_file_by_path(saved_file.file_path)
            raise

        if old_file_path != document.file_path:
            delete_file_by_path(old_file_path)

        return CandidateDocumentResponse.model_validate(document)
