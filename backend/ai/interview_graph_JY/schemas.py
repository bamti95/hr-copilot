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

QUESTION_CATEGORY_ALIASES = {
    "TECH": "TECH",
    "기술": "기술",
    "기술역량": "기술",
    "기술_역량": "기술",
    "기술 역량": "기술",
    "JOB_SKILL": "JOB_SKILL",
    "직무": "직무_역량",
    "직무역량": "직무_역량",
    "직무_역량": "직무_역량",
    "직무 역량": "직무_역량",
    "EXPERIENCE": "EXPERIENCE",
    "경험": "경험",
    "경험검증": "경험",
    "경험_검증": "경험",
    "경험 검증": "경험",
    "RISK": "RISK",
    "리스크": "리스크",
    "리스크검증": "리스크",
    "리스크_검증": "리스크",
    "리스크 검증": "리스크",
    "CULTURE_FIT": "CULTURE_FIT",
    "조직적합성": "조직_적합성",
    "조직_적합성": "조직_적합성",
    "조직 적합성": "조직_적합성",
    "문화_적합성": "조직_적합성",
    "문화 적합성": "조직_적합성",
    "MOTIVATION": "MOTIVATION",
    "지원동기": "지원_동기",
    "지원_동기": "지원_동기",
    "지원 동기": "지원_동기",
    "COMMUNICATION": "COMMUNICATION",
    "커뮤니케이션": "커뮤니케이션",
    "의사소통": "커뮤니케이션",
    "OTHER": "OTHER",
    "기타": "기타",
}


def normalize_jy_question_category(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "기타"
    key = raw.upper().replace(" ", "_")
    return QUESTION_CATEGORY_ALIASES.get(
        raw,
        QUESTION_CATEGORY_ALIASES.get(key, raw),
    )


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

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        return normalize_jy_question_category(value)


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
    "normalize_jy_question_category",
    "QuestionerOutput",
    "ReviewResult",
    "ReviewerOutput",
    "ScoreResult",
    "ScorerOutput",
]
