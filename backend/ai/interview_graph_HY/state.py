from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


QuestionStatus = Literal["pending", "approved", "rejected", "human_rejected"]


class QuestionSet(TypedDict, total=False):
    id: str
    generation_basis: str
    document_evidence: list[str]
    question_text: str
    evaluation_guide: str
    predicted_answer: str
    follow_up_question: str

    status: QuestionStatus
    review_reason: str
    reject_reason: str
    recommended_revision: str
    quality_flags: list[str]
    duplicate_with: str

    score: int
    score_reason: str

    regen_targets: list[str]


class AgentState(TypedDict, total=False):
    _payload: Any
    candidate_text: str
    recruitment_criteria: str
    questions: list[QuestionSet]

    retry_count: int
    max_retry_count: int
    is_all_approved: bool

    human_action: str | None
    additional_instruction: str | None
    regen_question_ids: list[str] | None

    node_warnings: Annotated[list[dict[str, Any]], operator.add]
    llm_usages: Annotated[list[dict[str, Any]], operator.add]

    final_response: dict[str, Any]
