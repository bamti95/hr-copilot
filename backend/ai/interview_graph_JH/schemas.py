"""JH 그래프 전용 Pydantic 스키마.

핵심 원칙:
1. 내부 코드값은 하나로 통일한다.
2. LLM이 한글/영문 값을 섞어 반환해도 validator에서 정규화한다.
3. 최종 응답에는 각 노드가 만든 핵심 메타데이터를 최대한 보존한다.
"""

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

QUESTION_CATEGORY_MAP = {
    "TECH": "TECH",
    "기술": "TECH",
    "JOB_SKILL": "JOB_SKILL",
    "직무_역량": "JOB_SKILL",
    "EXPERIENCE": "EXPERIENCE",
    "경험": "EXPERIENCE",
    "RISK": "RISK",
    "리스크": "RISK",
    "CULTURE_FIT": "CULTURE_FIT",
    "조직_적합성": "CULTURE_FIT",
    "MOTIVATION": "MOTIVATION",
    "지원_동기": "MOTIVATION",
    "LEADERSHIP": "LEADERSHIP",
    "리더십": "LEADERSHIP",
    "COMMUNICATION": "COMMUNICATION",
    "커뮤니케이션": "COMMUNICATION",
    "OTHER": "OTHER",
    "기타": "OTHER",
}

ANSWER_CONFIDENCE_MAP = {
    "low": "low",
    "낮음": "low",
    "medium": "medium",
    "보통": "medium",
    "high": "high",
    "높음": "high",
}

DRILL_TYPE_MAP = {
    "EVIDENCE_CHECK": "EVIDENCE_CHECK",
    "ROLE_VERIFICATION": "EVIDENCE_CHECK",
    "역할_검증": "EVIDENCE_CHECK",
    "DEPTH_CHECK": "DEPTH_CHECK",
    "OWNERSHIP_CHECK": "OWNERSHIP_CHECK",
    "METRIC_CHECK": "METRIC_CHECK",
    "METRIC_VERIFICATION": "METRIC_CHECK",
    "성과_검증": "METRIC_CHECK",
    "DECISION_CHECK": "DECISION_CHECK",
    "DECISION_REASONING": "DECISION_CHECK",
    "의사결정_검증": "DECISION_CHECK",
    "FAILURE_RECOVERY": "FAILURE_RECOVERY",
    "실패_복구_검증": "FAILURE_RECOVERY",
    "COLLABORATION": "COLLABORATION",
    "협업_갈등_검증": "COLLABORATION",
    "RISK_RESPONSE": "RISK_RESPONSE",
    "리스크_대응_검증": "RISK_RESPONSE",
    "OTHER": "OTHER",
    "기타": "OTHER",
}


class GraphBaseModel(BaseModel):
    """JH 그래프용 공통 BaseModel."""

    model_config = ConfigDict(populate_by_name=True)


class DocumentEvidence(GraphBaseModel):
    """문서 근거 한 건."""

    document_id: int | None = None
    document_type: str | None = None
    title: str | None = None
    quote: str
    reason: str


class DocumentAnalysisOutput(GraphBaseModel):
    """최종 응답에 담기는 간단한 문서 분석 요약."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    document_evidence: list[DocumentEvidence] = Field(default_factory=list)
    job_fit: str
    questionable_points: list[str] = Field(default_factory=list)


class QuestionCandidate(GraphBaseModel):
    """Questioner가 생성하는 질문 후보."""

    id: str
    category: Literal[
        "TECH",
        "JOB_SKILL",
        "EXPERIENCE",
        "RISK",
        "CULTURE_FIT",
        "MOTIVATION",
        "LEADERSHIP",
        "COMMUNICATION",
        "OTHER",
    ]
    question_text: str
    generation_basis: str
    document_evidence: list[str] = Field(default_factory=list)
    evaluation_guide: str
    risk_tags: list[str] = Field(default_factory=list)
    competency_tags: list[str] = Field(default_factory=list)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        normalized = QUESTION_CATEGORY_MAP.get(str(value), str(value))
        return normalized


class QuestionerOutput(GraphBaseModel):
    """Questioner의 구조화 출력."""

    questions: list[QuestionCandidate]


class PredictedAnswer(GraphBaseModel):
    """Predictor가 만든 예상 답변."""

    question_id: str
    predicted_answer: str
    predicted_answer_basis: str = Field(
        validation_alias=AliasChoices("predicted_answer_basis", "evidence_basis"),
    )
    answer_confidence: Literal["low", "medium", "high"] = Field(
        validation_alias=AliasChoices("answer_confidence", "confidence"),
    )
    answer_risk_points: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("answer_risk_points", "risk_points"),
    )

    @field_validator("answer_confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> str:
        return ANSWER_CONFIDENCE_MAP.get(str(value), str(value))


class PredictorOutput(GraphBaseModel):
    """Predictor의 구조화 출력."""

    answers: list[PredictedAnswer]


class FollowUpQuestion(GraphBaseModel):
    """Driller가 생성하는 꼬리질문."""

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
        "EVIDENCE_CHECK",
        "DEPTH_CHECK",
        "OWNERSHIP_CHECK",
        "METRIC_CHECK",
        "DECISION_CHECK",
        "FAILURE_RECOVERY",
        "COLLABORATION",
        "RISK_RESPONSE",
        "OTHER",
    ] = Field(validation_alias=AliasChoices("drill_type", "follow_up_type"))

    @field_validator("drill_type", mode="before")
    @classmethod
    def normalize_drill_type(cls, value: Any) -> str:
        return DRILL_TYPE_MAP.get(str(value), str(value))


class DrillerOutput(GraphBaseModel):
    """Driller의 구조화 출력."""

    follow_ups: list[FollowUpQuestion]


class QuestionQualityRubric(GraphBaseModel):
    """질문 품질 루브릭(고정 키). OpenAI strict JSON schema는 자유 dict를 허용하지 않는다."""

    job_relevance: int = Field(ge=1, le=5)
    document_grounding: int = Field(ge=1, le=5)
    validation_power: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    distinctiveness: int = Field(ge=1, le=5)
    interview_usability: int = Field(ge=1, le=5)
    core_resume_coverage: int = Field(ge=1, le=5)

    @model_validator(mode="before")
    @classmethod
    def coerce_from_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        keys = (
            "job_relevance",
            "document_grounding",
            "validation_power",
            "specificity",
            "distinctiveness",
            "interview_usability",
            "core_resume_coverage",
        )
        out: dict[str, int] = {}
        for key in keys:
            raw = data.get(key)
            try:
                out[key] = max(1, min(5, int(raw)))
            except (TypeError, ValueError):
                out[key] = 3
        return out


class EvaluationGuideRubric(GraphBaseModel):
    """평가 가이드 루브릭(고정 키)."""

    guide_alignment: int = Field(ge=1, le=5)
    signal_clarity: int = Field(ge=1, le=5)
    good_bad_answer_separation: int = Field(ge=1, le=5)
    practical_usability: int = Field(ge=1, le=5)
    verification_specificity: int = Field(ge=1, le=5)

    @model_validator(mode="before")
    @classmethod
    def coerce_from_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        keys = (
            "guide_alignment",
            "signal_clarity",
            "good_bad_answer_separation",
            "practical_usability",
            "verification_specificity",
        )
        out: dict[str, int] = {}
        for key in keys:
            raw = data.get(key)
            try:
                out[key] = max(1, min(5, int(raw)))
            except (TypeError, ValueError):
                out[key] = 3
        return out


class ReviewResult(GraphBaseModel):
    """Reviewer가 한 질문 세트에 대해 남기는 평가 결과."""

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
    issue_types: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("issue_types", "review_issue_types"),
    )
    requested_revision_fields: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("requested_revision_fields", "revision_fields"),
    )
    question_quality_scores: QuestionQualityRubric
    evaluation_guide_scores: EvaluationGuideRubric
    question_quality_average: float = 0.0
    evaluation_guide_average: float = 0.0
    overall_score: float = Field(
        default=0.0,
        validation_alias=AliasChoices("overall_score", "average_score"),
    )

    @field_validator("reject_reason", "recommended_revision", mode="before")
    @classmethod
    def stringify_optional_list(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value)

    @field_validator("issue_types", "requested_revision_fields", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return [str(value)]

class ReviewerOutput(GraphBaseModel):
    """Reviewer의 구조화 출력."""

    reviews: list[ReviewResult]


class ScoreResult(GraphBaseModel):
    """루브릭 평균 점수를 따로 다루고 싶을 때 쓰는 보조 스키마."""

    question_id: str
    score: float = Field(
        ge=1,
        le=5,
        validation_alias=AliasChoices("score", "average_score", "overall_score"),
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
    """별도 점수 리스트가 필요할 때 쓰는 보조 스키마."""

    scores: list[ScoreResult]


class InterviewQuestionItem(GraphBaseModel):
    """최종 응답에 담기는 질문 1건."""

    id: str
    category: str
    question_text: str
    generation_basis: str
    document_evidence: list[str]
    evaluation_guide: str

    predicted_answer: str
    predicted_answer_basis: str
    answer_confidence: str
    answer_risk_points: list[str] = Field(default_factory=list)

    follow_up_question: str
    follow_up_basis: str
    drill_type: str

    risk_tags: list[str]
    competency_tags: list[str]

    review: ReviewResult

    score: float
    score_reason: str


class QuestionGenerationResponse(GraphBaseModel):
    """JH 그래프 최종 응답."""

    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    status: Literal["completed", "partial_completed", "failed"]

    analysis_summary: DocumentAnalysisOutput
    questions: list[InterviewQuestionItem]
    generation_metadata: dict[str, Any]


class QuestionInteractionRequest(GraphBaseModel):
    """프론트/서비스가 그래프 재호출 시 보내는 요청."""

    session_id: int
    human_action: Literal[
        "more",
        "more_questions",
        "add_question",
        "generate_follow_up",
        "risk_questions",
        "different_perspective",
        "regenerate",
        "regenerate_question",
    ]
    target_question_ids: list[str] = Field(default_factory=list)
    additional_instruction: str | None = None
