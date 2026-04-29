"""`interview_graph_JH` 패키지 State 타입 정의 파일.

LangGraph의 각 노드가 공유하는 `AgentState`, 질문 단위 데이터인
`QuestionSet`, 입력 문서/프롬프트/LLM 사용량 타입을 정의합니다.
이 파일은 데이터 형태만 담당하고, LLM 호출이나 노드 실행 로직은
`nodes.py`에서 처리합니다.
"""

from typing import Any, Literal, TypedDict


# 질문 한 개의 워크플로 단계(에이전트 공유 상태)에서 쓰는 상태값.
# pending: 아직 검토 전 / predictor·driller 진행 중
# approved: Reviewer 통과
# rejected: Reviewer가 반려 → questioner로 재작성 루프 가능
# human_rejected: 사람(또는 서비스)이 "이 질문만 다시 써 달라"고 찍은 경우
QuestionStatus = Literal["pending", "approved", "rejected", "human_rejected"]

# 서비스/프론트가 그래프 재호출 때 넘기는 "사람 액션" 종류(영문 코드).
# 문자열 그대로 쓰이므로, 뜻만 알면 됨.
HumanAction = Literal[
    "more",  # 더보기: 기존 질문 유지하고 질문만 추가
    "more_questions",  # 팀 API와 맞춘 별칭
    "regenerate",  # 부분 재생성: target_question_ids에 있는 질문만 다시
    "regenerate_question",  # 팀 API와 맞춘 별칭
    "add_question",  # 추가 질문: additional_instruction 내용 반영해 새 질문
    "generate_follow_up",  # 다른 관점 등(현재는 add_question과 비슷하게 처리)
    "risk_questions",  # 리스크 위주 요청(프롬프트 분기용으로 확장 가능)
    "different_perspective",  # 다른 관점 요청(프롬프트 분기용)
]


class DocumentRef(TypedDict):
    """그래프에 주입되는 단일 지원자 문서."""

    document_id: int  # DB 문서 PK
    document_type: str  # RESUME 등 타입 코드
    title: str  # 문서 제목
    extracted_text: str  # OCR/추출된 본문(가장 중요한 입력)


class PromptProfileRef(TypedDict, total=False):
    """채용팀이 선택한 프롬프트 프로필(평가 기준·인재상 등)."""

    id: int  # 프로필 PK
    profile_key: str  # 프로필 식별 키(표시용)
    target_job: str | None  # 이 프로필이 묶인 직무(없으면 공통)
    system_prompt: str  # LLM에 들어가는 채용 평가 기준 본문(recruitment_criteria와 동일 역할)
    output_schema: dict[str, Any] | list[Any] | str | None  # JSON 스키마 등(선택)


class LlmUsageState(TypedDict, total=False):
    """노드 한 번 호출당 토큰·비용·시간(로그 테이블과 맞춤)."""

    node: str  # 어떤 노드에서 호출했는지(예: questioner, predictor)
    model_name: str  # 모델 이름
    input_tokens: int  # 입력 토큰 수
    output_tokens: int  # 출력 토큰 수
    total_tokens: int  # 합계 토큰
    estimated_cost: float  # 추정 비용(USD 등)
    call_status: str  # success / failed
    elapsed_ms: int  # 걸린 시간(밀리초)
    error_message: str  # 실패 시 메시지


class QuestionSet(TypedDict, total=False):
    """질문 1건에 대한 공유 상태(네 설계서의 QuestionSet에 해당).

    모든 에이전트가 이 객체의 필드를 순서대로 채우거나 갱신합니다.
    """

    id: str  # 질문 고유 ID(재생성 대상 매칭에 사용됨)
    category: str  # 질문 분류(TECH, RISK 등 팀 스키마와 맞춤)
    generation_basis: str  # 왜 이 질문을 만들었는지 근거(서류 인용 등)
    document_evidence: list[str]  # 문서 근거 문자열 목록(팀 스키마: 문자열 리스트)
    question_text: str  # 면접에서 읽을 본 질문
    evaluation_guide: str  # 면접관용 평가 가이드(고득점/감점 요령)
    predicted_answer: str  # Predictor가 쓴 지원자 예상 답변
    predicted_answer_basis: str  # 예상 답변을 왜 그렇게 봤는지 한 줄 근거
    follow_up_question: str  # Driller가 쓴 꼬리 질문
    follow_up_basis: str  # 꼬리 질문의 근거(어느 허점을 찌르는지)
    risk_tags: list[str]  # 리스크 태그(한국어 등)
    competency_tags: list[str]  # 역량 태그
    review_status: str  # Reviewer 출력: approved / needs_revision / rejected
    review_reason: str  # 검토 요약(한글로 쓰도록 프롬프트에서 지시)
    reject_reason: str   # 반려 시 구체 사유
    recommended_revision: str  # 수정 방향 제안
    score: int  # 간이 점수(Reviewer 결과에서 매핑, 팀은 별도 Scorer 있음)
    score_reason: str  # 점수/판정에 대한 이유 한 줄
    status: QuestionStatus  # 워크플로 단계용 상태(pending/approved/rejected/human_rejected)
    regen_targets: list[str]  # 부분 재생성 시 고칠 필드명 목록(예: question_text, follow_up_question)


class AgentState(TypedDict, total=False):
    """그래프 전체가 공유하는 루트 상태."""

    # --- 세션·지원자 식별(서비스가 처음에 채움) ---
    session_id: int  # 면접 세션 DB ID
    candidate_id: int  # 지원자 ID
    candidate_name: str  # 지원자 이름(프롬프트에 쓸 수 있음)
    target_job: str  # 지원 직무 코드/문자열
    difficulty_level: str | None  # 난이도(JUNIOR 등)

    # --- 입력 원본 ---
    prompt_profile: PromptProfileRef | None  # 선택한 프롬프트 프로필(없으면 None)
    documents: list[DocumentRef]  # 지원자가 제출한 문서 목록

    # --- 파생 입력(노드가 만듦) ---
    candidate_context: str  # 문서들을 합쳐 LLM이 읽기 쉬운 긴 텍스트 블록

    # --- 핵심 프로세스 데이터 ---
    questions: list[QuestionSet]  # 생성·검토 중인 질문 리스트(설계서의 공유 리스트)

    # --- 루프 제어 ---
    retry_count: int  # Review 반려로 questioner에 돌아간 횟수(무한 루프 방지)
    max_retry_count: int  # retry 상한(기본 3 등)
    is_all_approved: bool  # 모든 질문이 approved인지(참고용 플래그)

    # --- 서비스 레이어 재호출 시 넣는 값(사람이 누른 액션) ---
    # human_action: 사용자 액션 문자열(more, regenerate_question 등). 영어라서
    #               의미만 알면 되고, 위 HumanAction에 나열해 둠.
    human_action: HumanAction | str | None

    # additional_instruction: **추가 지시 문장**(한국어로 써도 됨).
    # 예: "이력서에 있는 Python 프로젝트 경험만 물어봐 줘", "꼬리 질문은 짧게".
    # 서비스/프론트가 사람 입력을 그대로 실어 보낼 때 여기에 넣음.
    additional_instruction: str | None

    # target_question_ids: **부분 재생성할 질문의 id 목록**(문자열).
    # human_action이 regenerate 계열일 때 어떤 질문만 다시 쓸지 지정.
    target_question_ids: list[str]

    # --- 관측성 ---
    llm_usages: list[LlmUsageState]  # 노드별 누적 LLM 사용량(비용·시간 집계용)
    node_warnings: list[dict[str, Any]]  # 파싱 실패·스킵 등 경고(디버깅용)
