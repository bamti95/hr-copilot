import operator
from typing import Annotated, Any, Optional, TypedDict


class DocumentRef(TypedDict):
    document_id: int
    document_type: str
    title: str
    extracted_text: str


class PromptProfileRef(TypedDict):
    id: int
    profile_key: str
    target_job: Optional[str]
    system_prompt: str
    output_schema: Optional[dict[str, Any] | list[Any] | str]


class LlmUsageState(TypedDict, total=False):
    node: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    call_status: str
    elapsed_ms: int
    error_message: str


class InputState(TypedDict, total=False):
    session_id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    difficulty_level: str | None
    prompt_profile: PromptProfileRef
    documents: list[DocumentRef]
    additional_instruction: str | None
    human_action: str | None
    target_question_ids: list[str]


class WorkflowState(TypedDict, total=False):
    candidate_context: str
    document_analysis: dict[str, Any]
    questions: list[dict[str, Any]]
    answers: list[dict[str, Any]]
    follow_ups: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    scores: list[dict[str, Any]]
    review_summary: dict[str, Any]


class ControlState(TypedDict, total=False):
    retry_feedback: str | None
    retry_count: int
    max_retry_count: int
    node_warnings: Annotated[list[dict[str, Any]], operator.add]


class ObservabilityState(TypedDict, total=False):
    llm_usages: Annotated[list[LlmUsageState], operator.add]


class OutputState(TypedDict, total=False):
    final_response: dict[str, Any]


class AgentState(
    InputState,
    WorkflowState,
    ControlState,
    ObservabilityState,
    OutputState,
    total=False,
):
    pass
