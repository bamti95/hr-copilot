from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.job_posting import (
    JobPostingAnalyzeResponse,
    JobPostingAnalyzeTextRequest,
    JobPostingAnalysisReportResponse,
    JobPostingCreateRequest,
    JobPostingListResponse,
    JobPostingResponse,
    KnowledgeChunkListResponse,
    KnowledgeIndexResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSeedResponse,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)
from services.job_posting_knowledge_service import JobPostingKnowledgeService
from services.job_posting_service import JobPostingService


router = APIRouter(prefix="/job-postings", tags=["채용공고 컴플라이언스 점검"])


@router.post(
    "",
    response_model=JobPostingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="채용공고 등록",
)
async def create_job_posting(
    request_body: JobPostingCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    return await JobPostingService.create_posting(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.get(
    "",
    response_model=JobPostingListResponse,
    summary="채용공고 목록 조회",
)
async def list_job_postings(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingListResponse:
    return await JobPostingService.list_postings(
        db=db,
        page=page,
        size=size,
        keyword=keyword,
    )


@router.post(
    "/analyze-text",
    response_model=JobPostingAnalyzeResponse,
    summary="채용공고 텍스트 분석",
)
async def analyze_job_posting_text(
    request_body: JobPostingAnalyzeTextRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingAnalyzeResponse:
    return await JobPostingService.analyze_text(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.post(
    "/analyze-file",
    response_model=JobPostingAnalyzeResponse,
    summary="채용공고 파일 분석",
)
async def analyze_job_posting_file(
    file: Annotated[UploadFile, File(...)],
    job_title: Annotated[str | None, Form()] = None,
    company_name: Annotated[str | None, Form()] = None,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingAnalyzeResponse:
    return await JobPostingService.analyze_upload_file(
        db=db,
        upload_file=file,
        job_title=job_title,
        company_name=company_name,
        actor_id=current_manager.id,
    )


@router.post(
    "/{posting_id}/analysis-reports",
    response_model=JobPostingAnalysisReportResponse,
    summary="기존 채용공고 재분석",
)
async def analyze_existing_job_posting(
    posting_id: int,
    analysis_type: str = Query("FULL"),
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingAnalysisReportResponse:
    return await JobPostingService.analyze_existing(
        db=db,
        posting_id=posting_id,
        analysis_type=analysis_type,
        actor_id=current_manager.id,
    )


@router.get(
    "/{posting_id}/analysis-reports",
    response_model=list[JobPostingAnalysisReportResponse],
    summary="채용공고 분석 리포트 목록 조회",
)
async def list_job_posting_reports(
    posting_id: int,
    limit: int = Query(20, ge=1, le=100),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> list[JobPostingAnalysisReportResponse]:
    return await JobPostingService.list_reports(
        db=db,
        posting_id=posting_id,
        limit=limit,
    )


@router.get(
    "/analysis-reports/{report_id}",
    response_model=JobPostingAnalysisReportResponse,
    summary="채용공고 분석 리포트 상세 조회",
)
async def get_job_posting_report(
    report_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingAnalysisReportResponse:
    return await JobPostingService.get_report(db=db, report_id=report_id)


@router.post(
    "/knowledge-sources/upload",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="RAG 지식문서 업로드",
)
async def upload_knowledge_source(
    file: Annotated[UploadFile, File(...)],
    source_type: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    version_label: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSourceResponse:
    return await JobPostingKnowledgeService.upload_source(
        db=db,
        upload_file=file,
        source_type=source_type,
        title=title,
        version_label=version_label,
        source_url=source_url,
        actor_id=current_manager.id,
    )


@router.get(
    "/knowledge-sources",
    response_model=KnowledgeSourceListResponse,
    summary="RAG 지식문서 목록 조회",
)
async def list_knowledge_sources(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    source_type: str | None = Query(None),
    keyword: str | None = Query(None),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSourceListResponse:
    return await JobPostingKnowledgeService.list_sources(
        db=db,
        page=page,
        size=size,
        source_type=source_type,
        keyword=keyword,
    )


@router.post(
    "/knowledge-sources/{source_id}/index",
    response_model=KnowledgeIndexResponse,
    summary="RAG 지식문서 인덱싱",
)
async def index_knowledge_source(
    source_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeIndexResponse:
    return await JobPostingKnowledgeService.index_source(db=db, source_id=source_id)


@router.get(
    "/knowledge-sources/{source_id}/chunks",
    response_model=KnowledgeChunkListResponse,
    summary="RAG 지식문서 청크 목록 조회",
)
async def list_knowledge_chunks(
    source_id: int,
    limit: int = Query(100, ge=1, le=1000),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeChunkListResponse:
    return await JobPostingKnowledgeService.list_chunks(
        db=db,
        source_id=source_id,
        limit=limit,
    )


@router.post(
    "/knowledge-sources/search",
    response_model=KnowledgeSearchResponse,
    summary="RAG 기반지식 하이브리드 검색",
)
async def search_knowledge_sources(
    request_body: KnowledgeSearchRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSearchResponse:
    return await JobPostingKnowledgeService.search_knowledge(
        db=db,
        request=request_body,
    )


@router.post(
    "/knowledge-sources/seed-source-data",
    response_model=KnowledgeSeedResponse,
    summary="샘플 source_data 법률문서 일괄 적재",
)
async def seed_source_data(
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSeedResponse:
    return await JobPostingKnowledgeService.seed_source_data(
        db=db,
        actor_id=current_manager.id,
    )


@router.get(
    "/{posting_id}",
    response_model=JobPostingResponse,
    summary="채용공고 상세 조회",
)
async def get_job_posting(
    posting_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    return await JobPostingService.get_posting(db=db, posting_id=posting_id)
