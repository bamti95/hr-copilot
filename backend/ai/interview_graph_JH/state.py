"""State contracts for the JH interview-question LangGraph.

The public response contract lives in ``schemas.py``.  This module keeps the
internal graph state small and explicit so each node has one clear job:

1. questioner creates enough candidates,
2. predictor/driller enrich only unevaluated candidates,
3. reviewer evaluates and ranks candidates,
4. selector returns the best five.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict


HumanAction = Literal[
    "generate",
    "add_question",
    "regenerate_selected",
    "regenerate_batch",
]

QuestionStatus = Literal[
    "pending",
    "approved",
    "needs_revision",
    "rejected",
    "human_rejected",
]

GraphStatus = Literal[
    "pending",
    "completed",
    "partial_completed",
    "review_failed",
    "failed",
]


class QuestionSet(TypedDict, total=False):
    id: str
    original_question_id: int | str | None
    focus_area: str
    category: str
    generation_basis: str
    document_evidence: str

    question_text: str
    evaluation_guide: str
    predicted_answer: str
    predicted_answer_basis: str
    follow_up_questions: list[str]
    follow_up_intents: list[str]

    status: QuestionStatus
    review_status: str
    review_reason: str
    recommended_revision: str
    reject_reason: str
    review_issue_types: list[str]
    requested_revision_fields: list[str]

    question_quality_scores: dict[str, int]
    evaluation_guide_scores: dict[str, int]
    question_quality_average: float
    evaluation_guide_average: float
    score: float
    score_reason: str

    is_selectable: bool
    selection_rank: int
    selection_reason: str
    review_strengths: list[str]
    review_risks: list[str]

    generation_mode: str
    regen_targets: list[str]
    retry_issue_types: list[str]
    retry_guidance: str
    previous_review_status: str
    previous_review_reason: str
    previous_score_reason: str
    previous_recommended_revision: str
    previous_score: float
    rewrite_feedback: str


class AgentState(TypedDict, total=False):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None

    job_posting: str
    prompt_profile_key: str | None
    prompt_profile_target_job: str | None
    prompt_profile_system_prompt: str | None
    prompt_profile_output_schema: dict[str, Any] | list[Any] | str | None
    prompt_profile_summary: str
    company_name: str | None
    applicant_name: str | None
    resume: str
    cover_letter: str
    portfolio: str
    existing_questions: list[dict[str, Any]]

    human_action: HumanAction
    selected_question_ids: list[int | str]
    feedback: str | None
    requested_count: int

    context: str
    candidate_context: str
    verification_profile: dict[str, Any]
    questions: list[QuestionSet]

    selected_questions: list[QuestionSet]
    is_all_approved: bool
    retry_count: int
    max_retry_count: int
    status: GraphStatus

    errors: list[str]
    raw_outputs: dict[str, Any]
    response: Any
