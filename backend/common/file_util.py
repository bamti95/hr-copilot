from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from core.config import get_settings

settings = get_settings()

FILES_PREFIX = "/files"
DOCUMENT_ROOT_DIR = "documents"
CANDIDATE_DIR = "candidates"
ALLOWED_DOCUMENT_TYPES = {
    "RESUME",
    "PORTFOLIO",
    "COVER_LETTER",
    "CAREER_DESCRIPTION",
    "ROLE_PROFILE",
}

ALLOWED_EXTENSIONS = {
    "pdf", 
    "doc",
    "docx",
    "txt",
    "hwp",
    "hwpx",
}

READ_CHUNK_SIZE = 1024 * 1024


@dataclass(slots=True)
class SavedFileResult:
    """
    업로드 후 저장된 파일의 메타데이터를 담는 결과 객체.

    Attributes:
        title:
            파일 제목. 일반적으로 원본 파일명에서 확장자를 제거한 값으로 사용한다.
        original_file_name:
            사용자가 업로드한 원본 파일명.
        stored_file_name:
            서버 디렉터리에 실제 저장된 파일명.
            UUID 기반으로 생성되어 파일명 충돌을 방지한다.
        file_path:
            DB 저장 및 프론트 노출용 공개 경로.
            예: /files/documents/candidates/3/resume/uuid.pdf
        file_ext:
            파일 확장자. 확장자가 없으면 None.
        mime_type:
            업로드 시 전달된 MIME 타입.
        file_size:
            저장된 파일 크기(byte 단위).
    """
    title: str
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_ext: str | None
    mime_type: str | None
    file_size: int | None


def get_upload_root() -> Path:
    """
    업로드 루트 디렉터리 절대경로를 반환한다.

    설정값(settings.UPLOAD_PATH)을 기준으로 Path 객체를 생성한다.
    업로드 경로가 비어 있으면 서버 설정 오류로 판단하여 ValueError를 발생시킨다.

    Returns:
        Path:
            업로드 파일 저장의 최상위 루트 경로.

    Raises:
        ValueError:
            UPLOAD_PATH가 비어 있거나 설정되지 않은 경우.
    """
    upload_path = settings.UPLOAD_PATH.strip()
    if not upload_path:
        raise ValueError("UPLOAD_PATH is not configured.")
    return Path(upload_path)


def sanitize_document_type(document_type: str) -> str:
    """
    문서 유형 문자열을 정규화하고 허용된 값인지 검증한다.

    입력값의 앞뒤 공백을 제거하고 대문자로 통일한 뒤,
    시스템에서 허용하는 문서 유형(ALLOWED_DOCUMENT_TYPES)에 포함되는지 검사한다.

    Args:
        document_type:
            사용자가 요청한 문서 유형.
            예: 'resume', 'portfolio', 'COVER_LETTER'

    Returns:
        str:
            검증을 통과한 정규화된 문서 유형 문자열.
            예: 'RESUME'

    Raises:
        HTTPException:
            지원하지 않는 문서 유형인 경우 400 Bad Request.
    """
    normalized = document_type.strip().upper()
    if normalized not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document_type: {document_type}",
        )
    return normalized


def get_extension(filename: str | None) -> str:
    """
    파일명에서 확장자를 추출하여 소문자로 반환한다.

    파일명이 없거나 '.' 이 포함되지 않은 경우 빈 문자열을 반환한다.

    Args:
        filename:
            원본 파일명 또는 저장 파일명.

    Returns:
        str:
            소문자 확장자.
            예: 'pdf', 'docx'
            확장자가 없으면 '' 반환.
    """
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def strip_extension(filename: str | None) -> str:
    """
    파일명에서 확장자를 제거한 순수 이름만 반환한다.

    경로가 포함된 문자열이 들어와도 Path(filename).name 을 사용해
    마지막 파일명만 추출한 뒤 확장자를 제거한다.

    Args:
        filename:
            파일명 또는 파일 경로 문자열.

    Returns:
        str:
            확장자가 제거된 파일명.
            파일명이 없으면 빈 문자열 반환.
    """
    if not filename:
        return ""
    leaf_name = Path(filename).name
    if "." not in leaf_name:
        return leaf_name
    return leaf_name.rsplit(".", 1)[0]


def validate_upload_file(upload_file: UploadFile) -> None:
    """
    업로드 파일의 기본 유효성을 검증한다.

    검증 항목:
    1. 파일명이 존재하는지
    2. 파일 확장자가 허용 목록(ALLOWED_EXTENSIONS)에 포함되는지

    Args:
        upload_file:
            FastAPI UploadFile 객체.

    Raises:
        HTTPException:
            - 파일명이 비어 있으면 400 Bad Request
            - 허용되지 않은 확장자면 400 Bad Request
    """
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
    """
    지원자 ID와 문서 유형을 기반으로 실제 저장 디렉터리 경로를 계산한다.

    최종 경로 패턴:
        {UPLOAD_PATH}/documents/candidates/{candidate_id}/{document_type_lower}

    예:
        /home/upload/bamti/documents/candidates/3/resume

    Args:
        candidate_id:
            지원자 식별자.
        document_type:
            문서 유형. 내부적으로 sanitize_document_type()을 통해 검증된다.

    Returns:
        Path:
            해당 파일이 저장될 절대 디렉터리 경로.
    """
    normalized_type = sanitize_document_type(document_type).lower()
    return (
        get_upload_root()
        / DOCUMENT_ROOT_DIR
        / CANDIDATE_DIR
        / str(candidate_id)
        / normalized_type
    )


def build_stored_filename(original_filename: str) -> str:
    """
    충돌 방지를 위한 서버 저장용 파일명을 생성한다.

    원본 파일의 확장자는 유지하되, 본문은 UUID로 교체한다.

    예:
        'resume.pdf' -> '550e8400-e29b-41d4-a716-446655440000.pdf'

    Args:
        original_filename:
            사용자가 업로드한 원본 파일명.

    Returns:
        str:
            UUID 기반 저장 파일명.
    """
    extension = get_extension(original_filename)
    suffix = f".{extension}" if extension else ""
    return f"{uuid4()}{suffix}"


def build_public_file_path(abs_path: Path) -> str:
    """
    서버 절대경로를 공개 접근용 파일 경로(/files/...)로 변환한다.

    업로드 루트 기준 상대경로를 추출한 뒤,
    프론트/DB 저장에 사용하는 공개 prefix('/files')를 붙인다.

    예:
        /home/upload/bamti/documents/candidates/3/resume/a.pdf
        -> /files/documents/candidates/3/resume/a.pdf

    Args:
        abs_path:
            서버 내부의 절대 파일 경로.

    Returns:
        str:
            공개 파일 접근 경로.
    """
    relative_path = abs_path.relative_to(get_upload_root())
    return f"{FILES_PREFIX}/{relative_path.as_posix()}"


def resolve_absolute_path(file_path: str) -> Path:
    """
    공개 파일 경로(/files/...)를 서버 절대경로로 역변환한다.

    DB에 저장된 공개 경로를 실제 물리 파일 경로로 변환할 때 사용한다.

    예:
        /files/documents/candidates/3/resume/a.pdf
        -> /home/upload/bamti/documents/candidates/3/resume/a.pdf

    Args:
        file_path:
            /files/ 로 시작하는 공개 파일 경로.

    Returns:
        Path:
            실제 서버 파일 절대경로.

    Raises:
        ValueError:
            file_path가 비어 있거나 /files/ prefix로 시작하지 않는 경우.
    """
    if not file_path or not file_path.startswith(f"{FILES_PREFIX}/"):
        raise ValueError("file_path must start with /files/.")

    relative_path = file_path.removeprefix(f"{FILES_PREFIX}/")
    return get_upload_root() / Path(relative_path)


def build_download_response(
    file_path: str,
    download_name: str | None = None,
    media_type: str | None = None,
) -> FileResponse:
    """
    다운로드 응답용 FileResponse 객체를 생성한다.

    공개 파일 경로를 실제 절대경로로 변환한 뒤,
    파일 존재 여부를 검사하고 다운로드 응답을 반환한다.

    Args:
        file_path:
            /files/... 형태의 공개 파일 경로.
        download_name:
            브라우저 다운로드 시 표시할 파일명.
            None이면 서버 파일명 또는 기본 처리 방식 사용.
        media_type:
            응답 MIME 타입. 필요 시 명시적으로 지정 가능.

    Returns:
        FileResponse:
            FastAPI 파일 다운로드 응답 객체.

    Raises:
        HTTPException:
            대상 파일이 존재하지 않거나 일반 파일이 아니면 404 Not Found.
    """
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
    """
    공개 파일 경로를 기준으로 실제 파일을 삭제한다.

    DB에 저장된 /files/... 경로를 실제 절대경로로 변환한 후 unlink()를 수행한다.
    삭제 중 OS 레벨 오류가 발생하면 500 예외로 변환한다.

    Args:
        file_path:
            삭제 대상 공개 파일 경로.
        missing_ok:
            True이면 파일이 없어도 예외 없이 통과한다.
            False이면 파일이 없을 때 FileNotFoundError가 발생할 수 있다.

    Raises:
        HTTPException:
            파일 삭제 중 OS 오류가 발생한 경우 500 Internal Server Error.
    """
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
    """
    단일 업로드 파일을 실제 디스크에 저장하고 메타데이터를 반환한다.

    내부 처리 순서:
    1. 파일 기본 유효성 검증
    2. 저장 대상 디렉터리 계산 및 생성
    3. UUID 기반 저장 파일명 생성
    4. 업로드 스트림을 chunk 단위로 읽어 파일 저장
    5. 저장 결과를 SavedFileResult로 반환

    Args:
        candidate_id:
            지원자 ID.
        document_type:
            문서 유형.
        upload_file:
            저장할 업로드 파일 객체.

    Returns:
        SavedFileResult:
            저장 완료된 파일의 메타데이터.

    Raises:
        HTTPException:
            디스크 저장 중 오류가 발생하면 500 Internal Server Error.
    """
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


async def save_upload_files(
    candidate_id: int,
    document_type: str,
    files: list[UploadFile],
) -> list[SavedFileResult]:
    """
    동일 문서 유형에 속한 여러 파일을 일괄 저장한다.

    주요 특징:
    - candidate_id 유효성 검사
    - 빈 파일 목록 방지
    - document_type 사전 검증
    - 저장 도중 하나라도 실패하면, 이전에 저장된 파일들을 롤백(삭제) 시도

    Args:
        candidate_id:
            지원자 ID. 0보다 커야 한다.
        document_type:
            모든 파일에 공통으로 적용할 문서 유형.
        files:
            저장할 업로드 파일 목록.

    Returns:
        list[SavedFileResult]:
            저장 성공한 파일들의 메타데이터 목록.

    Raises:
        HTTPException:
            - candidate_id가 0 이하이면 400
            - 파일 목록이 비어 있으면 400
            - 저장 중 파일 검증/저장 실패 시 관련 예외 재전파
    """
    if candidate_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="candidate_id must be a positive integer.",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    sanitize_document_type(document_type)

    saved_files: list[SavedFileResult] = []
    saved_paths: list[Path] = []

    try:
        for upload_file in files:
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


async def save_upload_file_pairs(
    candidate_id: int,
    document_file_pairs: list[tuple[str, UploadFile]],
) -> list[SavedFileResult]:
    """
    문서 유형이 서로 다른 파일들을 한 번에 저장한다.

    각 항목은 (document_type, upload_file) 쌍으로 구성되며,
    파일마다 다른 문서 유형을 지정할 수 있다.

    예:
        [
            ("RESUME", resume_file),
            ("PORTFOLIO", portfolio_file),
        ]

    주요 특징:
    - candidate_id 유효성 검사
    - 빈 목록 방지
    - 각 항목별 document_type 검증
    - 중간 실패 시 이전 저장 파일들에 대해 롤백(삭제) 시도

    Args:
        candidate_id:
            지원자 ID. 0보다 커야 한다.
        document_file_pairs:
            (문서유형, 업로드파일) 튜플 목록.

    Returns:
        list[SavedFileResult]:
            저장 성공한 파일들의 메타데이터 목록.

    Raises:
        HTTPException:
            - candidate_id가 0 이하이면 400
            - 파일 목록이 비어 있으면 400
            - 저장 실패 시 관련 예외 재전파
    """
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
