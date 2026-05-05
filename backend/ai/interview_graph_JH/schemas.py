"""Pydantic contracts used by the JH interview-question graph.

The service layer persists several fields from these models, so the existing
public names are intentionally preserved while the reviewer semantics are
changed from "reject/pass gate" to "evaluate/rank/select".
"""

from __future__ import annotations

import statistics
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ReviewStatus = Literal["approved", "needs_revision", "rejected"]
ResponseStatus = Literal["completed", "partial_completed", "failed"]


QUESTION_QUALITY_FIELDS = (
    "job_relevance",
    "document_grounding",
    "competency_signal",
    "specificity",
    "clarity",
)

EVALUATION_GUIDE_FIELDS = (
    "scoring_clarity",
    "evidence_alignment",
    "answer_discriminability",
    "risk_awareness",
    "interviewer_usability",
)

HARD_REVIEW_ISSUES = {
    "unsupported_assumption",
    "off_topic",
    "fairness_risk",
    "personal_sensitive",
    "no_document_anchor",
}


class GraphBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class QuestionCandidate(GraphBaseModel):
    category: str = Field(
        ...,
        description="역량/경험/직무적합도 등 면접 질문 카테고리",
    )
    generation_basis: str = Field(
        ...,
        description="질문을 만든 이유. 이력서/자소서/포트폴리오 근거와 확인하려는 역량을 함께 설명",
    )
    document_evidence: str = Field(
        ...,
        description="질문이 기대고 있는 지원자 문서의 짧은 근거 문장 또는 요약",
    )
    question_text: str = Field(..., description="면접관이 실제로 읽을 질문")
    evaluation_guide: str = Field(
        ...,
        description=(
            "면접관용 실전 가이드. 관찰 포인트, 좋은/보통/부족한 답변 기준, "
            "모호한 답변의 후속 확인 방향을 포함"
        ),
    )


class QuestionerOutput(GraphBaseModel):
    questions: list[QuestionCandidate] = Field(
        ...,
        min_length=1,
        description="생성 또는 재생성된 면접 질문 후보 목록",
    )


class PredictedAnswer(GraphBaseModel):
    question_text: str
    predicted_answer: str = Field(
        ...,
        description="지원자 문서만 근거로 추론한 예상 답변. 문서에 없으면 추정이라고 명시",
    )
    predicted_answer_basis: str = Field(
        ...,
        description="예상 답변을 만든 문서 근거 또는 추론 근거",
    )


class PredictorOutput(GraphBaseModel):
    answers: list[PredictedAnswer] = Field(..., min_length=1)


class FollowUpQuestion(GraphBaseModel):
    question_text: str
    follow_up_questions: list[str] = Field(..., min_length=2, max_length=3)
    follow_up_intents: list[str] = Field(..., min_length=2, max_length=3)

    @model_validator(mode="after")
    def align_intents(self) -> "FollowUpQuestion":
        if len(self.follow_up_intents) != len(self.follow_up_questions):
            self.follow_up_intents = self.follow_up_intents[: len(self.follow_up_questions)]
            while len(self.follow_up_intents) < len(self.follow_up_questions):
                self.follow_up_intents.append("답변의 구체성과 근거 확인")
        return self


class DrillerOutput(GraphBaseModel):
    follow_ups: list[FollowUpQuestion] = Field(..., min_length=1)


class QuestionQualityRubric(GraphBaseModel):
    job_relevance: int = Field(default=3, ge=1, le=5)
    document_grounding: int = Field(default=3, ge=1, le=5)
    competency_signal: int = Field(default=3, ge=1, le=5)
    specificity: int = Field(default=3, ge=1, le=5)
    clarity: int = Field(default=3, ge=1, le=5)


class EvaluationGuideRubric(GraphBaseModel):
    scoring_clarity: int = Field(default=3, ge=1, le=5)
    evidence_alignment: int = Field(default=3, ge=1, le=5)
    answer_discriminability: int = Field(default=3, ge=1, le=5)
    risk_awareness: int = Field(default=3, ge=1, le=5)
    interviewer_usability: int = Field(default=3, ge=1, le=5)


class ReviewResult(GraphBaseModel):
    question_id: str = ""
    status: ReviewStatus
    reason: str
    recommended_revision: str = ""
    reject_reason: str = ""
    issue_types: list[str] = Field(default_factory=list)
    requested_revision_fields: list[str] = Field(default_factory=list)
    question_quality_scores: QuestionQualityRubric = Field(
        default_factory=QuestionQualityRubric
    )
    evaluation_guide_scores: EvaluationGuideRubric = Field(
        default_factory=EvaluationGuideRubric
    )
    overall_score: Annotated[float, Field(ge=1, le=5)] = 3
    selection_reason: str = Field(
        default="",
        description="상위 5개 선별 관점에서 이 후보가 강하거나 약한 이유",
    )
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    is_selectable: bool = Field(
        default=True,
        description="최종 5개 후보로 선택해도 되는지 여부",
    )

    @field_validator("issue_types", "requested_revision_fields", mode="before")
    @classmethod
    def normalize_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @model_validator(mode="after")
    def normalize_review_fields(self) -> "ReviewResult":
        if self.status == "approved":
            self.reject_reason = ""
            self.requested_revision_fields = []
            self.recommended_revision = self.recommended_revision or ""
        if self.status == "rejected" and not self.reject_reason:
            self.reject_reason = self.reason
        return self

    @property
    def question_quality_average(self) -> float:
        return float(statistics.mean(self.question_quality_scores.model_dump().values()))

    @property
    def evaluation_guide_average(self) -> float:
        return float(statistics.mean(self.evaluation_guide_scores.model_dump().values()))


class ReviewedQuestion(GraphBaseModel):
    question_text: str
    review: ReviewResult


class ReviewerOutput(GraphBaseModel):
    reviews: list[ReviewedQuestion] = Field(..., min_length=1)


class DocumentAnalysisOutput(GraphBaseModel):
    job_fit: str = ""
    risks: list[str] = Field(default_factory=list)


class InterviewQuestionItem(GraphBaseModel):
    id: str
    category: str
    question_text: str
    generation_basis: str
    document_evidence: list[str] = Field(default_factory=list)
    evaluation_guide: str = Field(
        ...,
        description="면접관이 답변을 들으며 바로 사용할 수 있는 평가 및 진행 가이드",
    )

    predicted_answer: str = ""
    predicted_answer_basis: str = ""

    follow_up_question: str = ""
    follow_up_basis: str = ""
    follow_up_questions: list[str] = Field(default_factory=list)
    follow_up_intents: list[str] = Field(default_factory=list)

    risk_tags: list[str] = Field(default_factory=list)
    competency_tags: list[str] = Field(default_factory=list)

    review: ReviewResult
    score: int = 0
    score_reason: str = ""


class QuestionGenerationResponse(GraphBaseModel):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    status: ResponseStatus
    questions: list[InterviewQuestionItem] = Field(default_factory=list)
    analysis_summary: DocumentAnalysisOutput = Field(default_factory=DocumentAnalysisOutput)
    generation_metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionInteractionRequest(GraphBaseModel):
    action: Literal["add_question", "regenerate_selected", "regenerate_batch"]
    selected_question_ids: list[int | str] = Field(default_factory=list)
    feedback: str | None = None
    requested_count: int | None = None
