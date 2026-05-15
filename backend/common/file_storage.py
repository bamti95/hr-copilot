"""파일 저장 경로 계산과 공용 파일 루트 접근 함수를 제공한다."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from common.document_types import (
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_EXTENSIONS,
    CANDIDATE_DIR,
    DOCUMENT_ROOT_DIR,
    FILES_PREFIX,
    READ_CHUNK_SIZE,
    SavedFileResult,
)
from core.config import get_settings

settings = get_settings()
'''
업로드 저장, 경로 계산, 다운로드, 삭제
save_upload_file_pairs()와 테스트 라우터 호환용 save_upload_files() 포함
'''
def get_upload_root() -> Path:
    upload_path = settings.UPLOAD_PATH.strip()
    if not upload_path:
        raise ValueError("UPLOAD_PATH is not configured.")
    return Path(upload_path)


def sanitize_document_type(document_type: str) -> str:
    normalized = document_type.strip().upper()
    if normalized not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document_type: {document_type}",
        )
    return normalized


def get_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def strip_extension(filename: str | None) -> str:
    if not filename:
        return ""
    leaf_name = Path(filename).name
    if "." not in leaf_name:
        return leaf_name
    return leaf_name.rsplit(".", 1)[0]


def validate_upload_file(upload_file: UploadFile) -> None:
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


def resolve_document_dir(candidate_id: int, document_type: str) -> Path:
    normalized_type = sanitize_document_type(document_type).lower()
    return (
        get_upload_root()
        / DOCUMENT_ROOT_DIR
        / CANDIDATE_DIR
        / str(candidate_id)
        / normalized_type
    )


def build_stored_filename(original_filename: str) -> str:
    from uuid import uuid4

    extension = get_extension(original_filename)
    suffix = f".{extension}" if extension else ""
    return f"{uuid4()}{suffix}"


def build_public_file_path(abs_path: Path) -> str:
    relative_path = abs_path.relative_to(get_upload_root())
    return f"{FILES_PREFIX}/{relative_path.as_posix()}"


def resolve_absolute_path(file_path: str) -> Path:
    if not file_path or not file_path.startswith(f"{FILES_PREFIX}/"):
        raise ValueError("file_path must start with /files/.")

    relative_path = file_path.removeprefix(f"{FILES_PREFIX}/")
    return get_upload_root() / Path(relative_path)


def build_download_response(
    file_path: str,
    download_name: str | None = None,
    media_type: str | None = None,
) -> FileResponse:
    abs_path = resolve_absolute_path(file_path)
    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file was not found.",
        )

    return FileResponse(
        path=abs_path,
        filename=download_name,
        media_type=media_type,
    )


def delete_file_by_path(file_path: str, *, missing_ok: bool = True) -> None:
    abs_path = resolve_absolute_path(file_path)
    try:
        abs_path.unlink(missing_ok=missing_ok)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file.",
        ) from exc


async def _save_single_file(
    candidate_id: int,
    document_type: str,
    upload_file: UploadFile,
) -> SavedFileResult:
    validate_upload_file(upload_file)

    target_dir = resolve_document_dir(candidate_id, document_type)
    target_dir.mkdir(parents=True, exist_ok=True)

    original_file_name = Path(upload_file.filename or "").name
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
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {original_file_name}",
        ) from exc
    finally:
        await upload_file.close()

    return SavedFileResult(
        title=strip_extension(original_file_name) or stored_file_name,
        original_file_name=original_file_name,
        stored_file_name=stored_file_name,
        file_path=build_public_file_path(target_path),
        file_ext=get_extension(original_file_name) or None,
        mime_type=upload_file.content_type,
        file_size=file_size,
    )


async def save_upload_file_pairs(
    candidate_id: int,
    document_file_pairs: list[tuple[str, UploadFile]],
) -> list[SavedFileResult]:
    if candidate_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="candidate_id must be a positive integer.",
        )

    if not document_file_pairs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    saved_files: list[SavedFileResult] = []
    saved_paths: list[Path] = []

    try:
        for document_type, upload_file in document_file_pairs:
            sanitize_document_type(document_type)
            result = await _save_single_file(candidate_id, document_type, upload_file)
            saved_files.append(result)
            saved_paths.append(resolve_absolute_path(result.file_path))
    except Exception:
        for saved_path in saved_paths:
            try:
                saved_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    return saved_files


async def save_upload_files(
    candidate_id: int,
    document_type: str,
    files: list[UploadFile],
) -> list[SavedFileResult]:
    return await save_upload_file_pairs(
        candidate_id=candidate_id,
        document_file_pairs=[(document_type, file) for file in files],
    )

