"""지원자와 문서 관리 API 라우터다."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.candidate import ApplyStatus
from models.manager import Manager
from schemas.candidate import (
    CandidateBulkImportRequest,
    CandidateBulkImportResponse,
    CandidateCreateRequest,
    CandidateDetailResponse,
    DocumentBulkImportConfirmRequest,
    DocumentBulkImportConfirmResponse,
    DocumentBulkImportPreviewJobListResponse,
    DocumentBulkImportPreviewJobResponse,
    DocumentBulkImportPreviewStartResponse,
    CandidateDocumentDetailResponse,
    CandidateDeleteResponse,
    CandidateDocumentResponse,
    CandidateDocumentDeleteResponse,
    CandidateDocumentUploadResponse,
    CandidateListResponse,
    CandidateResponse,
    CandidateSampleFolderListResponse,
    CandidateStatisticsResponse,
    CandidateStatusPatchRequest,
    CandidateStatusPatchResponse,
    CandidateUpdateRequest,
)
from services.candidate_service import CandidateService
from services.document_bulk_import_service import DocumentBulkImportService

router = APIRouter(prefix="/candidates", tags=["지원자 관리"])


@router.get("",
            response_model=CandidateListResponse,
            summary="지원자 목록 조회",
)
async def list_candidates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    apply_status: ApplyStatus | None = Query(None),
    search: str | None = Query(None),
    target_job: str | None = Query(None, max_length=50),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateListResponse:
    return await CandidateService.list_candidates(
        db=db,
        page=page,
        limit=limit,
        apply_status=apply_status,
        search=search,
        target_job=target_job,
    )


@router.get("/statistics",
            response_model=CandidateStatisticsResponse,
            summary="지원자 통계 조회",
            )
async def get_candidate_statistics(
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateStatisticsResponse:
    return await CandidateService.get_statistics(db=db)


@router.get("/sample-folders",
            response_model=CandidateSampleFolderListResponse,
            summary="지원자 샘플 폴더 목록 조회",)
async def list_candidate_sample_folders(
    _: Manager = Depends(get_current_active_manager),
) -> CandidateSampleFolderListResponse:
    return await CandidateService.list_sample_folders()


@router.post(
    "/bulk-import",
    response_model=CandidateBulkImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="가상 지원자 대량 등록"
)
async def bulk_import_candidates(
    request_body: CandidateBulkImportRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateBulkImportResponse:
    return await CandidateService.bulk_import_candidates(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.post(
    "/document-bulk/preview",
    response_model=DocumentBulkImportPreviewStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="문서 ZIP 기반 지원자 일괄등록 미리보기",
)
async def preview_document_bulk_zip(
    zip_file: Annotated[UploadFile, File(...)],
    background_tasks: BackgroundTasks,
    default_job_position: Annotated[str | None, Form()] = None,
    default_apply_status: Annotated[str | None, Form()] = None,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> DocumentBulkImportPreviewStartResponse:
    response = await DocumentBulkImportService.start_preview_zip(
        db=db,
        zip_file=zip_file,
        default_job_position=default_job_position,
        default_apply_status=default_apply_status,
        actor_id=current_manager.id,
    )
    background_tasks.add_task(DocumentBulkImportService.run_preview_job, response.job_id)
    return response


@router.post(
    "/document-bulk/preview/files",
    response_model=DocumentBulkImportPreviewStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="다중 파일 기반 지원자 일괄등록 미리보기",
)
async def preview_document_bulk_files(
    files: Annotated[list[UploadFile], File(...)],
    background_tasks: BackgroundTasks,
    default_job_position: Annotated[str | None, Form()] = None,
    default_apply_status: Annotated[str | None, Form()] = None,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> DocumentBulkImportPreviewStartResponse:
    response = await DocumentBulkImportService.start_preview_files(
        db=db,
        files=files,
        default_job_position=default_job_position,
        default_apply_status=default_apply_status,
        actor_id=current_manager.id,
    )
    background_tasks.add_task(DocumentBulkImportService.run_preview_job, response.job_id)
    return response


@router.get(
    "/document-bulk/preview/jobs",
    response_model=DocumentBulkImportPreviewJobListResponse,
    summary="문서 기반 지원자 일괄등록 미리보기 작업 목록 조회",
)
async def list_document_bulk_preview_jobs(
    active_only: bool = Query(True),
    limit: int = Query(10, ge=1, le=50),
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> DocumentBulkImportPreviewJobListResponse:
    return await DocumentBulkImportService.list_preview_jobs(
        db=db,
        actor_id=current_manager.id,
        active_only=active_only,
        limit=limit,
    )


@router.get(
    "/document-bulk/preview/jobs/{job_id}",
    response_model=DocumentBulkImportPreviewJobResponse,
    summary="문서 기반 지원자 일괄등록 미리보기 작업 조회",
)
async def get_document_bulk_preview_job(
    job_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> DocumentBulkImportPreviewJobResponse:
    return await DocumentBulkImportService.get_preview_job(db=db, job_id=job_id)


@router.post(
    "/document-bulk/import",
    response_model=DocumentBulkImportConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="문서 기반 지원자 일괄등록 확정 저장",
)
async def confirm_document_bulk_import(
    request_body: DocumentBulkImportConfirmRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> DocumentBulkImportConfirmResponse:
    return await DocumentBulkImportService.confirm_import(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.get("/{candidate_id}",
            response_model=CandidateDetailResponse,
            summary="지원자 상세 조회")
async def get_candidate(
    candidate_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDetailResponse:
    return await CandidateService.get_candidate(db=db, candidate_id=candidate_id)


@router.get(
    "/{candidate_id}/documents/{document_id}",
    response_model=CandidateDocumentDetailResponse,
    summary="지원자 문서 상세 조회"
)
async def get_candidate_document(
    candidate_id: int,
    document_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDocumentDetailResponse:
    return await CandidateService.get_candidate_document(
        db=db,
        candidate_id=candidate_id,
        document_id=document_id,
    )


@router.post("",
             response_model=CandidateResponse,
             status_code=status.HTTP_201_CREATED,
             summary="지원자 등록")
async def create_candidate(
    request_body: CandidateCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateResponse:
    return await CandidateService.create_candidate(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.put("/{candidate_id}",
            response_model=CandidateResponse,
            summary="지원자 수정")
async def update_candidate(
    candidate_id: int,
    request_body: CandidateUpdateRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateResponse:
    return await CandidateService.update_candidate(
        db=db,
        candidate_id=candidate_id,
        request=request_body,
    )


@router.patch("/{candidate_id}/status",
              response_model=CandidateStatusPatchResponse,
              summary="지원자 지원 상태 변경")
async def patch_candidate_status(
    candidate_id: int,
    request_body: CandidateStatusPatchRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateStatusPatchResponse:
    return await CandidateService.patch_status(
        db=db,
        candidate_id=candidate_id,
        request=request_body,
    )


@router.post(
    "/{candidate_id}/documents",
    response_model=CandidateDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="지원자 문서 업로드"
)
async def upload_candidate_documents(
    candidate_id: int,
    document_types: Annotated[list[str], Form(...)],
    files: Annotated[list[UploadFile], File(...)],
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDocumentUploadResponse:
    response = await CandidateService.upload_candidate_documents(
        db=db,
        candidate_id=candidate_id,
        document_types=document_types,
        files=files,
        actor_id=current_manager.id,
    )

    document_ids = [document.id for document in response.documents]
    if document_ids:
        background_tasks.add_task(
            CandidateService.run_document_extraction,
            document_ids,
        )

    return response


@router.get("/{candidate_id}/documents/{document_id}/download",
            summary="지원자 문서 다운로드")
async def download_candidate_document(
    candidate_id: int,
    document_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
):
    return await CandidateService.download_candidate_document(
        db=db,
        candidate_id=candidate_id,
        document_id=document_id,
    )


@router.delete(
    "/{candidate_id}/documents/{document_id}",
    response_model=CandidateDocumentDeleteResponse,
    summary="지원자 문서 삭제"
)
async def delete_candidate_document(
    candidate_id: int,
    document_id: int,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDocumentDeleteResponse:
    return await CandidateService.delete_candidate_document(
        db=db,
        candidate_id=candidate_id,
        document_id=document_id,
        actor_id=current_manager.id,
    )


@router.put("/{candidate_id}/documents/{document_id}",
            response_model=CandidateDocumentResponse,
            summary="지원자 문서 교체")
async def replace_candidate_document(
    candidate_id: int,
    document_id: int,
    document_type: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDocumentResponse:
    response = await CandidateService.replace_candidate_document(
        db=db,
        candidate_id=candidate_id,
        document_id=document_id,
        document_type=document_type,
        upload_file=file,
        actor_id=current_manager.id,
    )
    background_tasks.add_task(
        CandidateService.run_document_extraction,
        [response.id],
    )
    return response


@router.delete("/{candidate_id}",
               response_model=CandidateDeleteResponse,
               summary="지원자 삭제")
async def delete_candidate(
    candidate_id: int,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDeleteResponse:
    return await CandidateService.delete_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=current_manager.id,
    )
