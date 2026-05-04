"""그래프에서 공유하는 state 타입 정의.

LangGraph에서는 노드끼리 state를 주고받으며 동작한다.
이 파일은 그 state가 어떤 필드를 가지는지 설명하는 역할을 한다.
"""

from typing import Any, Literal, TypedDict


# 질문 단위 처리 상태.
# - pending: 아직 후속 노드 처리가 남아 있음
# - approved: reviewer 통과
# - needs_revision: 부분 수정 후 다시 검토 필요
# - rejected: 구조적으로 약해서 큰 수정 또는 재생성 필요
# - human_rejected: 사람이 특정 질문만 다시 만들라고 지정한 상태
QuestionStatus = Literal["pending", "approved", "rejected", "human_rejected", "needs_revision"]


# 서비스나 프론트에서 그래프를 다시 호출할 때 넘길 수 있는 액션 종류.
HumanAction = Literal[
    "more",
    "more_questions",
    "regenerate",
    "regenerate_question",
    "add_question",
    "generate_follow_up",
    "risk_questions",
    "different_perspective",
]


class DocumentRef(TypedDict):
    """그래프 입력으로 들어오는 문서 한 건."""

    document_id: int
    document_type: str
    title: str
    extracted_text: str


class PromptProfileRef(TypedDict, total=False):
    """채용 기준과 관련된 프롬프트 프로필 정보."""

    id: int
    profile_key: str
    target_job: str | None
    system_prompt: str
    output_schema: dict[str, Any] | list[Any] | str | None


class LlmUsageState(TypedDict, total=False):
    """노드별 LLM 사용량/비용/시간 기록."""

    node: str
    model_name: str
    run_id: str
    parent_run_id: str
    trace_id: str
    run_type: str
    execution_order: int
    request_json: dict[str, Any]
    output_json: dict[str, Any] | None
    response_json: dict[str, Any] | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    call_status: str
    elapsed_ms: int
    error_message: str
    started_at: Any
    ended_at: Any


class QuestionSet(TypedDict, total=False):
    """그래프 내부에서 질문 1건을 표현하는 핵심 구조."""

    id: str
    category: str
    generation_basis: str
    document_evidence: list[str]
    question_text: str
    evaluation_guide: str
    predicted_answer: str
    predicted_answer_basis: str
    answer_confidence: str
    answer_risk_points: list[str]
    follow_up_question: str
    follow_up_basis: str
    drill_type: str
    risk_tags: list[str]
    competency_tags: list[str]
    review_status: str
    review_reason: str
    reject_reason: str
    recommended_revision: str
    review_issue_types: list[str]
    requested_revision_fields: list[str]
    question_quality_scores: dict[str, int]
    evaluation_guide_scores: dict[str, int]
    question_quality_average: float
    evaluation_guide_average: float
    score: float
    score_reason: str
    status: QuestionStatus
    regen_targets: list[str]
    generation_mode: str
    retry_guidance: str


class AgentState(TypedDict, total=False):
    """그래프 전체가 공유하는 루트 state."""

    session_id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    difficulty_level: str | None

    prompt_profile: PromptProfileRef | None
    documents: list[DocumentRef]

    # prepare_context가 만든 공통 문맥 문자열.
    candidate_context: str

    # 질문 생성/수정/검토가 누적되는 메인 데이터.
    questions: list[QuestionSet]

    retry_count: int
    max_retry_count: int
    is_all_approved: bool

    human_action: HumanAction | str | None
    additional_instruction: str | None
    target_question_ids: list[str]
    generation_mode: str | None

    llm_usages: list[LlmUsageState]
    node_warnings: list[dict[str, Any]]
