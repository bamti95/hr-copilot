from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.llm_client import client as openai_client
from ai.llm_client import get_openai_model
from common.document_types import ALLOWED_DOCUMENT_TYPES, ALLOWED_EXTENSIONS, READ_CHUNK_SIZE
from common.file_util import (
    build_public_file_path,
    build_stored_filename,
    extract_text_from_file,
    get_extension,
    get_upload_root,
    resolve_absolute_path,
    resolve_document_dir,
    strip_extension,
)
from core.config import settings
from core.database import AsyncSessionLocal
from models.ai_job import AiJob, AiJobStatus, AiJobTargetType, AiJobType
from models.candidate import ApplyStatus
from models.candidate import Candidate
from models.document import Document
from repositories.candidate_repository import CandidateRepository
from schemas.candidate import (
    CandidateProfileExtractionOutput,
    DocumentBulkImportConfirmError,
    DocumentBulkImportConfirmRequest,
    DocumentBulkImportConfirmResponse,
    DocumentBulkImportPreviewDocument,
    DocumentBulkImportPreviewJobListResponse,
    DocumentBulkImportPreviewJobResponse,
    DocumentBulkImportPreviewResponse,
    DocumentBulkImportPreviewRow,
    DocumentBulkImportPreviewStartResponse,
    DocumentBulkImportPreviewSummary,
)

logger = logging.getLogger(__name__)

DOCUMENT_BULK_ROOT_DIR = "document_bulk_previews"
DOCUMENT_BULK_LLM_TEXT_LIMIT = 12000
SUPPORTED_EXTRACTION_EXTENSIONS = {"pdf", "docx", "txt"}
DOCUMENT_TYPE_KEYWORDS = {
    "RESUME": (
        "resume",
        "cv",
        "이력서",
        "application",
        "application_form",
        "job_application",
        "입사지원서",
        "지원서",
        "지원양식",
        "입사 지원서",
        "입사_지원서",
    ),
    "COVER_LETTER": (
        "cover_letter",
        "self_introduction",
        "자기소개서",
        "자소서",
        "소개서",
    ),
    "PORTFOLIO": (
        "portfolio",
        "포트폴리오",
    ),
    "CAREER_DESCRIPTION": (
        "career_description",
        "career_summary",
        "work_experience",
        "경력기술서",
        "경력 기술서",
        "경력_기술서",
        "경력사항",
        "경력 사항",
        "경력소개서",
    ),
}

@dataclass(slots=True)
class StagedDocument:
    group_key: str
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_ext: str | None
    mime_type: str | None
    file_size: int | None
    document_type: str
    inferred_candidate_name: str | None


def _normalize_default_job_position(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _validate_apply_status(value: str | None) -> str:
    normalized = (value or ApplyStatus.APPLIED.value).strip().upper()
    try:
        return ApplyStatus(normalized).value
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid default_apply_status.",
        ) from exc


def _safe_zip_member_path(member_name: str) -> PurePosixPath:
    normalized = member_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsafe ZIP member path: {member_name}",
        )
    return path


def _clean_group_key(value: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "ungrouped"


def _strip_document_tokens(stem: str) -> str:
    result = stem
    tokens = [
        "resume",
        "cv",
        "application",
        "application_form",
        "job_application",
        "cover_letter",
        "cover",
        "portfolio",
        "career_description",
        "career",
        "이력서",
        "입사지원서",
        "지원서",
        "지원양식",
        "입사 지원서",
        "입사_지원서",
        "자기소개서",
        "자소서",
        "포트폴리오",
        "경력기술서",
    ]
    for token in tokens:
        result = re.sub(token, "", result, flags=re.IGNORECASE)
    return _clean_group_key(result)


def _infer_group_from_zip_path(path: PurePosixPath) -> tuple[str, str | None]:
    parts = [part for part in path.parts if part]
    if len(parts) >= 2:
        return _clean_group_key(parts[0]), _clean_group_key(parts[0])
    stem = strip_extension(parts[0] if parts else path.name)
    group_key = _strip_document_tokens(stem)
    return group_key, group_key


def _infer_group_from_filename(filename: str) -> tuple[str, str | None]:
    stem = strip_extension(Path(filename).name)
    group_key = _strip_document_tokens(stem)
    return group_key, group_key


def _infer_document_type(filename: str) -> str:
    lower_name = filename.lower()
    for document_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        if any(keyword.lower() in lower_name for keyword in keywords):
            return document_type
    return "RESUME"


def _build_preview_dir(job_id: int) -> Path:
    return get_upload_root() / DOCUMENT_BULK_ROOT_DIR / str(job_id)


def _validate_extension(filename: str) -> str:
    extension = get_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {extension or 'none'}",
        )
    return extension


async def _save_upload_to_path(upload_file: UploadFile, target_path: Path) -> int:
    file_size = 0
    target_path.parent.mkdir(parents=True, exist_ok=True)
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
    return file_size


def _extract_email(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(?:\+?82[-.\s]?)?0?1[016789][-\s.]?\d{3,4}[-\s.]?\d{4}", text)
    return match.group(0) if match else None


def _extract_birth_date(text: str) -> str | None:
    match = re.search(r"(19|20)\d{2}[-./년\s]?(0?[1-9]|1[0-2])[-./월\s]?(0?[1-9]|[12]\d|3[01])", text)
    return match.group(0) if match else None


def _normalize_birth_date_for_candidate(value: str | None) -> tuple[str | None, str | None]:
    raw_value = (value or "").strip()
    if not raw_value:
        return None, None

    year_only_match = re.fullmatch(r"((?:19|20)\d{2})년?", raw_value)
    if year_only_match:
        return (
            f"{year_only_match.group(1)}-01-01",
            "birth_date contains only the birth year; candidate birth_date was normalized to YYYY-01-01 for sample data.",
        )

    match = re.fullmatch(
        r"((?:19|20)\d{2})[-./년\s]?(0?[1-9]|1[0-2])[-./월\s]?(0?[1-9]|[12]\d|3[01])일?",
        raw_value,
    )
    if not match:
        return (
            None,
            "birth_date is incomplete or not a full YYYY-MM-DD date; candidate birth_date will stay empty.",
        )

    year, month, day = match.groups()
    normalized = f"{year}-{int(month):02d}-{int(day):02d}"
    try:
        datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError:
        return (
            None,
            "birth_date is not a valid calendar date; candidate birth_date will stay empty.",
        )
    return normalized, None


def _build_text_preview(text: str | None, limit: int = 240) -> str | None:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _infer_experience_suffix(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text or "").lower()
    if not normalized:
        return None

    fresher_patterns = [
        "신입",
        "new grad",
        "new graduate",
        "entry level",
        "entry-level",
        "junior applicant",
    ]
    career_patterns = [
        "경력",
        "재직",
        "퇴사",
        "이직",
        "년차",
        "근무",
        "프로젝트 리드",
        "담당",
        "experienced",
        "senior",
        "work experience",
        "professional experience",
    ]

    if any(pattern in normalized for pattern in fresher_patterns):
        return "신입"
    if any(pattern in normalized for pattern in career_patterns):
        return "경력"
    if re.search(r"\d+\s*년\s*(?:이상|차|경력|근무)", normalized):
        return "경력"
    return None


def _append_experience_suffix(job_position: str | None, suffix: str | None) -> str | None:
    normalized = (job_position or "").strip()
    if not normalized or not suffix:
        return normalized or None
    if re.search(r"\((?:신입|경력)\)\s*$", normalized):
        return normalized
    return f"{normalized} ({suffix})"


def _phone_digits(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def _parse_candidate_birth_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _heuristic_extract_profile(
    *,
    text: str,
    inferred_name: str | None,
    default_job_position: str | None,
) -> CandidateProfileExtractionOutput:
    email = _extract_email(text)
    phone = _extract_phone(text)
    missing_fields: list[str] = []
    if not inferred_name:
        missing_fields.append("name")
    if not email:
        missing_fields.append("email")
    if not phone:
        missing_fields.append("phone")

    present_score = 1 - (len(missing_fields) / 3)
    return CandidateProfileExtractionOutput(
        name=inferred_name,
        email=email,
        phone=phone,
        birth_date=_extract_birth_date(text),
        job_position=default_job_position,
        summary=None,
        confidence_score=round(max(0.0, min(0.86, present_score * 0.86)), 2),
        missing_fields=missing_fields,
        warnings=[],
    )


def _json_from_llm_text(text: str) -> dict | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


async def _extract_profile_with_llm(
    *,
    text: str,
    inferred_name: str | None,
    default_job_position: str | None,
) -> CandidateProfileExtractionOutput | None:
    if not (settings.OPENAI_API_KEY or "").strip() or not text.strip():
        return None

    clipped_text = text[:DOCUMENT_BULK_LLM_TEXT_LIMIT]
    prompt = f"""
You extract candidate profile fields for an HR recruiting system.

Return only a JSON object with these keys:
name, email, phone, birth_date, job_position, summary, confidence_score, missing_fields, warnings.

Rules:
- Do not invent missing values.
- If the document does not state a value, return null and include the field in missing_fields.
- Use the inferred file/folder name only as a weak hint for name.
- Do not store sensitive information beyond the requested fields.
- If the candidate is clearly new graduate/entry-level, reflect it in job_position with "(신입)".
- If the candidate clearly has work experience, reflect it in job_position with "(경력)".
- confidence_score must be between 0 and 1.

Weak inferred name hint: {inferred_name or ""}
Default job position hint: {default_job_position or ""}

Document text:
\"\"\"
{clipped_text}
\"\"\"
"""

    try:
        response = await openai_client.responses.create(
            model=get_openai_model(),
            input=prompt,
        )
        payload = _json_from_llm_text(getattr(response, "output_text", "") or "")
        if not payload:
            return None
        return CandidateProfileExtractionOutput.model_validate(payload)
    except Exception:
        logger.exception("Candidate profile LLM extraction failed.")
        return None


async def _extract_profile(
    *,
    text: str,
    inferred_name: str | None,
    default_job_position: str | None,
) -> CandidateProfileExtractionOutput:
    llm_profile = await _extract_profile_with_llm(
        text=text,
        inferred_name=inferred_name,
        default_job_position=default_job_position,
    )
    if llm_profile is not None:
        if default_job_position and not llm_profile.job_position:
            llm_profile.job_position = default_job_position
        return llm_profile

    return _heuristic_extract_profile(
        text=text,
        inferred_name=inferred_name,
        default_job_position=default_job_position,
    )


class DocumentBulkImportService:
    @staticmethod
    async def start_preview_zip(
        *,
        db: AsyncSession,
        zip_file: UploadFile,
        default_job_position: str | None,
        default_apply_status: str | None,
        actor_id: int | None,
    ) -> DocumentBulkImportPreviewStartResponse:
        if zip_file.filename is None or get_extension(zip_file.filename) != "zip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="zip_file must be a ZIP file.",
            )

        job = await DocumentBulkImportService._create_preview_job(
            db=db,
            upload_mode="ZIP",
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
            actor_id=actor_id,
        )

        preview_dir = _build_preview_dir(job.id)
        source_path = preview_dir / "source" / build_stored_filename(zip_file.filename)
        file_size = await _save_upload_to_path(zip_file, source_path)

        job.request_payload = {
            **(job.request_payload or {}),
            "source_zip": {
                "original_file_name": Path(zip_file.filename).name,
                "stored_file_name": source_path.name,
                "file_path": build_public_file_path(source_path),
                "file_size": file_size,
            },
        }
        job.current_step = "preview_upload_saved"
        await db.commit()

        return DocumentBulkImportPreviewStartResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            message="Document bulk import preview job has started.",
        )

    @staticmethod
    async def start_preview_files(
        *,
        db: AsyncSession,
        files: list[UploadFile],
        default_job_position: str | None,
        default_apply_status: str | None,
        actor_id: int | None,
    ) -> DocumentBulkImportPreviewStartResponse:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required.",
            )

        job = await DocumentBulkImportService._create_preview_job(
            db=db,
            upload_mode="FILES",
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
            actor_id=actor_id,
        )

        preview_dir = _build_preview_dir(job.id)
        source_files: list[dict] = []
        for upload_file in files:
            original_name = Path(upload_file.filename or "").name
            if not original_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file name is missing.",
                )
            _validate_extension(original_name)
            stored_file_name = build_stored_filename(original_name)
            source_path = preview_dir / "source" / stored_file_name
            file_size = await _save_upload_to_path(upload_file, source_path)
            source_files.append(
                {
                    "original_file_name": original_name,
                    "stored_file_name": stored_file_name,
                    "file_path": build_public_file_path(source_path),
                    "mime_type": upload_file.content_type or mimetypes.guess_type(original_name)[0],
                    "file_size": file_size,
                }
            )

        job.request_payload = {
            **(job.request_payload or {}),
            "source_files": source_files,
        }
        job.current_step = "preview_upload_saved"
        await db.commit()

        return DocumentBulkImportPreviewStartResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            message="Document bulk import preview job has started.",
        )

    @staticmethod
    async def run_preview_job(job_id: int) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AiJob).where(AiJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                logger.warning("Document bulk preview job not found: %s", job_id)
                return

            try:
                request_payload = job.request_payload or {}
                upload_mode = request_payload.get("upload_mode")
                default_job_position = request_payload.get("default_job_position")
                default_apply_status = request_payload.get("default_apply_status")

                job.status = AiJobStatus.RUNNING.value
                job.progress = 10
                job.current_step = "preview_processing_started"
                job.started_at = job.started_at or datetime.now(timezone.utc)
                await db.commit()

                if upload_mode == "ZIP":
                    staged_documents = DocumentBulkImportService._stage_documents_from_zip(
                        job_id=job.id,
                        source_zip=request_payload.get("source_zip") or {},
                    )
                elif upload_mode == "FILES":
                    staged_documents = DocumentBulkImportService._stage_documents_from_files(
                        job_id=job.id,
                        source_files=request_payload.get("source_files") or [],
                    )
                else:
                    raise ValueError(f"Unsupported upload_mode: {upload_mode}")

                await DocumentBulkImportService._build_preview_response(
                    db=db,
                    job=job,
                    upload_mode=upload_mode,
                    staged_documents=staged_documents,
                    default_job_position=default_job_position,
                    default_apply_status=default_apply_status,
                    incremental=True,
                )
            except Exception as exc:
                logger.exception("Document bulk preview job failed. job_id=%s", job_id)
                job.status = AiJobStatus.FAILED.value
                job.progress = 100
                job.current_step = "preview_failed"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

    @staticmethod
    async def get_preview_job(
        *,
        db: AsyncSession,
        job_id: int,
    ) -> DocumentBulkImportPreviewJobResponse:
        result = await db.execute(
            select(AiJob).where(
                AiJob.id == job_id,
                AiJob.job_type == AiJobType.DOCUMENT_BULK_IMPORT.value,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document bulk import preview job was not found.",
            )

        payload = job.result_payload or {}
        summary_payload = payload.get("summary")
        rows_payload = payload.get("rows") or []
        return DocumentBulkImportPreviewJobResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            error_message=job.error_message,
            upload_mode=payload.get("upload_mode") or (job.request_payload or {}).get("upload_mode"),
            summary=(
                DocumentBulkImportPreviewSummary.model_validate(summary_payload)
                if summary_payload
                else None
            ),
            rows=[
                DocumentBulkImportPreviewRow.model_validate(row_payload)
                for row_payload in rows_payload
            ],
        )

    @staticmethod
    async def list_preview_jobs(
        *,
        db: AsyncSession,
        actor_id: int | None,
        active_only: bool = True,
        limit: int = 10,
    ) -> DocumentBulkImportPreviewJobListResponse:
        conditions = [AiJob.job_type == AiJobType.DOCUMENT_BULK_IMPORT.value]
        if actor_id is not None:
            conditions.append(AiJob.requested_by == actor_id)
        if active_only:
            conditions.append(
                AiJob.status.in_(
                    [
                        AiJobStatus.QUEUED.value,
                        AiJobStatus.RUNNING.value,
                        AiJobStatus.RETRYING.value,
                    ]
                )
            )

        result = await db.execute(
            select(AiJob)
            .where(*conditions)
            .order_by(desc(AiJob.created_at))
            .limit(max(1, min(limit, 50)))
        )
        jobs = result.scalars().all()
        return DocumentBulkImportPreviewJobListResponse(
            jobs=[
                await DocumentBulkImportService.get_preview_job(db=db, job_id=job.id)
                for job in jobs
            ]
        )

    @staticmethod
    async def confirm_import(
        *,
        db: AsyncSession,
        request: DocumentBulkImportConfirmRequest,
        actor_id: int | None,
    ) -> DocumentBulkImportConfirmResponse:
        job_result = await db.execute(
            select(AiJob).where(
                AiJob.id == request.job_id,
                AiJob.job_type == AiJobType.DOCUMENT_BULK_IMPORT.value,
            )
        )
        job = job_result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document bulk import preview job was not found.",
            )
        if job.status in {
            AiJobStatus.QUEUED.value,
            AiJobStatus.RUNNING.value,
            AiJobStatus.RETRYING.value,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preview job is still running.",
            )

        payload = job.result_payload or {}
        rows = [
            DocumentBulkImportPreviewRow.model_validate(row_payload)
            for row_payload in payload.get("rows") or []
        ]
        selected_ids = set(request.selected_row_ids)
        target_rows = [
            row
            for row in rows
            if (not selected_ids and row.status == "READY")
            or (selected_ids and row.row_id in selected_ids)
        ]

        repo = CandidateRepository(db)
        created_count = 0
        document_count = 0
        candidate_ids: list[int] = []
        errors: list[DocumentBulkImportConfirmError] = []

        for row in target_rows:
            candidate_payload = row.candidate or {}
            name = str(candidate_payload.get("name") or "").strip()
            email = str(candidate_payload.get("email") or "").strip()
            phone = str(candidate_payload.get("phone") or "").strip()
            job_position = str(candidate_payload.get("job_position") or "").strip() or None
            apply_status = str(
                candidate_payload.get("apply_status") or ApplyStatus.APPLIED.value
            ).strip()

            if not name or not email or not phone:
                errors.append(
                    DocumentBulkImportConfirmError(
                        row_id=row.row_id,
                        group_key=row.group_key,
                        reason="Candidate name, email and phone are required.",
                    )
                )
                continue

            try:
                apply_status = ApplyStatus(apply_status).value
            except ValueError:
                apply_status = ApplyStatus.APPLIED.value

            if await repo.find_active_by_email(email):
                errors.append(
                    DocumentBulkImportConfirmError(
                        row_id=row.row_id,
                        group_key=row.group_key,
                        reason="Duplicate email candidate exists.",
                    )
                )
                continue
            phone_digits = _phone_digits(phone)
            if phone_digits and await repo.find_active_by_phone_digits(phone_digits):
                errors.append(
                    DocumentBulkImportConfirmError(
                        row_id=row.row_id,
                        group_key=row.group_key,
                        reason="Duplicate phone candidate exists.",
                    )
                )
                continue

            candidate = Candidate(
                name=name,
                email=email,
                phone=phone,
                job_position=job_position,
                birth_date=_parse_candidate_birth_date(candidate_payload.get("birth_date")),
                apply_status=apply_status,
                created_by=actor_id,
            )
            await repo.add(candidate)
            await repo.flush()

            copied_paths: list[Path] = []
            row_document_count = 0
            try:
                for preview_document in row.documents:
                    source_path = resolve_absolute_path(preview_document.file_path)
                    document_type = (
                        preview_document.document_type
                        if preview_document.document_type in ALLOWED_DOCUMENT_TYPES
                        else "RESUME"
                    )
                    target_dir = resolve_document_dir(candidate.id, document_type)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    stored_file_name = build_stored_filename(
                        preview_document.original_file_name
                    )
                    target_path = target_dir / stored_file_name
                    shutil.copy2(source_path, target_path)
                    copied_paths.append(target_path)

                    extraction = await asyncio.to_thread(
                        extract_text_from_file,
                        build_public_file_path(target_path),
                        preview_document.file_ext,
                    )
                    document = Document(
                        document_type=document_type,
                        title=strip_extension(preview_document.original_file_name)
                        or stored_file_name,
                        original_file_name=preview_document.original_file_name,
                        stored_file_name=stored_file_name,
                        file_path=build_public_file_path(target_path),
                        file_ext=preview_document.file_ext,
                        mime_type=preview_document.mime_type,
                        file_size=target_path.stat().st_size,
                        candidate_id=candidate.id,
                        extracted_text=extraction.extracted_text,
                        extract_status=extraction.extract_status,
                        created_by=actor_id,
                    )
                    await repo.add(document)
                    row_document_count += 1

                await repo.flush()
                await db.commit()
                await repo.refresh(candidate)
                candidate_ids.append(candidate.id)
                created_count += 1
                document_count += row_document_count
            except Exception:
                await db.rollback()
                for copied_path in copied_paths:
                    try:
                        copied_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                errors.append(
                    DocumentBulkImportConfirmError(
                        row_id=row.row_id,
                        group_key=row.group_key,
                        reason="Failed while saving candidate documents.",
                    )
                )

        return DocumentBulkImportConfirmResponse(
            job_id=request.job_id,
            requested_count=len(target_rows),
            created_count=created_count,
            skipped_count=len(target_rows) - created_count,
            document_count=document_count,
            candidate_ids=candidate_ids,
            errors=errors,
        )

    @staticmethod
    def _stage_documents_from_zip(
        *,
        job_id: int,
        source_zip: dict,
    ) -> list[StagedDocument]:
        file_path = source_zip.get("file_path")
        if not file_path:
            raise ValueError("source_zip.file_path is missing.")

        preview_dir = _build_preview_dir(job_id)
        zip_path = resolve_absolute_path(file_path)
        staged_documents: list[StagedDocument] = []

        try:
            with zipfile.ZipFile(zip_path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    member_path = _safe_zip_member_path(info.filename)
                    extension = _validate_extension(member_path.name)
                    group_key, inferred_name = _infer_group_from_zip_path(member_path)
                    document_type = _infer_document_type(member_path.name)
                    stored_file_name = build_stored_filename(member_path.name)
                    target_path = preview_dir / "files" / group_key / document_type.lower() / stored_file_name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, target_path.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    staged_documents.append(
                        StagedDocument(
                            group_key=group_key,
                            original_file_name=Path(member_path.name).name,
                            stored_file_name=stored_file_name,
                            file_path=build_public_file_path(target_path),
                            file_ext=extension,
                            mime_type=mimetypes.guess_type(member_path.name)[0],
                            file_size=target_path.stat().st_size,
                            document_type=document_type,
                            inferred_candidate_name=inferred_name,
                        )
                    )
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid ZIP file.") from exc

        return staged_documents

    @staticmethod
    def _stage_documents_from_files(
        *,
        job_id: int,
        source_files: list[dict],
    ) -> list[StagedDocument]:
        preview_dir = _build_preview_dir(job_id)
        staged_documents: list[StagedDocument] = []

        for source_file in source_files:
            original_name = source_file.get("original_file_name") or ""
            file_path = source_file.get("file_path")
            if not original_name or not file_path:
                raise ValueError("source file metadata is incomplete.")

            extension = _validate_extension(original_name)
            group_key, inferred_name = _infer_group_from_filename(original_name)
            document_type = _infer_document_type(original_name)
            stored_file_name = build_stored_filename(original_name)
            source_path = resolve_absolute_path(file_path)
            target_path = preview_dir / "files" / group_key / document_type.lower() / stored_file_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
            staged_documents.append(
                StagedDocument(
                    group_key=group_key,
                    original_file_name=original_name,
                    stored_file_name=stored_file_name,
                    file_path=build_public_file_path(target_path),
                    file_ext=extension,
                    mime_type=source_file.get("mime_type") or mimetypes.guess_type(original_name)[0],
                    file_size=target_path.stat().st_size,
                    document_type=document_type,
                    inferred_candidate_name=inferred_name,
                )
            )

        return staged_documents

    @staticmethod
    async def preview_zip(
        *,
        db: AsyncSession,
        zip_file: UploadFile,
        default_job_position: str | None,
        default_apply_status: str | None,
        actor_id: int | None,
    ) -> DocumentBulkImportPreviewResponse:
        if zip_file.filename is None or get_extension(zip_file.filename) != "zip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="zip_file must be a ZIP file.",
            )

        job = await DocumentBulkImportService._create_preview_job(
            db=db,
            upload_mode="ZIP",
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
            actor_id=actor_id,
        )

        preview_dir = _build_preview_dir(job.id)
        zip_path = preview_dir / "source" / build_stored_filename(zip_file.filename)
        await _save_upload_to_path(zip_file, zip_path)

        staged_documents: list[StagedDocument] = []
        try:
            with zipfile.ZipFile(zip_path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    member_path = _safe_zip_member_path(info.filename)
                    extension = _validate_extension(member_path.name)
                    group_key, inferred_name = _infer_group_from_zip_path(member_path)
                    document_type = _infer_document_type(member_path.name)
                    stored_file_name = build_stored_filename(member_path.name)
                    target_path = preview_dir / "files" / group_key / document_type.lower() / stored_file_name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, target_path.open("wb") as target:
                        target.write(source.read())
                    staged_documents.append(
                        StagedDocument(
                            group_key=group_key,
                            original_file_name=Path(member_path.name).name,
                            stored_file_name=stored_file_name,
                            file_path=build_public_file_path(target_path),
                            file_ext=extension,
                            mime_type=mimetypes.guess_type(member_path.name)[0],
                            file_size=target_path.stat().st_size,
                            document_type=document_type,
                            inferred_candidate_name=inferred_name,
                        )
                    )
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP file.",
            ) from exc

        return await DocumentBulkImportService._build_preview_response(
            db=db,
            job=job,
            upload_mode="ZIP",
            staged_documents=staged_documents,
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
        )

    @staticmethod
    async def preview_files(
        *,
        db: AsyncSession,
        files: list[UploadFile],
        default_job_position: str | None,
        default_apply_status: str | None,
        actor_id: int | None,
    ) -> DocumentBulkImportPreviewResponse:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required.",
            )

        job = await DocumentBulkImportService._create_preview_job(
            db=db,
            upload_mode="FILES",
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
            actor_id=actor_id,
        )

        preview_dir = _build_preview_dir(job.id)
        staged_documents: list[StagedDocument] = []
        for upload_file in files:
            original_name = Path(upload_file.filename or "").name
            if not original_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file name is missing.",
                )
            extension = _validate_extension(original_name)
            group_key, inferred_name = _infer_group_from_filename(original_name)
            document_type = _infer_document_type(original_name)
            stored_file_name = build_stored_filename(original_name)
            target_path = preview_dir / "files" / group_key / document_type.lower() / stored_file_name
            file_size = await _save_upload_to_path(upload_file, target_path)
            staged_documents.append(
                StagedDocument(
                    group_key=group_key,
                    original_file_name=original_name,
                    stored_file_name=stored_file_name,
                    file_path=build_public_file_path(target_path),
                    file_ext=extension,
                    mime_type=upload_file.content_type or mimetypes.guess_type(original_name)[0],
                    file_size=file_size,
                    document_type=document_type,
                    inferred_candidate_name=inferred_name,
                )
            )

        return await DocumentBulkImportService._build_preview_response(
            db=db,
            job=job,
            upload_mode="FILES",
            staged_documents=staged_documents,
            default_job_position=default_job_position,
            default_apply_status=default_apply_status,
        )

    @staticmethod
    async def _create_preview_job(
        *,
        db: AsyncSession,
        upload_mode: str,
        default_job_position: str | None,
        default_apply_status: str | None,
        actor_id: int | None,
    ) -> AiJob:
        apply_status = _validate_apply_status(default_apply_status)
        job_position = _normalize_default_job_position(default_job_position)
        job = AiJob(
            job_type=AiJobType.DOCUMENT_BULK_IMPORT.value,
            status=AiJobStatus.QUEUED.value,
            target_type=AiJobTargetType.BULK_IMPORT.value,
            progress=2,
            current_step="preview_job_created",
            request_payload={
                "upload_mode": upload_mode,
                "default_job_position": job_position,
                "default_apply_status": apply_status,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.flush()
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def _build_preview_response(
        *,
        db: AsyncSession,
        job: AiJob,
        upload_mode: str,
        staged_documents: list[StagedDocument],
        default_job_position: str | None,
        default_apply_status: str | None,
        incremental: bool = False,
    ) -> DocumentBulkImportPreviewResponse:
        if not staged_documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No supported document files were found.",
            )

        grouped: dict[str, list[StagedDocument]] = {}
        for document in staged_documents:
            grouped.setdefault(document.group_key, []).append(document)

        repo = CandidateRepository(db)
        rows: list[DocumentBulkImportPreviewRow] = []
        sorted_groups = sorted(grouped.items(), key=lambda item: item[0])
        total_groups = len(sorted_groups)
        if incremental:
            initial_summary = DocumentBulkImportPreviewSummary(
                total_groups=total_groups,
                processed_groups=0,
                ready_count=0,
                needs_review_count=0,
                invalid_count=0,
                document_count=len(staged_documents),
            )
            job.progress = 20
            job.current_step = "preview_grouping_completed"
            job.result_payload = DocumentBulkImportPreviewResponse(
                job_id=job.id,
                upload_mode=upload_mode,
                summary=initial_summary,
                rows=[],
            ).model_dump(mode="json")
            await db.commit()

        for index, (group_key, documents) in enumerate(sorted_groups, start=1):
            if incremental:
                job.current_step = f"preview_processing_group_{index}_of_{total_groups}"
                job.progress = min(95, 20 + int(70 * (index - 1) / max(total_groups, 1)))
                await db.commit()

            row = await DocumentBulkImportService._build_preview_row(
                repo=repo,
                group_key=group_key,
                documents=documents,
                default_job_position=_normalize_default_job_position(default_job_position),
                default_apply_status=_validate_apply_status(default_apply_status),
            )
            rows.append(row)

            if incremental:
                partial_summary = DocumentBulkImportPreviewSummary(
                    total_groups=total_groups,
                    processed_groups=len(rows),
                    ready_count=sum(1 for item in rows if item.status == "READY"),
                    needs_review_count=sum(1 for item in rows if item.status == "NEEDS_REVIEW"),
                    invalid_count=sum(1 for item in rows if item.status == "INVALID"),
                    document_count=len(staged_documents),
                )
                job.progress = min(98, 20 + int(75 * index / max(total_groups, 1)))
                job.result_payload = DocumentBulkImportPreviewResponse(
                    job_id=job.id,
                    upload_mode=upload_mode,
                    summary=partial_summary,
                    rows=rows,
                ).model_dump(mode="json")
                await db.commit()

        summary = DocumentBulkImportPreviewSummary(
            total_groups=len(rows),
            processed_groups=len(rows),
            ready_count=sum(1 for row in rows if row.status == "READY"),
            needs_review_count=sum(1 for row in rows if row.status == "NEEDS_REVIEW"),
            invalid_count=sum(1 for row in rows if row.status == "INVALID"),
            document_count=len(staged_documents),
        )
        response = DocumentBulkImportPreviewResponse(
            job_id=job.id,
            upload_mode=upload_mode,
            summary=summary,
            rows=rows,
        )

        job.status = AiJobStatus.SUCCESS.value
        job.progress = 100
        job.current_step = "preview_completed"
        job.completed_at = datetime.now(timezone.utc)
        job.result_payload = response.model_dump(mode="json")
        await db.commit()
        return response

    @staticmethod
    async def _build_preview_row(
        *,
        repo: CandidateRepository,
        group_key: str,
        documents: list[StagedDocument],
        default_job_position: str | None,
        default_apply_status: str,
    ) -> DocumentBulkImportPreviewRow:
        extracted_texts: list[str] = []
        preview_documents: list[DocumentBulkImportPreviewDocument] = []
        errors: list[str] = []
        warnings: list[str] = []

        for document in documents:
            extraction = None
            error_message = None
            extracted_text = None
            if (document.file_ext or "").lower() in SUPPORTED_EXTRACTION_EXTENSIONS:
                extraction = await asyncio.to_thread(
                    extract_text_from_file,
                    document.file_path,
                    document.file_ext,
                )
                extracted_text = extraction.extracted_text
                if extracted_text:
                    extracted_texts.append(extracted_text)
            else:
                error_message = "File extension is uploadable but text extraction is not supported."
                warnings.append(f"{document.original_file_name}: extraction unsupported")

            preview_documents.append(
                DocumentBulkImportPreviewDocument(
                    original_file_name=document.original_file_name,
                    stored_file_name=document.stored_file_name,
                    file_path=document.file_path,
                    file_ext=document.file_ext,
                    mime_type=document.mime_type,
                    file_size=document.file_size,
                    document_type=document.document_type if document.document_type in ALLOWED_DOCUMENT_TYPES else "RESUME",
                    extract_status=extraction.extract_status if extraction else "FAILED",
                    extract_strategy=extraction.extract_strategy if extraction else "unsupported",
                    extract_quality_score=extraction.extract_quality_score if extraction else 0,
                    extract_source_type=extraction.source_type if extraction else "unsupported",
                    detected_document_type=extraction.document_type if extraction else None,
                    extracted_text_length=len(extracted_text or ""),
                    extracted_text_preview=_build_text_preview(extracted_text),
                    extract_meta=extraction.extract_meta if extraction else None,
                    error_message=error_message,
                )
            )

        merged_text = "\n\n".join(extracted_texts)
        inferred_name = next((document.inferred_candidate_name for document in documents if document.inferred_candidate_name), None)
        profile = await _extract_profile(
            text=merged_text,
            inferred_name=inferred_name,
            default_job_position=default_job_position,
        )
        profile.job_position = _append_experience_suffix(
            profile.job_position or default_job_position,
            _infer_experience_suffix(merged_text),
        )

        if not merged_text.strip():
            errors.append("No text could be extracted from this document group.")
        for field_name in ("name", "email", "phone"):
            if field_name in profile.missing_fields:
                warnings.append(f"{field_name} is missing")

        duplicate_candidate_id: int | None = None
        if profile.email:
            duplicate = await repo.find_active_by_email(profile.email)
            if duplicate:
                duplicate_candidate_id = duplicate.id
                warnings.append("Duplicate email candidate exists.")
        if duplicate_candidate_id is None and profile.phone:
            phone_digits = re.sub(r"\D", "", profile.phone)
            if phone_digits:
                duplicate = await repo.find_active_by_phone_digits(phone_digits)
                if duplicate:
                    duplicate_candidate_id = duplicate.id
                    warnings.append("Duplicate phone candidate exists.")

        if errors:
            row_status = "INVALID"
        elif profile.confidence_score >= 0.8 and profile.name and (profile.email or profile.phone) and duplicate_candidate_id is None:
            row_status = "READY"
        else:
            row_status = "NEEDS_REVIEW"

        normalized_birth_date, birth_date_warning = _normalize_birth_date_for_candidate(
            profile.birth_date
        )
        if birth_date_warning:
            warnings.append(birth_date_warning)

        candidate = {
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone,
            "birth_date": normalized_birth_date,
            "job_position": profile.job_position or default_job_position,
            "apply_status": default_apply_status,
        }

        return DocumentBulkImportPreviewRow(
            row_id=str(uuid4()),
            status=row_status,
            group_key=group_key,
            inferred_candidate_name=inferred_name,
            extracted_profile=profile,
            candidate=candidate,
            documents=preview_documents,
            document_count=len(preview_documents),
            confidence_score=profile.confidence_score,
            duplicate_candidate_id=duplicate_candidate_id,
            errors=errors,
            warnings=warnings + profile.warnings,
        )
