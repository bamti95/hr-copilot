"""채용공고 분석 실행과 실험 평가를 총괄하는 서비스다."""

from __future__ import annotations

import hashlib
import asyncio
import json
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
from sqlalchemy import desc, select
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
from models.job_posting_experiment_case_result import JobPostingExperimentCaseResult
from repositories.job_posting_knowledge_repository import JobPostingKnowledgeChunkRepository
from repositories.job_posting_experiment_repository import (
    JobPostingExperimentCaseResultRepository,
    JobPostingExperimentRunRepository,
)
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
    JobPostingExperimentRunCreateRequest,
    JobPostingExperimentCaseResultResponse,
    JobPostingExperimentRunDetailResponse,
    JobPostingExperimentRunListResponse,
    JobPostingExperimentRunResponse,
    JobPostingCreateRequest,
    JobPostingListResponse,
    JobPostingResponse,
    JobPostingAnalysisReportResponse,
)
from models.job_posting_experiment_run import (
    JobPostingExperimentRun,
    JobPostingExperimentStatus,
)


PIPELINE_VERSION = "job-posting-compliance-rag-v1"
ANALYSIS_VERSION = "2026-05-12"
MODEL_NAME = "rule-rag-baseline"
JOB_POSTING_UPLOAD_DIR = "job_postings"
logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], Awaitable[None]]


class JobPostingAnalysisCancelled(Exception):
    """Raised when a running job posting analysis job is cancelled."""


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
        pattern=re.compile(
            r"(여성|남성|남자|여자|남직원|여직원|군필\s*남성|군필자|병역필자)"
            r"\s*(지원자|개발자|엔지니어|인재|인력|직원|경력자|비서|멤버)?"
            r"\s*(?:를|을|는|은|만|에\s*한해)?\s*"
            r"(우대|선호|한정|지원\s*가능|환영|우선\s*검토|채용|모집)"
        ),
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
        """AI 작업 엔티티를 채용공고 작업 응답 DTO로 변환한다."""
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
    async def create_experiment_run(
        *,
        db: AsyncSession,
        request: JobPostingExperimentRunCreateRequest,
        actor_id: int | None,
    ) -> JobPostingExperimentRunResponse:
        repo = JobPostingExperimentRunRepository(db)
        total_cases = 0
        try:
            total_cases = len(load_experiment_dataset(request.dataset_name))
        except Exception:
            total_cases = 0
        entity = JobPostingExperimentRun(
            title=request.title,
            description=request.description,
            dataset_name=request.dataset_name,
            dataset_version=request.dataset_version,
            experiment_type=request.experiment_type,
            status=JobPostingExperimentStatus.QUEUED.value,
            total_cases=total_cases,
            config_snapshot=request.config_snapshot,
            requested_by=actor_id,
            created_by=actor_id,
        )
        await repo.add(entity)
        await db.commit()
        await repo.refresh(entity)
        return JobPostingExperimentRunResponse.from_entity(entity)

    @staticmethod
    async def list_experiment_runs(
        *,
        db: AsyncSession,
        page: int,
        size: int,
    ) -> JobPostingExperimentRunListResponse:
        repo = JobPostingExperimentRunRepository(db)
        total_count = await repo.count_list()
        rows = await repo.find_list(page=page, size=size)
        total_pages = math.ceil(total_count / size) if total_count else 0
        return JobPostingExperimentRunListResponse(
            items=[JobPostingExperimentRunResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_experiment_run(
        *,
        db: AsyncSession,
        run_id: int,
        case_limit: int = 200,
    ) -> JobPostingExperimentRunDetailResponse:
        run_repo = JobPostingExperimentRunRepository(db)
        case_repo = JobPostingExperimentCaseResultRepository(db)
        entity = await run_repo.find_by_id_not_deleted(run_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting experiment run was not found.",
            )
        case_rows = await case_repo.find_by_run_id(run_id, limit=case_limit)
        return JobPostingExperimentRunDetailResponse(
            run=JobPostingExperimentRunResponse.from_entity(entity),
            case_results=[
                JobPostingExperimentCaseResultResponse.from_entity(row)
                for row in case_rows
            ],
        )

    @staticmethod
    async def submit_experiment_run_job(
        *,
        db: AsyncSession,
        run_id: int,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        run_repo = JobPostingExperimentRunRepository(db)
        run = await run_repo.find_by_id_not_deleted(run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting experiment run was not found.",
            )
        if run.ai_job_id is not None or run.completed_cases > 0 or run.failed_cases > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Experiment run was already started. Create a new run for another attempt.",
            )
        job = AiJob(
            job_type=AiJobType.JOB_POSTING_EXPERIMENT_RUN.value,
            status=AiJobStatus.QUEUED.value,
            target_id=run.id,
            progress=2,
            current_step="experiment_job_created",
            request_payload={
                "mode": "DATASET",
                "experiment_run_id": run.id,
                "dataset_name": run.dataset_name,
            },
            requested_by=actor_id,
            created_by=actor_id,
        )
        db.add(job)
        await db.flush()
        run.ai_job_id = job.id
        run.status = JobPostingExperimentStatus.QUEUED.value
        await db.commit()
        await db.refresh(job)
        await run_repo.refresh(run)
        return JobPostingService._job_response(
            job,
            "채용공고 실험 배치 작업이 시작되었습니다.",
        )

    @staticmethod
    async def get_experiment_job(
        *,
        db: AsyncSession,
        job_id: int,
    ) -> JobPostingAiJobResponse:
        result = await db.execute(
            select(AiJob).where(
                AiJob.id == job_id,
                AiJob.job_type == AiJobType.JOB_POSTING_EXPERIMENT_RUN.value,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting experiment job was not found.",
            )
        return JobPostingService._job_response(job, "채용공고 실험 작업 상태입니다.")

    @staticmethod
    async def get_active_experiment_job(
        *,
        db: AsyncSession,
        actor_id: int | None,
        run_id: int | None = None,
    ) -> JobPostingAiJobResponse | None:
        conditions = [
            AiJob.job_type == AiJobType.JOB_POSTING_EXPERIMENT_RUN.value,
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
        if run_id is not None:
            conditions.append(AiJob.target_id == run_id)
        result = await db.execute(
            select(AiJob)
            .where(*conditions)
            .order_by(desc(AiJob.created_at), desc(AiJob.id))
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None
        return JobPostingService._job_response(job, "채용공고 실험 작업 상태입니다.")

    @staticmethod
    async def create_posting(
        *,
        db: AsyncSession,
        request: JobPostingCreateRequest,
        actor_id: int | None,
    ) -> JobPostingResponse:
        """채용공고를 신규 등록하거나 기존 공고를 갱신한다."""
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
        """업로드된 파일에서 텍스트를 추출한 뒤 채용공고 분석을 수행한다."""
        extracted = await asyncio.to_thread(
            extract_text_from_file,
            file_path,
            file_ext,
        )
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
    async def cancel_analysis_job(
        *,
        db: AsyncSession,
        job_id: int,
        actor_id: int | None,
    ) -> JobPostingAiJobResponse:
        result = await db.execute(
            select(AiJob).where(
                AiJob.id == job_id,
                AiJob.job_type == AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
            )
        )
        job = result.scalar_one_or_none()
        if job is None or (actor_id is not None and job.requested_by != actor_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting analysis job was not found.",
            )

        if job.status not in {
            AiJobStatus.SUCCESS.value,
            AiJobStatus.PARTIAL_SUCCESS.value,
            AiJobStatus.FAILED.value,
            AiJobStatus.CANCELLED.value,
        }:
            job.status = AiJobStatus.CANCELLED.value
            job.current_step = "analysis_cancelled"
            job.error_message = "사용자가 채용공고 분석 작업을 취소했습니다."
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(job)

        return JobPostingService._job_response(
            job,
            "채용공고 점검 작업이 취소되었습니다.",
        )

    @staticmethod
    async def get_active_analysis_job(
        *,
        db: AsyncSession,
        actor_id: int | None,
        posting_id: int | None = None,
    ) -> JobPostingAiJobResponse | None:
        conditions = [
            AiJob.job_type == AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
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
        if posting_id is not None:
            conditions.append(AiJob.target_id == posting_id)

        result = await db.execute(
            select(AiJob)
            .where(*conditions)
            .order_by(desc(AiJob.created_at), desc(AiJob.id))
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None
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
                if job.status == AiJobStatus.CANCELLED.value:
                    return
                job.status = AiJobStatus.RUNNING.value
                job.progress = 10
                job.current_step = "analysis_started"
                job.started_at = job.started_at or datetime.now(timezone.utc)
                await db.commit()

                async def update_progress(progress: int, current_step: str) -> None:
                    await db.refresh(job)
                    if job.status == AiJobStatus.CANCELLED.value:
                        raise JobPostingAnalysisCancelled()
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
                    extracted = await asyncio.to_thread(
                        extract_text_from_file,
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

                await db.refresh(job)
                if job.status == AiJobStatus.CANCELLED.value:
                    return
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
            except JobPostingAnalysisCancelled:
                await db.rollback()
                result = await db.execute(select(AiJob).where(AiJob.id == job_id))
                cancelled_job = result.scalar_one_or_none()
                if cancelled_job is not None:
                    cancelled_job.status = AiJobStatus.CANCELLED.value
                    cancelled_job.current_step = "analysis_cancelled"
                    cancelled_job.error_message = (
                        cancelled_job.error_message
                        or "사용자가 채용공고 분석 작업을 취소했습니다."
                    )
                    cancelled_job.completed_at = (
                        cancelled_job.completed_at or datetime.now(timezone.utc)
                    )
                    await db.commit()
            except Exception as exc:
                logger.exception("Job posting analysis job failed. job_id=%s", job_id)
                await db.rollback()
                result = await db.execute(select(AiJob).where(AiJob.id == job_id))
                failed_job = result.scalar_one_or_none()
                if failed_job is not None:
                    if failed_job.status == AiJobStatus.CANCELLED.value:
                        failed_job.current_step = "analysis_cancelled"
                        failed_job.completed_at = (
                            failed_job.completed_at or datetime.now(timezone.utc)
                        )
                        await db.commit()
                        return
                    failed_job.status = AiJobStatus.FAILED.value
                    failed_job.progress = 100
                    failed_job.current_step = "analysis_failed"
                    failed_job.error_message = str(exc)
                    failed_job.completed_at = datetime.now(timezone.utc)
                    await db.commit()

    @staticmethod
    async def run_experiment_job(job_id: int) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AiJob).where(AiJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                logger.warning("Job posting experiment job not found: %s", job_id)
                return

            payload = job.request_payload or {}
            run_id = int(payload.get("experiment_run_id") or 0)
            run_repo = JobPostingExperimentRunRepository(db)
            case_repo = JobPostingExperimentCaseResultRepository(db)
            run = await run_repo.find_by_id_not_deleted(run_id)
            if run is None:
                job.status = AiJobStatus.FAILED.value
                job.error_message = "Experiment run was not found."
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return

            try:
                job.status = AiJobStatus.RUNNING.value
                job.progress = 8
                job.current_step = "experiment_started"
                job.started_at = job.started_at or datetime.now(timezone.utc)
                run.status = JobPostingExperimentStatus.RUNNING.value
                run.started_at = run.started_at or datetime.now(timezone.utc)
                await db.commit()

                dataset_cases = load_experiment_dataset(run.dataset_name)
                run.total_cases = len(dataset_cases)
                await db.commit()

                case_results: list[JobPostingExperimentCaseResult] = []
                for index, case in enumerate(dataset_cases, start=1):
                    job.current_step = f"running_case_{index}_of_{len(dataset_cases)}"
                    job.progress = min(
                        95,
                        10 + int((index - 1) / max(len(dataset_cases), 1) * 80),
                    )
                    await db.commit()

                    case_row = JobPostingExperimentCaseResult(
                        experiment_run_id=run.id,
                        case_id=case["case_id"],
                        case_index=index,
                        job_group=case.get("job_group"),
                        status="RUNNING",
                        expected_label=case.get("expected_label"),
                        expected_risk_types=case.get("risk_types") or [],
                        created_by=job.requested_by,
                    )
                    await case_repo.add(case_row)
                    await db.commit()
                    await case_repo.refresh(case_row)

                    started_at = time.perf_counter()
                    try:
                        request = build_experiment_case_request(case)
                        response = await JobPostingService.analyze_text(
                            db=db,
                            request=request,
                            actor_id=job.requested_by,
                        )
                        latency_ms = (time.perf_counter() - started_at) * 1000
                        evaluation = evaluate_experiment_case(
                            case=case,
                            report=response.report,
                            latency_ms=latency_ms,
                        )
                        case_row.status = "SUCCESS"
                        case_row.predicted_label = evaluation["predicted_label"]
                        case_row.predicted_risk_types = evaluation["predicted_risk_types"]
                        case_row.retrieval_hit_at_5 = evaluation["retrieval_hit_at_5"]
                        case_row.source_omitted = evaluation["source_omitted"]
                        case_row.latency_ms = evaluation["latency_ms"]
                        case_row.evaluation_payload = evaluation
                        case_row.report_payload = {
                            "job_posting_id": response.job_posting.id,
                            "report_id": response.report.id,
                            "risk_level": response.report.risk_level,
                            "detected_issue_types": response.report.detected_issue_types,
                            "retrieval_summary": response.report.retrieval_summary,
                        }
                    except Exception as exc:
                        latency_ms = (time.perf_counter() - started_at) * 1000
                        logger.exception(
                            "Experiment case failed. run_id=%s case_id=%s",
                            run.id,
                            case["case_id"],
                        )
                        case_row.status = "FAILED"
                        case_row.error_message = str(exc)
                        case_row.latency_ms = round(latency_ms, 2)
                        case_row.evaluation_payload = {
                            "case_id": case["case_id"],
                            "latency_ms": round(latency_ms, 2),
                            "failure_reason": str(exc),
                        }

                    await db.commit()
                    await case_repo.refresh(case_row)
                    case_results.append(case_row)
                    run.completed_cases = len(
                        [item for item in case_results if item.status == "SUCCESS"]
                    )
                    run.failed_cases = len(
                        [item for item in case_results if item.status == "FAILED"]
                    )
                    await db.commit()

                summary = summarize_experiment_results(case_results)
                run.retrieval_recall_at_5 = summary["retrieval_recall_at_5"]
                run.macro_f1 = summary["macro_f1"]
                run.high_risk_recall = summary["high_risk_recall"]
                run.source_omission_rate = summary["source_omission_rate"]
                run.avg_latency_ms = summary["avg_latency_ms"]
                run.summary_metrics = summary
                run.result_summary = {
                    "total_cases": run.total_cases,
                    "completed_cases": run.completed_cases,
                    "failed_cases": run.failed_cases,
                    "label_accuracy": summary["label_accuracy"],
                }
                run.status = (
                    JobPostingExperimentStatus.SUCCESS.value
                    if run.completed_cases > 0
                    else JobPostingExperimentStatus.FAILED.value
                )
                run.completed_at = datetime.now(timezone.utc)

                job.status = (
                    AiJobStatus.SUCCESS.value
                    if run.failed_cases == 0
                    else AiJobStatus.PARTIAL_SUCCESS.value
                )
                job.progress = 100
                job.current_step = "experiment_completed"
                job.completed_at = datetime.now(timezone.utc)
                job.result_payload = {
                    "experiment_run_id": run.id,
                    "summary_metrics": summary,
                }
                await db.commit()
            except Exception as exc:
                logger.exception("Job posting experiment job failed. run_id=%s", run.id)
                await db.rollback()
                result = await db.execute(select(AiJob).where(AiJob.id == job_id))
                failed_job = result.scalar_one_or_none()
                failed_run = await run_repo.find_by_id_not_deleted(run.id)
                if failed_run is not None:
                    failed_run.status = JobPostingExperimentStatus.FAILED.value
                    failed_run.completed_at = datetime.now(timezone.utc)
                if failed_job is not None:
                    failed_job.status = AiJobStatus.FAILED.value
                    failed_job.progress = 100
                    failed_job.current_step = "experiment_failed"
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
    """채용공고 1건의 분석 파이프라인을 실행한다.

    룰 기반 위험 표현 탐지와 RAG 근거 검색을 한 흐름으로 묶는다.
    각 단계의 결과는 보고서와 추적 로그에 함께 남겨 이후 실험 비교에 쓴다.
    """
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
        logger.info(
            "Job posting risk detection started. posting_id=%s report_id=%s text_length=%s",
            posting.id,
            report.id,
            len(posting.posting_text or ""),
        )
        issues = detect_issues(posting.posting_text)
        logger.info(
            "Job posting risk detection completed. posting_id=%s report_id=%s issue_count=%s issues=%s",
            posting.id,
            report.id,
            len(issues),
            [
                {
                    "issue_type": issue.get("issue_type"),
                    "severity": issue.get("severity"),
                    "flagged_text": issue.get("flagged_text"),
                }
                for issue in issues
            ],
        )
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

        # 이슈별 근거를 분리해 붙여야 최종 리포트에서 어떤 문제를 왜 판단했는지 설명할 수 있다.
        retrieval_service = JobPostingRetrievalService(db)
        evidence_items: list[dict[str, Any]] = []
        total_issues = max(len(issues), 1)
        for issue_index, issue in enumerate(issues):
            logger.info(
                "Job posting evidence retrieval started. posting_id=%s report_id=%s issue_index=%s/%s issue_type=%s flagged_text=%s query_terms=%s",
                posting.id,
                report.id,
                issue_index + 1,
                len(issues),
                issue.get("issue_type"),
                issue.get("flagged_text"),
                issue.get("query_terms"),
            )
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
            retrieval_trace = retrieval_service.last_trace
            evidence_payloads = [evidence.to_payload() for evidence in evidences]
            logger.info(
                "Job posting evidence retrieval completed. posting_id=%s report_id=%s issue_type=%s flagged_text=%s evidence_count=%s top_evidence=%s",
                posting.id,
                report.id,
                issue.get("issue_type"),
                issue.get("flagged_text"),
                len(evidence_payloads),
                [
                    {
                        "chunk_id": evidence.get("chunk_id"),
                        "source_id": evidence.get("source_id"),
                        "title": evidence.get("title"),
                        "law_name": evidence.get("law_name"),
                        "article_no": evidence.get("article_no"),
                        "hybrid_score": evidence.get("hybrid_score"),
                        "rerank_score": evidence.get("rerank_score"),
                    }
                    for evidence in evidence_payloads[:3]
                ],
            )
            await trace.record(
                node_name="bm25_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "query_terms": issue["query_terms"],
                    "mode": retrieval_trace.get("bm25_mode"),
                    "timeout_seconds": retrieval_trace.get("bm25_timeout_seconds"),
                },
                output_json={
                    "used": retrieval_trace.get("bm25_used"),
                    "timeout": retrieval_trace.get("bm25_timeout"),
                    "candidate_count": retrieval_trace.get("bm25_count"),
                },
                elapsed_ms=int(retrieval_trace.get("bm25_elapsed_ms") or 0),
            )
            await trace.record(
                node_name="metadata_exact_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "query_terms": issue["query_terms"],
                },
                output_json={
                    "candidate_count": retrieval_trace.get("metadata_count"),
                },
                elapsed_ms=int(retrieval_trace.get("metadata_elapsed_ms") or 0),
            )
            await trace.record(
                node_name="hybrid_lite_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "retrieval_mode": "metadata_vector_bm25_fallback",
                },
                output_json={
                    "candidate_count": len(evidence_payloads),
                    "top_candidates": evidence_payloads[:5],
                    "trace": retrieval_trace,
                },
                elapsed_ms=int((time.perf_counter() - node_started_at) * 1000),
            )
            await trace.record(
                node_name="vector_retrieve",
                request_json={
                    "issue_type": issue["issue_type"],
                    "embedding_model": current_embedding_model_name(),
                },
                output_json={
                    "candidate_count": retrieval_trace.get("vector_count"),
                    "top_vector_scores": [
                        item.get("vector_score") for item in evidence_payloads[:5]
                    ],
                },
                elapsed_ms=int(retrieval_trace.get("vector_elapsed_ms") or 0),
            )
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
                elapsed_ms=int(retrieval_trace.get("merge_elapsed_ms") or 0),
            )
            issue["sources"] = evidence_payloads[:5]
            evidence_items.extend(evidence_payloads[:5])

        if progress_callback is not None:
            await progress_callback(82, "checking_evidence_sufficiency")
        node_started_at = time.perf_counter()
        sufficiency = build_evidence_sufficiency(issues=issues)
        logger.info(
            "Job posting evidence sufficiency checked. posting_id=%s report_id=%s sufficiency=%s",
            posting.id,
            report.id,
            sufficiency,
        )
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
        # 최종 위험도는 탐지 개수보다 issue의 성격과 법적 리스크를 더 중요하게 본다.
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
        logger.info(
            "Job posting structured report generated. posting_id=%s report_id=%s risk_level=%s issue_count=%s evidence_count=%s evidence_strength=%s",
            posting.id,
            report.id,
            risk_level,
            len(issues),
            len(reranked_evidence_items),
            evidence_strength,
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
            if risk_pattern.issue_type == "SALARY_MISSING" and has_explicit_salary_range(
                posting_text
            ):
                logger.debug(
                    "Salary-missing match skipped due to explicit salary range. flagged_text=%s",
                    flagged,
                )
                continue
            if (
                risk_pattern.issue_type == "WORKING_CONDITION_AMBIGUITY"
                and len(flagged) > 120
            ):
                logger.debug(
                    "Working-condition ambiguity match skipped due to overly long span. flagged_text=%s",
                    flagged,
                )
                continue
            key = (risk_pattern.issue_type, flagged)
            if key in seen:
                logger.debug(
                    "Duplicate job posting risk match skipped. issue_type=%s flagged_text=%s",
                    risk_pattern.issue_type,
                    flagged,
                )
                continue
            seen.add(key)
            logger.info(
                "Job posting risk phrase matched. issue_type=%s severity=%s flagged_text=%s query_terms=%s",
                risk_pattern.issue_type,
                risk_pattern.severity,
                flagged,
                risk_pattern.query_terms,
            )
            issues.append(
                {
                    **build_issue_payload(
                        issue_type=risk_pattern.issue_type,
                        severity=risk_pattern.severity,
                        flagged_text=flagged,
                        why_risky=risk_pattern.reason,
                        recommended_revision=risk_pattern.replacement,
                        query_terms=risk_pattern.query_terms,
                    )
                }
            )
    issues.extend(detect_additional_issues(posting_text=posting_text, seen=seen))
    return issues


def build_issue_payload(
    *,
    issue_type: str,
    severity: str,
    flagged_text: str,
    why_risky: str,
    recommended_revision: str,
    query_terms: list[str],
) -> dict[str, Any]:
    return {
        "issue_type": issue_type,
        "severity": severity,
        "category": (
            "LEGAL"
            if issue_type
            in {
                "FALSE_JOB_AD",
                "UNFAVORABLE_CONDITION_CHANGE",
                "GENDER_DISCRIMINATION",
                "AGE_DISCRIMINATION",
                "PHYSICAL_CONDITION",
                "IRRELEVANT_PERSONAL_INFO",
                "WORKING_CONDITION_AMBIGUITY",
                "OVERTIME_RISK",
            }
            else "BRANDING"
        ),
        "flagged_text": flagged_text,
        "why_risky": why_risky,
        "recommended_revision": recommended_revision,
        "confidence": confidence_by_severity(severity),
        "query_terms": query_terms,
        "sources": [],
    }


def detect_additional_issues(
    *, posting_text: str, seen: set[tuple[str, str]]
) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    extra_rules: list[tuple[str, str, str, str, list[str], re.Pattern[str]]] = [
        (
            "OVERTIME_RISK",
            "HIGH",
            "연장근로·야간근무 가능만 강조하고 보상 기준이 불명확한 표현입니다.",
            "연장·야간·온콜 발생 조건과 수당/대체휴무 기준을 함께 명시합니다.",
            ["연장근로", "야근", "온콜", "수당", "대체휴무"],
            re.compile(
                r"(야근\s*가능|야간\s*온콜|온콜\s*참여|연장근로|늦은\s*시간까지|교대\s*기준은\s*합류\s*후|수당.*팀\s*상황|대체휴무.*팀\s*상황|긴급\s*배포.*대응|출장이\s*수시로\s*발생)"
            ),
        ),
        (
            "AGE_DISCRIMINATION",
            "HIGH",
            "특정 연령대/연차 구간만 선호하거나 제한하는 표현입니다.",
            "연령과 무관하게 직무 역량·성과 기준으로 평가합니다.",
            ["연령", "차별", "경력제한", "나이"],
            re.compile(
                r"(경력은\s*\d+\s*년\s*이상\s*\d+\s*년\s*이하\s*인\s*분만\s*검토|젊은\s*스타트업\s*문화|젊고\s*활동적인|젊고\s*빠른\s*조직|지원\s*가능\s*연령은\s*만\s*\d+\s*세부터\s*만\s*\d+\s*세까지)"
            ),
        ),
        (
            "FALSE_JOB_AD",
            "CRITICAL",
            "공고상 조건과 실제 근로조건이 다를 수 있음을 시사하는 표현입니다.",
            "정규직/계약직/평가조건/기본급·인센티브 기준을 공고에 동일하게 명시합니다.",
            ["근로조건", "정규직", "계약직", "기본급", "전환조건"],
            re.compile(
                r"(실제\s*기본급은|입사\s*후\s*별도\s*안내|프로젝트\s*계약\s*평가\s*통과.*정규직\s*전환|개인사업자\s*위촉계약|고용조건을\s*다시\s*협의|포지션명은.*이나.*초기\s*\d+\s*년은.*대부분|제출물의\s*사용권과\s*저작권은\s*회사에\s*귀속|제출한\s*산출물은\s*반환하지\s*않고)"
            ),
        ),
        (
            "UNFAVORABLE_CONDITION_CHANGE",
            "HIGH",
            "공고 조건 대비 입사 후 불리한 계약 변경 가능성이 있는 표현입니다.",
            "입사 전 제시한 고용형태·근로조건을 동일하게 적용하고 변경 가능 조건을 사전 고지합니다.",
            ["고용형태", "정규직", "프리랜서", "계약변경"],
            re.compile(
                r"(정규직으로\s*안내하지만\s*입사\s*후\s*\d+\s*개월은\s*프리랜서\s*계약|정규직\s*영업\s*담당자로\s*모집하지만,\s*입사\s*시\s*개인사업자\s*위촉계약)"
            ),
        ),
        (
            "WORKING_CONDITION_AMBIGUITY",
            "HIGH",
            "성과급·보상 기준이 경영 상황에 따라 달라져 예측 가능성이 낮은 표현입니다.",
            "성과급 지급률, 평가 기준, 확정/변동 항목을 공고에 구체적으로 명시합니다.",
            ["성과급", "지급률", "평가기준", "별도결정"],
            re.compile(
                r"(성과급\s*지급률.*별도\s*결정|인센티브는\s*팀\s*목표\s*초과\s*달성\s*시에만\s*검토|포괄임금제를\s*적용하며.*연장근로\s*수당은\s*연봉에\s*포함|구체적인\s*산정\s*기준은\s*입사\s*후\s*안내)"
            ),
        ),
        (
            "SALARY_MISSING",
            "MEDIUM",
            "최대 연봉만 강조되고 실제 기본급 범위가 불명확한 표현입니다.",
            "최대 보상과 별개로 기본급 범위와 성과급 산정 방식을 함께 안내합니다.",
            ["연봉", "기본급", "성과급", "보상구조"],
            re.compile(
                r"(연봉\s*최대\s*\d[\d,]*\s*만?\s*원\s*가능.*실제\s*기본급\s*범위는\s*입사\s*후\s*별도\s*안내)"
            ),
        ),
        (
            "CULTURE_RED_FLAG",
            "MEDIUM",
            "과도한 적합성/성과 중심 문화를 강조해 업무 강도 리스크가 있는 표현입니다.",
            "조직문화 표현 대신 업무 방식, 의사결정, 성과 지원 체계를 구체적으로 안내합니다.",
            ["조직문화", "성과압박", "적합성", "장기근속"],
            re.compile(
                r"(장기근속이\s*가능한\s*안정적인\s*생활\s*패턴의\s*분을\s*선호|강한\s*성과\s*중심\s*문화를\s*운영)"
            ),
        ),
        (
            "BENEFIT_VAGUE",
            "LOW",
            "경험 기회를 포괄적으로 제시하지만 실제 참여 범위가 불명확한 표현입니다.",
            "경험 가능한 기술 스택과 실제 담당 비중을 구체적으로 명시합니다.",
            ["경험기회", "기술스택", "참여비중"],
            re.compile(
                r"(최신\s*LLM,\s*MLOps,\s*검색\s*시스템을\s*모두\s*경험할\s*수\s*있다고\s*소개하지만\s*실제\s*담당\s*범위와\s*기술별\s*참여\s*비중은\s*프로젝트\s*상황에\s*따라\s*달라집니다)"
            ),
        ),
        (
            "REPEATED_POSTING",
            "LOW",
            "동일 포지션의 반복 게시를 시사하는 표현입니다.",
            "반복 게시 사유와 충원 계획을 명확하게 안내합니다.",
            ["반복게시", "상시채용", "동일포지션"],
            re.compile(r"(동일\s*포지션을\s*상시로\s*다시\s*게시|상시로\s*반복\s*게시되는\s*포지션)"),
        ),
        (
            "IRRELEVANT_PERSONAL_INFO",
            "HIGH",
            "직무 역량과 무관한 과도한 전형 과제/원본 제출 요구 표현입니다.",
            "전형 과제는 최소 범위로 제한하고, 원본 산출물 귀속/활용 조건을 명확히 고지합니다.",
            ["전형과제", "원본제출", "과도요구"],
            re.compile(
                r"(전형\s*과제로.*기획안\s*전체를\s*제출해야|광고\s*소재\s*원본을\s*제출해야)"
            ),
        ),
        (
            "PHYSICAL_CONDITION",
            "HIGH",
            "신체적 부담을 전제한 선호 표현으로 해석될 수 있습니다.",
            "직무상 이동/현장 요구사항은 객관적 업무 조건 중심으로 명시합니다.",
            ["신체조건", "체력", "이동", "현장"],
            re.compile(r"(장거리\s*이동과\s*현장\s*미팅을\s*부담\s*없이\s*소화)"),
        ),
        (
            "JOB_DESCRIPTION_VAGUE",
            "MEDIUM",
            "공고 직무명과 실제 수행 업무 간 괴리가 있는 표현입니다.",
            "핵심 업무 비중과 초기 담당 업무를 공고에 구체적으로 표시합니다.",
            ["직무범위", "업무비중", "직무명"],
            re.compile(r"(포지션명은.*이나.*초기\s*\d+\s*년은.*대부분)"),
        ),
    ]
    for issue_type, severity, why_risky, recommended_revision, query_terms, pattern in extra_rules:
        for match in pattern.finditer(posting_text):
            flagged = normalize_flagged_text(match.group(0))
            key = (issue_type, flagged)
            if key in seen:
                continue
            seen.add(key)
            extra.append(
                build_issue_payload(
                    issue_type=issue_type,
                    severity=severity,
                    flagged_text=flagged,
                    why_risky=why_risky,
                    recommended_revision=recommended_revision,
                    query_terms=query_terms,
                )
            )
    return extra


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
    return calculate_risk_level_from_issues(issues)


def calculate_risk_level_with_evidence(issues: list[dict[str, Any]]) -> str:
    """탐지 결과를 최종 위험도로 변환한다.

    실제 계산은 `calculate_risk_level_from_issues`로 위임한다.
    호출부에서는 이 함수를 통해 위험도 산정 규칙을 한 이름으로 사용한다.
    """
    return calculate_risk_level_from_issues(issues)


def calculate_risk_level_from_issues(issues: list[dict[str, Any]]) -> str:
    """issue 목록을 법적 리스크 기준으로 위험도 단계에 매핑한다.

    직접 법 위반 가능성이 큰 유형은 HIGH 축으로 올린다.
    허위공고와 특정 파트너 이슈가 함께 나오면 CRITICAL로 본다.
    표현상 비권장이나 모호성 위주의 이슈는 MEDIUM 또는 LOW에 머무르게 한다.
    """
    if not issues:
        return "CLEAN"

    severe_direct_issue_types = {
        "FALSE_JOB_AD",
        "UNFAVORABLE_CONDITION_CHANGE",
        "GENDER_DISCRIMINATION",
        "AGE_DISCRIMINATION",
        "PHYSICAL_CONDITION",
        "IRRELEVANT_PERSONAL_INFO",
    }
    medium_issue_types = {
        "WORKING_CONDITION_AMBIGUITY",
        "OVERTIME_RISK",
        "JOB_DESCRIPTION_VAGUE",
        "SALARY_MISSING",
        "CULTURE_RED_FLAG",
    }
    low_issue_types = {
        "BENEFIT_VAGUE",
        "REPEATED_POSTING",
    }

    # 입력 구조가 달라도 위험도 계산에 필요한 핵심 값만 정규화해서 사용한다.
    normalized = [
        {
            "issue_type": issue.get("issue_type"),
            "severity": issue.get("severity") or "LOW",
        }
        for issue in issues
        if issue.get("issue_type")
    ]
    issue_types = [item["issue_type"] for item in normalized if item["issue_type"]]

    false_job_ad_present = "FALSE_JOB_AD" in issue_types
    critical_partner_issue_types = {
        "UNFAVORABLE_CONDITION_CHANGE",
        "WORKING_CONDITION_AMBIGUITY",
        "IRRELEVANT_PERSONAL_INFO",
        "SALARY_MISSING",
    }
    if false_job_ad_present and any(
        issue_type in critical_partner_issue_types for issue_type in issue_types
    ):
        return "CRITICAL"

    if any(issue_type in severe_direct_issue_types for issue_type in issue_types):
        return "HIGH"

    medium_high_count = sum(
        1
        for item in normalized
        if item["issue_type"] in medium_issue_types
        and item["severity"] in {"HIGH", "CRITICAL"}
    )
    if medium_high_count >= 2:
        return "HIGH"
    if any(item["issue_type"] in medium_issue_types for item in normalized):
        return "MEDIUM"

    low_count = sum(1 for issue_type in issue_types if issue_type in low_issue_types)
    if low_count >= 2:
        return "MEDIUM"
    if low_count >= 1:
        return "LOW"
    return "LOW"


def calculate_risk_level_from_issue_types(issue_types: list[str]) -> str:
    default_severity = {
        "FALSE_JOB_AD": "HIGH",
        "UNFAVORABLE_CONDITION_CHANGE": "HIGH",
        "GENDER_DISCRIMINATION": "HIGH",
        "AGE_DISCRIMINATION": "HIGH",
        "PHYSICAL_CONDITION": "HIGH",
        "IRRELEVANT_PERSONAL_INFO": "HIGH",
        "WORKING_CONDITION_AMBIGUITY": "HIGH",
        "OVERTIME_RISK": "MEDIUM",
        "JOB_DESCRIPTION_VAGUE": "MEDIUM",
        "SALARY_MISSING": "MEDIUM",
        "CULTURE_RED_FLAG": "MEDIUM",
        "BENEFIT_VAGUE": "LOW",
        "REPEATED_POSTING": "LOW",
    }
    return calculate_risk_level_from_issues(
        [
            {"issue_type": issue_type, "severity": default_severity.get(issue_type, "LOW")}
            for issue_type in issue_types
            if issue_type
        ]
    )


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


def has_explicit_salary_range(text: str) -> bool:
    normalized = normalize_flagged_text(text)
    has_amount = bool(re.search(r"\d[\d,]*\s*(만\s*)?원", normalized))
    has_range = bool(
        re.search(
            r"(~|-|부터\s*\d[\d,]*\s*(만\s*)?원\s*까지)",
            normalized,
        )
    )
    return has_amount and has_range


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


def load_experiment_dataset(dataset_name: str) -> list[dict[str, Any]]:
    """실험용 데이터셋 폴더를 읽어 케이스 목록으로 반환한다.

    `meta.json`의 정답 정보와 `source.json`의 원문 정보를 합쳐
    실험 실행기가 바로 돌릴 수 있는 형태로 정리한다.
    """
    dataset_root = Path(__file__).resolve().parent.parent / "sample_data" / "source_data" / dataset_name
    if not dataset_root.exists():
        raise ValueError(f"Experiment dataset was not found: {dataset_name}")

    cases: list[dict[str, Any]] = []
    for meta_path in sorted(dataset_root.rglob("meta.json")):
        source_path = meta_path.with_name("source.json")
        if not source_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        source = json.loads(source_path.read_text(encoding="utf-8"))
        cases.append(
            {
                "case_id": meta.get("case_id") or source.get("case_id") or meta_path.parent.name,
                "job_group": source.get("job_group") or meta_path.parent.parent.name,
                "expected_label": meta.get("expected_label") or "VIOLATION",
                "expected_risk_level": meta.get("risk_level") or "UNKNOWN",
                "risk_types": meta.get("risk_types") or [],
                "expected_findings": meta.get("expected_findings") or [],
                "source": source,
                "meta": meta,
            }
        )
    return cases


def build_experiment_case_request(case: dict[str, Any]) -> JobPostingAnalyzeTextRequest:
    """실험 케이스를 실제 분석 요청 DTO로 변환한다."""
    source = case["source"]
    return JobPostingAnalyzeTextRequest(
        company_name=source.get("company_name"),
        job_title=source.get("job_title") or source.get("posting_title") or case["case_id"],
        target_job=source.get("job_group"),
        career_level=source.get("career_level"),
        location=source.get("location"),
        employment_type=source.get("employment_type"),
        salary_text=source.get("salary"),
        posting_text=source.get("posting_body") or "",
        input_source=JobPostingInputSource.SYNTHETIC.value,
        raw_payload={
            "experiment_case_id": case["case_id"],
            "dataset_name": "job_posting_risk_50",
            "source_json": source,
        },
        normalized_payload={
            "experiment_case_id": case["case_id"],
            "expected_label": case.get("expected_label"),
            "expected_risk_types": case.get("risk_types") or [],
        },
        analysis_type=JobPostingAnalysisType.FULL.value,
    )


def evaluate_experiment_case(
    *,
    case: dict[str, Any],
    report: JobPostingAnalysisReportResponse,
    latency_ms: float,
) -> dict[str, Any]:
    """케이스 1건의 예측 결과를 정답과 비교한다.

    라벨, 위험 유형, 위험도, 근거 포함 여부를 한 번에 정리한다.
    `retrieval_hit_at_5`는 기대한 위험 유형별로 상위 5개 근거가 붙었는지를 본다.
    """
    expected_risk_types = list(case.get("risk_types") or [])
    predicted_risk_types = sorted(set(report.detected_issue_types or []))
    predicted_label = "CLEAN" if not predicted_risk_types else "VIOLATION"
    issue_summary = list(report.issue_summary or [])
    matched_evidence = list(report.matched_evidence or [])
    matched_top5 = matched_evidence[:5]

    per_expected_hits: dict[str, bool] = {}
    for risk_type in expected_risk_types:
        matching_issue = next(
            (item for item in issue_summary if item.get("issue_type") == risk_type),
            None,
        )
        sources = list((matching_issue or {}).get("sources") or [])
        per_expected_hits[risk_type] = len(sources[:5]) > 0

    # 정답 위험 유형이 있으면 각 유형마다 근거가 붙었는지 본다.
    # 정답 위험 유형이 없으면 CLEAN 예측 또는 상위 근거 존재를 성공으로 본다.
    retrieval_hit_at_5 = (
        all(per_expected_hits.values()) if expected_risk_types else len(matched_top5) > 0 or predicted_label == "CLEAN"
    )

    source_omitted = False
    predicted_issue_count = len(issue_summary)
    issue_without_sources = 0
    for issue in issue_summary:
        if not list(issue.get("sources") or []):
            issue_without_sources += 1
    if predicted_issue_count > 0 and issue_without_sources > 0:
        source_omitted = True

    return {
        "case_id": case["case_id"],
        "expected_label": case.get("expected_label"),
        "predicted_label": predicted_label,
        "expected_risk_types": expected_risk_types,
        "predicted_risk_types": predicted_risk_types,
        "risk_level": report.risk_level,
        "expected_risk_level": case.get("expected_risk_level"),
        "retrieval_hit_at_5": retrieval_hit_at_5,
        "per_expected_hits": per_expected_hits,
        "source_omitted": source_omitted,
        "issue_without_sources": issue_without_sources,
        "predicted_issue_count": predicted_issue_count,
        "matched_evidence_count": len(matched_evidence),
        "latency_ms": round(latency_ms, 2),
        "report_id": report.id,
    }


def summarize_experiment_results(
    case_results: list[JobPostingExperimentCaseResult],
) -> dict[str, float | int]:
    """케이스별 결과를 실험 요약 지표로 집계한다.

    label_accuracy, retrieval_recall_at_5, macro_f1, high_risk_recall,
    source_omission_rate, avg_latency_ms를 한 번에 계산한다.
    """
    successful = [item for item in case_results if item.status == "SUCCESS"]
    if not successful:
        return {
            "total_cases": len(case_results),
            "successful_cases": 0,
            "failed_cases": len(case_results),
            "label_accuracy": 0.0,
            "retrieval_recall_at_5": 0.0,
            "macro_f1": 0.0,
            "high_risk_recall": 0.0,
            "source_omission_rate": 0.0,
            "avg_latency_ms": 0.0,
        }

    label_pairs = [
        (
            (item.expected_label or "VIOLATION"),
            (item.predicted_label or "VIOLATION"),
        )
        for item in successful
    ]
    # 현재 실험은 이진 라벨 기준이라 CLEAN/VIOLATION 두 축의 F1 평균을 macro_f1로 쓴다.
    labels = ["CLEAN", "VIOLATION"]
    f1_scores = [
        binary_f1_for_label(label_pairs=label_pairs, positive_label=label)
        for label in labels
    ]

    retrieval_hits = [
        1.0 for item in successful if item.retrieval_hit_at_5 is True
    ]
    high_risk_rows = [
        item
        for item in successful
        if (item.evaluation_payload or {}).get("expected_risk_level") in {"HIGH", "CRITICAL"}
    ]
    high_risk_hit_count = sum(
        1
        for item in high_risk_rows
        if (item.evaluation_payload or {}).get("risk_level") in {"HIGH", "CRITICAL"}
    )

    predicted_issue_total = sum(
        int((item.evaluation_payload or {}).get("predicted_issue_count") or 0)
        for item in successful
    )
    omitted_issue_total = sum(
        int((item.evaluation_payload or {}).get("issue_without_sources") or 0)
        for item in successful
    )

    return {
        "total_cases": len(case_results),
        "successful_cases": len(successful),
        "failed_cases": len(case_results) - len(successful),
        "label_accuracy": round(
            sum(1 for expected, predicted in label_pairs if expected == predicted)
            / max(len(label_pairs), 1),
            4,
        ),
        "retrieval_recall_at_5": round(
            len(retrieval_hits) / max(len(successful), 1),
            4,
        ),
        "macro_f1": round(sum(f1_scores) / len(f1_scores), 4),
        "high_risk_recall": round(
            high_risk_hit_count / max(len(high_risk_rows), 1),
            4,
        ),
        "source_omission_rate": round(
            omitted_issue_total / max(predicted_issue_total, 1),
            4,
        ),
        "avg_latency_ms": round(
            sum(float(item.latency_ms or 0.0) for item in successful)
            / max(len(successful), 1),
            2,
        ),
    }


def binary_f1_for_label(
    *,
    label_pairs: list[tuple[str, str]],
    positive_label: str,
) -> float:
    tp = sum(1 for expected, predicted in label_pairs if expected == positive_label and predicted == positive_label)
    fp = sum(1 for expected, predicted in label_pairs if expected != positive_label and predicted == positive_label)
    fn = sum(1 for expected, predicted in label_pairs if expected == positive_label and predicted != positive_label)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)

