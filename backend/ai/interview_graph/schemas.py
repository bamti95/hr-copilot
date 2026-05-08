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


QuestionCategory = Literal[
    "기술 역량",
    "직무 역량",
    "경험 검증",
    "리스크 검증",
    "조직 적합성",
    "지원 동기",
    "커뮤니케이션",
    "기타",
]

QUESTION_CATEGORY_ALIASES = {
    "TECH": "기술 역량",
    "기술": "기술 역량",
    "기술역량": "기술 역량",
    "기술_역량": "기술 역량",
    "JOB_SKILL": "직무 역량",
    "직무": "직무 역량",
    "직무역량": "직무 역량",
    "직무_역량": "직무 역량",
    "EXPERIENCE": "경험 검증",
    "경험": "경험 검증",
    "경험검증": "경험 검증",
    "경험_검증": "경험 검증",
    "RISK": "리스크 검증",
    "리스크": "리스크 검증",
    "리스크검증": "리스크 검증",
    "리스크_검증": "리스크 검증",
    "CULTURE_FIT": "조직 적합성",
    "조직적합성": "조직 적합성",
    "조직_적합성": "조직 적합성",
    "문화_적합성": "조직 적합성",
    "MOTIVATION": "지원 동기",
    "지원동기": "지원 동기",
    "지원_동기": "지원 동기",
    "COMMUNICATION": "커뮤니케이션",
    "의사소통": "커뮤니케이션",
    "OTHER": "기타",
    "기타": "기타",
}

QUESTION_GENERATION_BASIS_MAX_CHARS = 120
QUESTION_DOCUMENT_EVIDENCE_MAX_ITEMS = 2
QUESTION_DOCUMENT_EVIDENCE_MAX_CHARS = 80
QUESTION_EVALUATION_GUIDE_MAX_CHARS = 160
QUESTION_TAG_MAX_ITEMS = 3


def _clip_compact_text(value: Any, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def _normalize_limited_text_list(
    value: Any,
    *,
    max_items: int,
    max_chars: int | None = None,
) -> list[str]:
    if value is None:
        return []
    raw_items = value if isinstance(value, list) else [value]
    items: list[str] = []
    for item in raw_items:
        text = " ".join(str(item or "").split())
        if not text:
            continue
        if max_chars is not None:
            text = _clip_compact_text(text, max_chars)
        items.append(text)
        if len(items) >= max_items:
            break
    return items


def normalize_question_category(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "기타"
    key = raw.upper().replace(" ", "_")
    return QUESTION_CATEGORY_ALIASES.get(
        raw,
        QUESTION_CATEGORY_ALIASES.get(key, raw),
    )


class QuestionCandidate(GraphBaseModel):
    id: str
    category: QuestionCategory
    question_text: str
    generation_basis: str = Field(max_length=QUESTION_GENERATION_BASIS_MAX_CHARS)
    document_evidence: list[str] = Field(
        default_factory=list,
        max_length=QUESTION_DOCUMENT_EVIDENCE_MAX_ITEMS,
    )
    evaluation_guide: str = Field(max_length=QUESTION_EVALUATION_GUIDE_MAX_CHARS)
    risk_tags: list[str] = Field(default_factory=list, max_length=QUESTION_TAG_MAX_ITEMS)
    competency_tags: list[str] = Field(
        default_factory=list,
        max_length=QUESTION_TAG_MAX_ITEMS,
    )

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        return normalize_question_category(value)

    @field_validator("generation_basis", mode="before")
    @classmethod
    def compact_generation_basis(cls, value: Any) -> str:
        return _clip_compact_text(value, QUESTION_GENERATION_BASIS_MAX_CHARS)

    @field_validator("document_evidence", mode="before")
    @classmethod
    def compact_document_evidence(cls, value: Any) -> list[str]:
        return _normalize_limited_text_list(
            value,
            max_items=QUESTION_DOCUMENT_EVIDENCE_MAX_ITEMS,
            max_chars=QUESTION_DOCUMENT_EVIDENCE_MAX_CHARS,
        )

    @field_validator("evaluation_guide", mode="before")
    @classmethod
    def compact_evaluation_guide(cls, value: Any) -> str:
        return _clip_compact_text(value, QUESTION_EVALUATION_GUIDE_MAX_CHARS)

    @field_validator("risk_tags", "competency_tags", mode="before")
    @classmethod
    def compact_tags(cls, value: Any) -> list[str]:
        return _normalize_limited_text_list(
            value,
            max_items=QUESTION_TAG_MAX_ITEMS,
        )


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
    category: QuestionCategory
    question_text: str
    generation_basis: str = Field(max_length=QUESTION_GENERATION_BASIS_MAX_CHARS)
    document_evidence: list[str] = Field(max_length=QUESTION_DOCUMENT_EVIDENCE_MAX_ITEMS)
    evaluation_guide: str = Field(max_length=QUESTION_EVALUATION_GUIDE_MAX_CHARS)

    predicted_answer: str
    predicted_answer_basis: str

    follow_up_question: str
    follow_up_basis: str

    risk_tags: list[str] = Field(max_length=QUESTION_TAG_MAX_ITEMS)
    competency_tags: list[str] = Field(max_length=QUESTION_TAG_MAX_ITEMS)

    review: ReviewResult

    score: int
    score_reason: str

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        return normalize_question_category(value)

    @field_validator("generation_basis", mode="before")
    @classmethod
    def compact_generation_basis(cls, value: Any) -> str:
        return _clip_compact_text(value, QUESTION_GENERATION_BASIS_MAX_CHARS)

    @field_validator("document_evidence", mode="before")
    @classmethod
    def compact_document_evidence(cls, value: Any) -> list[str]:
        return _normalize_limited_text_list(
            value,
            max_items=QUESTION_DOCUMENT_EVIDENCE_MAX_ITEMS,
            max_chars=QUESTION_DOCUMENT_EVIDENCE_MAX_CHARS,
        )

    @field_validator("evaluation_guide", mode="before")
    @classmethod
    def compact_evaluation_guide(cls, value: Any) -> str:
        return _clip_compact_text(value, QUESTION_EVALUATION_GUIDE_MAX_CHARS)

    @field_validator("risk_tags", "competency_tags", mode="before")
    @classmethod
    def compact_tags(cls, value: Any) -> list[str]:
        return _normalize_limited_text_list(
            value,
            max_items=QUESTION_TAG_MAX_ITEMS,
        )


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
