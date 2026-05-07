"""JY 그래프 전용 스키마 진입점."""

from typing import Annotated, Any, Literal

from pydantic import AliasChoices, Field, field_validator

from ai.interview_graph.schemas import (
    DrillerOutput as DrillerOutputBase,
    FollowUpQuestion as FollowUpQuestionBase,
    GraphBaseModel,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionInteractionRequest,
    ReviewResult,
    ReviewerOutput,
    ScoreResult,
    ScorerOutput,
)

ShortText = Annotated[str, Field(max_length=120)]
TagText = Annotated[str, Field(max_length=40)]
# Driller 꼬리질문 본문·근거 공통 상한 (프롬프트·스키마와 맞출 것)
FOLLOW_UP_TEXT_MAX = 120


class DocumentEvidence(GraphBaseModel):
    document_id: int | None = None
    document_type: str | None = None
    title: str | None = Field(default=None, max_length=80)
    quote: str = Field(max_length=120)
    reason: str = Field(max_length=120)


class DocumentAnalysisOutput(GraphBaseModel):
    strengths: list[ShortText] = Field(default_factory=list, max_length=2)
    weaknesses: list[ShortText] = Field(default_factory=list, max_length=2)
    risks: list[ShortText] = Field(default_factory=list, max_length=6)
    document_evidence: list[DocumentEvidence] = Field(default_factory=list, max_length=5)
    job_fit: str = Field(max_length=220)
    questionable_points: list[ShortText] = Field(default_factory=list, max_length=8)


class QuestionCandidate(GraphBaseModel):
    id: str = Field(max_length=32)
    category: Literal[
        "TECH",
        "JOB_SKILL",
        "EXPERIENCE",
        "RISK",
        "CULTURE_FIT",
        "MOTIVATION",
        "COMMUNICATION",
        "OTHER",
        "기술",
        "직무_역량",
        "경험",
        "리스크",
        "조직_적합성",
        "지원_동기",
        "커뮤니케이션",
        "기타",
    ]
    question_text: str = Field(max_length=180)
    generation_basis: str = Field(max_length=140)
    document_evidence: list[ShortText] = Field(default_factory=list, max_length=2)
    evaluation_guide: str = Field(max_length=180)
    risk_tags: list[TagText] = Field(default_factory=list, max_length=4)
    competency_tags: list[TagText] = Field(default_factory=list, max_length=4)


class QuestionerOutput(GraphBaseModel):
    questions: list[QuestionCandidate] = Field(max_length=8)


class FollowUpQuestion(FollowUpQuestionBase):
    """꼬리질문은 면접에서 바로 읽을 수 있도록 짧게 유지합니다."""

    follow_up_question: str = Field(max_length=FOLLOW_UP_TEXT_MAX)
    follow_up_basis: str = Field(
        max_length=FOLLOW_UP_TEXT_MAX,
        validation_alias=AliasChoices(
            "follow_up_basis",
            "probing_target",
            "expected_signal",
        ),
    )

    @field_validator("follow_up_question", "follow_up_basis", mode="before")
    @classmethod
    def _trim_follow_up_text(cls, value: object) -> object:
        if isinstance(value, str) and len(value) > FOLLOW_UP_TEXT_MAX:
            return value[:FOLLOW_UP_TEXT_MAX].rstrip()
        return value


class DrillerOutput(DrillerOutputBase):
    follow_ups: list[FollowUpQuestion]


class QuestionGenerationResponse(GraphBaseModel):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    status: Literal["completed", "partial_completed", "failed"]
    analysis_summary: DocumentAnalysisOutput
    questions: list[InterviewQuestionItem]
    generation_metadata: dict[str, Any]


__all__ = [
    "DocumentAnalysisOutput",
    "DocumentEvidence",
    "DrillerOutput",
    "FollowUpQuestion",
    "GraphBaseModel",
    "InterviewQuestionItem",
    "PredictedAnswer",
    "PredictorOutput",
    "QuestionCandidate",
    "QuestionGenerationResponse",
    "QuestionInteractionRequest",
    "QuestionerOutput",
    "ReviewResult",
    "ReviewerOutput",
    "ScoreResult",
    "ScorerOutput",
]
