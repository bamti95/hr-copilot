from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    source_payload: dict[str, Any]

    candidate_text: str
    recruitment_criteria: dict[str, Any]

    document_analysis: dict[str, Any]

    questions: list[dict[str, Any]]
    selected_questions: list[dict[str, Any]]

    answers: list[dict[str, Any]]
    follow_ups: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    scores: list[dict[str, Any]]

    review_summary: dict[str, Any]

    router_decision: str
    retry_feedback: str | None
    retry_count: int
    max_retry_count: int

    human_action: str | None
    additional_instruction: str | None
    regen_question_ids: list[str] | None

    final_response: dict[str, Any]
