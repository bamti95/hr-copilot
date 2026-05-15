from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from models.job_posting import JobPosting
from models.job_posting_analysis_report import JobPostingAnalysisReport
from models.job_posting_experiment_case_result import JobPostingExperimentCaseResult
from models.job_posting_experiment_run import JobPostingExperimentRun
from models.job_posting_knowledge_chunk import JobPostingKnowledgeChunk
from models.job_posting_knowledge_source import JobPostingKnowledgeSource


class JobPostingCreateRequest(BaseModel):
    company_name: str | None = Field(default=None, max_length=255)
    job_title: str = Field(..., min_length=1, max_length=255)
    target_job: str | None = Field(default=None, max_length=100)
    career_level: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    employment_type: str | None = Field(default=None, max_length=100)
    salary_text: str | None = Field(default=None, max_length=255)
    posting_text: str = Field(..., min_length=1)
    input_source: str = "MANUAL"
    source_platform: str | None = None
    external_posting_id: str | None = None
    external_url: str | None = None
    raw_payload: dict[str, Any] | None = None
    normalized_payload: dict[str, Any] | None = None


class JobPostingAnalyzeTextRequest(JobPostingCreateRequest):
    analysis_type: str = "FULL"


class JobPostingResponse(BaseModel):
    id: int
    input_source: str
    source_platform: str | None = None
    external_posting_id: str | None = None
    external_url: str | None = None
    company_name: str | None = None
    job_title: str
    target_job: str | None = None
    career_level: str | None = None
    location: str | None = None
    employment_type: str | None = None
    salary_text: str | None = None
    posting_text: str
    posting_text_hash: str
    raw_payload: dict[str, Any] | None = None
    normalized_payload: dict[str, Any] | None = None
    posting_status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: JobPosting) -> "JobPostingResponse":
        return cls(
            id=entity.id,
            input_source=entity.input_source,
            source_platform=entity.source_platform,
            external_posting_id=entity.external_posting_id,
            external_url=entity.external_url,
            company_name=entity.company_name,
            job_title=entity.job_title,
            target_job=entity.target_job,
            career_level=entity.career_level,
            location=entity.location,
            employment_type=entity.employment_type,
            salary_text=entity.salary_text,
            posting_text=entity.posting_text,
            posting_text_hash=entity.posting_text_hash,
            raw_payload=entity.raw_payload,
            normalized_payload=entity.normalized_payload,
            posting_status=entity.posting_status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class JobPostingListResponse(BaseModel):
    items: list[JobPostingResponse]
    total_count: int
    total_pages: int


class EvidenceSourceResponse(BaseModel):
    chunk_id: int
    source_id: int
    title: str | None = None
    source_type: str | None = None
    chunk_type: str
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    law_name: str | None = None
    article_no: str | None = None
    content: str
    score: float | None = None


class JobPostingAnalysisReportResponse(BaseModel):
    id: int
    job_posting_id: int
    analysis_status: str
    analysis_type: str
    analysis_version: str | None = None
    model_name: str | None = None
    risk_level: str | None = None
    issue_count: int
    violation_count: int
    warning_count: int
    confidence_score: int | None = None
    detected_issue_types: list[Any] | None = None
    retrieval_summary: dict[str, Any] | None = None
    prompt_version: str | None = None
    pipeline_version: str | None = None
    summary_text: str | None = None
    parsed_sections: dict[str, Any] | None = None
    overall_score: int | None = None
    risk_score: int | None = None
    attractiveness_score: int | None = None
    issue_summary: list[Any] | dict[str, Any] | None = None
    matched_evidence: list[Any] | dict[str, Any] | None = None
    compliance_warnings: list[Any] | dict[str, Any] | None = None
    improvement_suggestions: list[Any] | dict[str, Any] | None = None
    rewrite_examples: list[Any] | dict[str, Any] | None = None
    final_report: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(
        cls,
        entity: JobPostingAnalysisReport,
    ) -> "JobPostingAnalysisReportResponse":
        return cls(
            id=entity.id,
            job_posting_id=entity.job_posting_id,
            analysis_status=entity.analysis_status,
            analysis_type=entity.analysis_type,
            analysis_version=entity.analysis_version,
            model_name=entity.model_name,
            risk_level=entity.risk_level,
            issue_count=entity.issue_count,
            violation_count=entity.violation_count,
            warning_count=entity.warning_count,
            confidence_score=entity.confidence_score,
            detected_issue_types=entity.detected_issue_types,
            retrieval_summary=entity.retrieval_summary,
            prompt_version=entity.prompt_version,
            pipeline_version=entity.pipeline_version,
            summary_text=entity.summary_text,
            parsed_sections=entity.parsed_sections,
            overall_score=entity.overall_score,
            risk_score=entity.risk_score,
            attractiveness_score=entity.attractiveness_score,
            issue_summary=entity.issue_summary,
            matched_evidence=entity.matched_evidence,
            compliance_warnings=entity.compliance_warnings,
            improvement_suggestions=entity.improvement_suggestions,
            rewrite_examples=entity.rewrite_examples,
            final_report=entity.final_report,
            error_message=entity.error_message,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class JobPostingAnalyzeResponse(BaseModel):
    job_posting: JobPostingResponse
    report: JobPostingAnalysisReportResponse


class JobPostingAiJobResponse(BaseModel):
    job_id: int
    status: str
    job_type: str
    target_type: str | None = None
    target_id: int | None = None
    progress: int
    current_step: str | None = None
    error_message: str | None = None
    request_payload: dict[str, Any] | None = None
    result_payload: dict[str, Any] | None = None
    message: str


class KnowledgeSourceCreateRequest(BaseModel):
    source_type: str | None = None
    title: str | None = Field(default=None, max_length=255)
    source_name: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=500)
    version_label: str | None = Field(default=None, max_length=50)
    file_path: str
    file_ext: str | None = Field(default=None, max_length=20)
    mime_type: str | None = Field(default=None, max_length=100)
    file_size: int | None = None
    metadata: dict[str, Any] | None = None


class KnowledgeSourceResponse(BaseModel):
    id: int
    source_type: str
    title: str
    source_name: str | None = None
    source_url: str | None = None
    version_label: str | None = None
    file_path: str | None = None
    file_ext: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    extract_status: str
    index_status: str
    chunk_count: int
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: JobPostingKnowledgeSource) -> "KnowledgeSourceResponse":
        return cls(
            id=entity.id,
            source_type=entity.source_type,
            title=entity.title,
            source_name=entity.source_name,
            source_url=entity.source_url,
            version_label=entity.version_label,
            file_path=entity.file_path,
            file_ext=entity.file_ext,
            mime_type=entity.mime_type,
            file_size=entity.file_size,
            extract_status=entity.extract_status,
            index_status=entity.index_status,
            chunk_count=entity.chunk_count,
            metadata=entity.metadata_json,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class KnowledgeSourceListResponse(BaseModel):
    items: list[KnowledgeSourceResponse]
    total_count: int
    total_pages: int


class KnowledgeChunkResponse(BaseModel):
    id: int
    knowledge_source_id: int
    chunk_type: str
    chunk_key: str | None = None
    chunk_index: int
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    content: str
    summary: str | None = None
    issue_code: str | None = None
    risk_category: str | None = None
    severity: str | None = None
    law_name: str | None = None
    article_no: str | None = None
    penalty_guide: str | None = None
    violation_text: str | None = None
    violation_reason: str | None = None
    correction_suggestion: str | None = None
    tags: list[Any] | None = None
    metadata: dict[str, Any] | None = None
    embedding_model: str | None = None
    content_hash: str
    token_count: int | None = None

    @classmethod
    def from_entity(cls, entity: JobPostingKnowledgeChunk) -> "KnowledgeChunkResponse":
        return cls(
            id=entity.id,
            knowledge_source_id=entity.knowledge_source_id,
            chunk_type=entity.chunk_type,
            chunk_key=entity.chunk_key,
            chunk_index=entity.chunk_index,
            page_start=entity.page_start,
            page_end=entity.page_end,
            section_title=entity.section_title,
            content=entity.content,
            summary=entity.summary,
            issue_code=entity.issue_code,
            risk_category=entity.risk_category,
            severity=entity.severity,
            law_name=entity.law_name,
            article_no=entity.article_no,
            penalty_guide=entity.penalty_guide,
            violation_text=entity.violation_text,
            violation_reason=entity.violation_reason,
            correction_suggestion=entity.correction_suggestion,
            tags=entity.tags,
            metadata=entity.metadata_json,
            embedding_model=entity.embedding_model,
            content_hash=entity.content_hash,
            token_count=entity.token_count,
        )


class KnowledgeChunkListResponse(BaseModel):
    items: list[KnowledgeChunkResponse]
    total_count: int


class KnowledgeIndexResponse(BaseModel):
    source: KnowledgeSourceResponse
    chunk_count: int


class KnowledgeSeedResponse(BaseModel):
    indexed_sources: list[KnowledgeSourceResponse]
    total_sources: int
    total_chunks: int


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    search_mode: str = Field(default="HYBRID", max_length=20)
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeSearchResult(BaseModel):
    chunk: KnowledgeChunkResponse
    keyword_score: float
    vector_score: float
    hybrid_score: float
    matched_terms: list[str]


class KnowledgeSearchResponse(BaseModel):
    query: str
    search_mode: str
    embedding_model: str
    result_count: int
    results: list[KnowledgeSearchResult]


class JobPostingExperimentRunCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_name: str = Field(default="job_posting_risk_50", min_length=1, max_length=100)
    dataset_version: str | None = Field(default=None, max_length=50)
    experiment_type: str = Field(default="RAG_EVAL", max_length=50)
    config_snapshot: dict[str, Any] | None = None


class JobPostingExperimentCaseResultResponse(BaseModel):
    id: int
    case_id: str
    case_index: int
    job_group: str | None = None
    status: str
    expected_label: str | None = None
    predicted_label: str | None = None
    expected_risk_types: list[Any] | None = None
    predicted_risk_types: list[Any] | None = None
    retrieval_hit_at_5: bool | None = None
    source_omitted: bool | None = None
    latency_ms: float | None = None
    error_message: str | None = None
    evaluation_payload: dict[str, Any] | None = None
    report_payload: dict[str, Any] | None = None

    @classmethod
    def from_entity(
        cls,
        entity: JobPostingExperimentCaseResult,
    ) -> "JobPostingExperimentCaseResultResponse":
        return cls(
            id=entity.id,
            case_id=entity.case_id,
            case_index=entity.case_index,
            job_group=entity.job_group,
            status=entity.status,
            expected_label=entity.expected_label,
            predicted_label=entity.predicted_label,
            expected_risk_types=entity.expected_risk_types,
            predicted_risk_types=entity.predicted_risk_types,
            retrieval_hit_at_5=entity.retrieval_hit_at_5,
            source_omitted=entity.source_omitted,
            latency_ms=entity.latency_ms,
            error_message=entity.error_message,
            evaluation_payload=entity.evaluation_payload,
            report_payload=entity.report_payload,
        )


class JobPostingExperimentRunResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    dataset_name: str
    dataset_version: str | None = None
    experiment_type: str
    status: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    retrieval_recall_at_5: float | None = None
    macro_f1: float | None = None
    high_risk_recall: float | None = None
    source_omission_rate: float | None = None
    avg_latency_ms: float | None = None
    config_snapshot: dict[str, Any] | None = None
    summary_metrics: dict[str, Any] | None = None
    result_summary: dict[str, Any] | None = None
    ai_job_id: int | None = None
    requested_by: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(
        cls,
        entity: JobPostingExperimentRun,
    ) -> "JobPostingExperimentRunResponse":
        return cls(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            dataset_name=entity.dataset_name,
            dataset_version=entity.dataset_version,
            experiment_type=entity.experiment_type,
            status=entity.status,
            total_cases=entity.total_cases,
            completed_cases=entity.completed_cases,
            failed_cases=entity.failed_cases,
            retrieval_recall_at_5=entity.retrieval_recall_at_5,
            macro_f1=entity.macro_f1,
            high_risk_recall=entity.high_risk_recall,
            source_omission_rate=entity.source_omission_rate,
            avg_latency_ms=entity.avg_latency_ms,
            config_snapshot=entity.config_snapshot,
            summary_metrics=entity.summary_metrics,
            result_summary=entity.result_summary,
            ai_job_id=entity.ai_job_id,
            requested_by=entity.requested_by,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class JobPostingExperimentRunListResponse(BaseModel):
    items: list[JobPostingExperimentRunResponse]
    total_count: int
    total_pages: int


class JobPostingExperimentRunDetailResponse(BaseModel):
    run: JobPostingExperimentRunResponse
    case_results: list[JobPostingExperimentCaseResultResponse]
