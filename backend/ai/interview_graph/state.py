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
    recruitment_criteria: dict[str, Any]
    candidate_question_count: int
    additional_instruction: str | None


class PreparedState(TypedDict, total=False):
    candidate_text: str
    merged_candidate_context: str


class AnalysisState(TypedDict, total=False):
    document_analysis: dict[str, Any]


class QuestionState(TypedDict, total=False):
    questions: list[dict[str, Any]]
    selected_questions: list[dict[str, Any]]
    regen_question_ids: list[str] | None


class EvaluationState(TypedDict, total=False):
    answers: list[dict[str, Any]]
    follow_ups: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    scores: list[dict[str, Any]]
    review_summary: dict[str, Any]


class ControlState(TypedDict, total=False):
    router_decision: str
    retry_feedback: str | None
    retry_count: int
    max_retry_count: int
    human_action: str | None
    is_all_approved: bool
    node_warnings: Annotated[list[dict[str, Any]], operator.add]


class ObservabilityState(TypedDict, total=False):
    llm_usages: Annotated[list[LlmUsageState], operator.add]


class OutputState(TypedDict, total=False):
    final_response: dict[str, Any]


class AgentState(
    InputState,
    PreparedState,
    AnalysisState,
    QuestionState,
    EvaluationState,
    ControlState,
    ObservabilityState,
    OutputState,
    total=False,
):
    pass
