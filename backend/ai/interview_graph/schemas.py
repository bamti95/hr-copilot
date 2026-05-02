from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class GraphBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class DocumentEvidence(GraphBaseModel):
    document_id: int | None = None
    document_type: str | None = None
    title: str | None = None
    quote: str
    reason: str


class DocumentAnalysisOutput(GraphBaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    document_evidence: list[DocumentEvidence] = Field(default_factory=list)
    job_fit: str
    questionable_points: list[str] = Field(default_factory=list)


class QuestionCandidate(GraphBaseModel):
    id: str
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
    question_text: str
    generation_basis: str
    document_evidence: list[str] = Field(default_factory=list)
    evaluation_guide: str
    risk_tags: list[str] = Field(default_factory=list)
    competency_tags: list[str] = Field(default_factory=list)


class QuestionerOutput(GraphBaseModel):
    questions: list[QuestionCandidate]


class PredictedAnswer(GraphBaseModel):
    question_id: str
    predicted_answer: str
    predicted_answer_basis: str = Field(
        validation_alias=AliasChoices("predicted_answer_basis", "evidence_basis"),
    )
    answer_confidence: Literal["low", "medium", "high", "낮음", "보통", "높음"] = Field(
        validation_alias=AliasChoices("answer_confidence", "confidence"),
    )
    answer_risk_points: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("answer_risk_points", "risk_points"),
    )


class PredictorOutput(GraphBaseModel):
    answers: list[PredictedAnswer]


class FollowUpQuestion(GraphBaseModel):
    question_id: str
    follow_up_question: str
    follow_up_basis: str = Field(
        validation_alias=AliasChoices(
            "follow_up_basis",
            "probing_target",
            "expected_signal",
        ),
    )
    drill_type: Literal[
        "ROLE_VERIFICATION",
        "METRIC_VERIFICATION",
        "DECISION_REASONING",
        "FAILURE_RECOVERY",
        "COLLABORATION",
        "RISK_RESPONSE",
        "OTHER",
        "역할_검증",
        "성과_검증",
        "의사결정_검증",
        "실패_복구_검증",
        "협업_갈등_검증",
        "리스크_대응_검증",
        "기타",
    ] = Field(validation_alias=AliasChoices("drill_type", "follow_up_type"))


class DrillerOutput(GraphBaseModel):
    follow_ups: list[FollowUpQuestion]


class ReviewResult(GraphBaseModel):
    question_id: str
    status: Literal["approved", "needs_revision", "rejected"] = Field(
        validation_alias=AliasChoices("status", "decision"),
    )
    reason: str = Field(validation_alias=AliasChoices("reason", "review_summary"))
    reject_reason: str = Field(
        default="",
        validation_alias=AliasChoices("reject_reason", "issues"),
    )
    recommended_revision: str = Field(
        default="",
        validation_alias=AliasChoices("recommended_revision", "revision_suggestion"),
    )

    @field_validator("reject_reason", "recommended_revision", mode="before")
    @classmethod
    def stringify_optional_list(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value)


class ReviewerOutput(GraphBaseModel):
    reviews: list[ReviewResult]


class ScoreResult(GraphBaseModel):
    question_id: str
    score: int = Field(
        ge=0,
        le=100,
        validation_alias=AliasChoices("score", "total_score"),
    )
    score_reason: str = Field(
        validation_alias=AliasChoices("score_reason", "scoring_reason"),
    )
    quality_flags: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("quality_flags", "recommended_action"),
    )

    @field_validator("quality_flags", mode="before")
    @classmethod
    def normalize_quality_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]


class ScorerOutput(GraphBaseModel):
    scores: list[ScoreResult]


class InterviewQuestionItem(GraphBaseModel):
    id: str
    category: str
    question_text: str
    generation_basis: str
    document_evidence: list[str]
    evaluation_guide: str

    predicted_answer: str
    predicted_answer_basis: str

    follow_up_question: str
    follow_up_basis: str

    risk_tags: list[str]
    competency_tags: list[str]

    review: ReviewResult

    score: int
    score_reason: str


class QuestionGenerationResponse(GraphBaseModel):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    status: Literal["completed", "partial_completed", "failed"]

    analysis_summary: DocumentAnalysisOutput

    questions: list[InterviewQuestionItem]

    generation_metadata: dict[str, Any]


class QuestionInteractionRequest(GraphBaseModel):
    session_id: int
    human_action: Literal[
        "more_questions",
        "generate_follow_up",
        "risk_questions",
        "different_perspective",
        "regenerate_question",
    ]
    target_question_ids: list[str] = Field(default_factory=list)
    additional_instruction: str | None = None
