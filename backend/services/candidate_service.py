import asyncio
import json
import logging
import math
import mimetypes
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.file_util import (
    build_download_response,
    build_public_file_path,
    build_stored_filename,
    delete_file_by_path,
    extract_text_from_file,
    get_extension,
    resolve_absolute_path,
    resolve_document_dir,
    save_upload_file_pairs,
    strip_extension,
)
from core.database import AsyncSessionLocal
from models.candidate import ApplyStatus, Candidate, JobPosition
from models.document import Document
from repositories.candidate_repository import CandidateRepository
from schemas.candidate import (
    ApplyStatusCountRow,
    CandidateCreateRequest,
    CandidateBulkImportError,
    CandidateBulkImportRequest,
    CandidateBulkImportResponse,
    CandidateDeleteResponse,
    CandidateDocumentDeleteResponse,
    CandidateDocumentDetailResponse,
    CandidateDetailResponse,
    CandidateDocumentResponse,
    CandidateDocumentUploadResponse,
    CandidateListResponse,
    CandidatePagination,
    CandidateResponse,
    CandidateSampleFolderListResponse,
    CandidateSampleFolderResponse,
    CandidateStatisticsResponse,
    CandidateStatusPatchRequest,
    CandidateStatusPatchResponse,
    CandidateUpdateRequest,
    TargetJobCountRow,
)

logger = logging.getLogger(__name__)
DOCUMENT_EXTRACTION_CONCURRENCY = 2
SAMPLE_DATA_ROOT = Path(__file__).resolve().parents[1] / "sample_data"
_JOB_CODE_TO_POSITION = {
    "STRATEGY_PLANNING": JobPosition.STRATEGY_PLANNING,
    "HR": JobPosition.HR,
    "MARKETING": JobPosition.MARKETING,
    "AI_DEV_DATA": JobPosition.AI_DEV_DATA,
    "SALES": JobPosition.SALES,
}
_SAMPLE_DOCUMENT_SUFFIX_MAP = {
    "_bundle.pdf": "RESUME",
    "_portfolio.pdf": "PORTFOLIO",
    "_career_description.pdf": "CAREER_DESCRIPTION",
}


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


def _iter_sample_candidate_groups(folder_path: Path) -> list[tuple[str, dict[str, Path]]]:
    grouped: dict[str, dict[str, Path]] = {}
    for file_path in folder_path.rglob("*"):
        if not file_path.is_file():
            continue

        for suffix in ("_meta.json", "_source.json", "_bundle.pdf", "_portfolio.pdf", "_career_description.pdf"):
            if file_path.name.endswith(suffix):
                candidate_key = file_path.name[: -len(suffix)]
                grouped.setdefault(candidate_key, {})[suffix] = file_path
                break

    return sorted(grouped.items(), key=lambda item: item[0])


def _resolve_sample_folder(folder_name: str) -> Path:
    folder_path = (SAMPLE_DATA_ROOT / folder_name).resolve()
    sample_root = SAMPLE_DATA_ROOT.resolve()
    if sample_root not in folder_path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sample folder path.",
        )
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample folder not found.",
        )
    return folder_path


def _load_json_file(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _build_birth_date(source_payload: dict) -> date | None:
    birth_year = ((source_payload.get("candidate_profile") or {}).get("birth_year"))
    if not birth_year:
        return None
    try:
        return datetime(int(birth_year), 1, 1, tzinfo=timezone.utc).date()
    except (TypeError, ValueError):
        return None


def _document_type_for_sample_file(file_path: Path) -> str | None:
    lower_name = file_path.name.lower()
    for suffix, document_type in _SAMPLE_DOCUMENT_SUFFIX_MAP.items():
        if lower_name.endswith(suffix):
            return document_type
    return None


def _copy_sample_document(
    *,
    candidate_id: int,
    source_path: Path,
    document_type: str,
) -> tuple[Document, int]:
    target_dir = resolve_document_dir(candidate_id, document_type)
    target_dir.mkdir(parents=True, exist_ok=True)

    original_file_name = source_path.name
    stored_file_name = build_stored_filename(original_file_name)
    target_path = target_dir / stored_file_name
    shutil.copy2(source_path, target_path)

    file_size = target_path.stat().st_size
    mime_type = mimetypes.guess_type(original_file_name)[0]

    document = Document(
        document_type=document_type,
        title=strip_extension(original_file_name) or stored_file_name,
        original_file_name=original_file_name,
        stored_file_name=stored_file_name,
        file_path=build_public_file_path(target_path),
        file_ext=get_extension(original_file_name) or None,
        mime_type=mime_type,
        file_size=file_size,
        candidate_id=candidate_id,
        extracted_text=None,
        extract_status="PENDING",
    )
    return document, file_size


class CandidateService:
    @staticmethod
    async def list_sample_folders() -> CandidateSampleFolderListResponse:
        if not SAMPLE_DATA_ROOT.exists():
            return CandidateSampleFolderListResponse(folders=[])

        folders: list[CandidateSampleFolderResponse] = []
        for folder_path in sorted(
            [path for path in SAMPLE_DATA_ROOT.iterdir() if path.is_dir()],
            key=lambda path: path.name,
        ):
            candidate_count = sum(
                1
                for _, files in _iter_sample_candidate_groups(folder_path)
                if "_meta.json" in files and "_source.json" in files
            )
            if candidate_count == 0:
                continue
            folders.append(
                CandidateSampleFolderResponse(
                    folder_name=folder_path.name,
                    candidate_count=candidate_count,
                )
            )

        return CandidateSampleFolderListResponse(folders=folders)

    @staticmethod
    async def bulk_import_candidates(
        db: AsyncSession,
        request: CandidateBulkImportRequest,
        actor_id: int | None,
    ) -> CandidateBulkImportResponse:
        folder_path = _resolve_sample_folder(request.folder_name)
        candidate_groups = _iter_sample_candidate_groups(folder_path)
        repo = CandidateRepository(db)

        created_count = 0
        skipped_count = 0
        document_count = 0
        document_ids: list[int] = []
        errors: list[CandidateBulkImportError] = []

        for candidate_key, files in candidate_groups:
            meta_path = files.get("_meta.json")
            source_path = files.get("_source.json")
            if meta_path is None or source_path is None:
                skipped_count += 1
                errors.append(
                    CandidateBulkImportError(
                        candidate_key=candidate_key,
                        reason="Required meta/source files are missing.",
                    )
                )
                continue

            try:
                meta_payload = _load_json_file(meta_path)
                source_payload = _load_json_file(source_path)
                profile = source_payload.get("candidate_profile") or {}

                email = str(profile.get("email", "")).strip()
                phone = str(profile.get("phone", "")).strip()
                name = str(profile.get("name", "")).strip()
                job_code = str(meta_payload.get("job_code", "")).strip().upper()

                if not email or not phone or not name or job_code not in _JOB_CODE_TO_POSITION:
                    skipped_count += 1
                    errors.append(
                        CandidateBulkImportError(
                            candidate_key=candidate_key,
                            reason="Sample candidate metadata is incomplete.",
                        )
                    )
                    continue

                _assert_extra_email_rules(email)
                _assert_phone_format(phone)

                if await repo.find_active_by_email(email):
                    skipped_count += 1
                    errors.append(
                        CandidateBulkImportError(
                            candidate_key=candidate_key,
                            reason="Duplicate email. Candidate skipped.",
                        )
                    )
                    continue

                phone_digits = _phone_digits(phone)
                if await repo.find_active_by_phone_digits(phone_digits):
                    skipped_count += 1
                    errors.append(
                        CandidateBulkImportError(
                            candidate_key=candidate_key,
                            reason="Duplicate phone number. Candidate skipped.",
                        )
                    )
                    continue

                candidate = Candidate(
                    name=name,
                    email=email,
                    phone=phone,
                    job_position=_JOB_CODE_TO_POSITION[job_code].value,
                    birth_date=_build_birth_date(source_payload),
                    apply_status=ApplyStatus.APPLIED.value,
                    created_by=actor_id,
                )
                await repo.add(candidate)
                await repo.flush()

                created_documents: list[Document] = []
                copied_file_paths: list[Path] = []
                try:
                    for file_path in files.values():
                        document_type = _document_type_for_sample_file(file_path)
                        if document_type is None:
                            continue
                        document, _ = _copy_sample_document(
                            candidate_id=candidate.id,
                            source_path=file_path,
                            document_type=document_type,
                        )
                        document.created_by = actor_id
                        created_documents.append(document)
                        copied_file_paths.append(resolve_absolute_path(document.file_path))
                        await repo.add(document)

                    await repo.flush()
                    await db.commit()
                except Exception:
                    await db.rollback()
                    for copied_file_path in copied_file_paths:
                        try:
                            copied_file_path.unlink(missing_ok=True)
                        except OSError:
                            pass
                    skipped_count += 1
                    errors.append(
                        CandidateBulkImportError(
                            candidate_key=candidate_key,
                            reason="Failed while copying sample documents.",
                        )
                    )
                    continue

                await repo.refresh(candidate)
                for document in created_documents:
                    await repo.refresh(document)
                    document_ids.append(document.id)

                created_count += 1
                document_count += len(created_documents)
            except HTTPException as exc:
                await db.rollback()
                skipped_count += 1
                errors.append(
                    CandidateBulkImportError(
                        candidate_key=candidate_key,
                        reason=str(exc.detail),
                    )
                )
            except Exception:
                await db.rollback()
                logger.exception("Sample bulk import failed for candidate_key=%s", candidate_key)
                skipped_count += 1
                errors.append(
                    CandidateBulkImportError(
                        candidate_key=candidate_key,
                        reason="Unexpected error occurred during import.",
                    )
                )

        if document_ids:
            await CandidateService.run_document_extraction(document_ids)

        return CandidateBulkImportResponse(
            folder_name=request.folder_name,
            requested_count=len(candidate_groups),
            created_count=created_count,
            skipped_count=skipped_count,
            document_count=document_count,
            errors=errors,
        )

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
            job_position=request.job_position.value if request.job_position else None,
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
        target_job: str | None,
    ) -> CandidateListResponse:
        repo = CandidateRepository(db)
        status_str = apply_status.value if apply_status else None
        job_filter = target_job.strip() if target_job and target_job.strip() else None
        total_items = await repo.count_list(
            apply_status=status_str,
            search=search,
            target_job=job_filter,
        )
        rows = await repo.find_list(
            page=page,
            limit=limit,
            apply_status=status_str,
            search=search,
            target_job=job_filter,
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
        job_map = {job: count for job, count in job_rows}
        job_rows_sorted = [
            (job_item.value, job_map.get(job_item.value, 0))
            for job_item in JobPosition
        ]
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
        entity.job_position = request.job_position.value if request.job_position else None
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
