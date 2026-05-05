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


class AgentState(TypedDict, total=False):
    job_posting: str
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
    questions: list[QuestionSet]

    selected_questions: list[QuestionSet]
    is_all_approved: bool
    retry_count: int
    max_retry_count: int
    status: GraphStatus

    errors: list[str]
    raw_outputs: dict[str, Any]
    response: Any
