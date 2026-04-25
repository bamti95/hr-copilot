from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentEvidence(BaseModel):
    document_id: int | None = None
    document_type: str | None = None
    title: str | None = None
    quote: str
    reason: str


class DocumentAnalysisOutput(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    document_evidence: list[DocumentEvidence] = Field(default_factory=list)
    job_fit: str
    questionable_points: list[str] = Field(default_factory=list)


class QuestionCandidate(BaseModel):
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


class QuestionerOutput(BaseModel):
    questions: list[QuestionCandidate]


class PredictedAnswer(BaseModel):
    question_id: str
    predicted_answer: str
    predicted_answer_basis: str
    answer_confidence: Literal["low", "medium", "high"]
    answer_risk_points: list[str] = Field(default_factory=list)


class PredictorOutput(BaseModel):
    answers: list[PredictedAnswer]


class FollowUpQuestion(BaseModel):
    question_id: str
    follow_up_question: str
    follow_up_basis: str
    drill_type: Literal[
        "ROLE_VERIFICATION",
        "METRIC_VERIFICATION",
        "DECISION_REASONING",
        "FAILURE_RECOVERY",
        "COLLABORATION",
        "RISK_RESPONSE",
        "OTHER",
    ]


class DrillerOutput(BaseModel):
    follow_ups: list[FollowUpQuestion]


class ReviewResult(BaseModel):
    question_id: str
    status: Literal["approved", "rejected"]
    reason: str
    reject_reason: str = ""
    recommended_revision: str = ""


class ReviewerOutput(BaseModel):
    reviews: list[ReviewResult]


class ScoreResult(BaseModel):
    question_id: str
    score: int = Field(ge=0, le=100)
    score_reason: str
    quality_flags: list[str] = Field(default_factory=list)


class ScorerOutput(BaseModel):
    scores: list[ScoreResult]


class InterviewQuestionItem(BaseModel):
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


class QuestionGenerationResponse(BaseModel):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    status: Literal["completed", "partial_completed", "failed"]

    analysis_summary: DocumentAnalysisOutput

    questions: list[InterviewQuestionItem]

    generation_metadata: dict[str, Any]


class QuestionInteractionRequest(BaseModel):
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
