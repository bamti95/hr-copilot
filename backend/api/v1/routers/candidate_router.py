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

router = APIRouter(prefix="/candidates", tags=["candidate"])


@router.get("", response_model=CandidateListResponse)
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


@router.get("/statistics", response_model=CandidateStatisticsResponse)
async def get_candidate_statistics(
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateStatisticsResponse:
    return await CandidateService.get_statistics(db=db)


@router.get("/sample-folders", response_model=CandidateSampleFolderListResponse)
async def list_candidate_sample_folders(
    _: Manager = Depends(get_current_active_manager),
) -> CandidateSampleFolderListResponse:
    return await CandidateService.list_sample_folders()


@router.post(
    "/bulk-import",
    response_model=CandidateBulkImportResponse,
    status_code=status.HTTP_201_CREATED,
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


@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(
    candidate_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDetailResponse:
    return await CandidateService.get_candidate(db=db, candidate_id=candidate_id)


@router.get(
    "/{candidate_id}/documents/{document_id}",
    response_model=CandidateDocumentDetailResponse,
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


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{candidate_id}", response_model=CandidateResponse)
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


@router.patch("/{candidate_id}/status", response_model=CandidateStatusPatchResponse)
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


@router.get("/{candidate_id}/documents/{document_id}/download")
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


@router.put("/{candidate_id}/documents/{document_id}", response_model=CandidateDocumentResponse)
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


@router.delete("/{candidate_id}", response_model=CandidateDeleteResponse)
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
