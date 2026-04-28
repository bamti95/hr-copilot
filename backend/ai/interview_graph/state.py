import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    source_payload: dict[str, Any]
    # 입력으로 들어온 원본 데이터 (이력서, JD, 사용자 요청 등 전체 payload)

    candidate_text: str
    # 후보자 관련 텍스트 (이력서 본문, 자기소개 등)

    recruitment_criteria: dict[str, Any]
    # 채용 기준 (필수/우대 조건, 평가 기준 등)

    document_analysis: dict[str, Any]
    # 후보자 문서 분석 결과 (스킬 추출, 요약, 키워드 등)

    questions: list[dict[str, Any]]
    # 생성된 전체 면접 질문 리스트

    selected_questions: list[dict[str, Any]]
    # 실제로 선택된 질문 (출제용)

    candidate_question_count: int
    # 후보자에게 할 질문 개수

    answers: list[dict[str, Any]]
    # 후보자의 답변 기록

    follow_ups: list[dict[str, Any]]
    # 꼬리 질문(추가 질문) 목록

    reviews: list[dict[str, Any]]
    # 각 답변에 대한 리뷰/피드백

    scores: list[dict[str, Any]]
    # 평가 점수 (질문별 또는 전체)

    review_summary: dict[str, Any]
    # 전체 리뷰 요약 (강점/약점/종합 평가)

    node_warnings: Annotated[list[dict[str, Any]], operator.add]
    # 각 노드 실행 중 발생한 경고 누적 (operator.add로 병합됨)

    router_decision: str
    # 다음 단계로 어떤 노드를 실행할지 결정하는 라우팅 값

    retry_feedback: str | None
    # 재시도 시 참고할 피드백 (왜 실패했는지 등)

    retry_count: int
    # 현재까지 재시도 횟수

    max_retry_count: int
    # 최대 허용 재시도 횟수

    human_action: str | None
    # 사람이 개입해서 해야 할 액션 (승인, 수정 등)

    additional_instruction: str | None
    # 추가 지시사항 (프롬프트 보강용)

    regen_question_ids: list[str] | None
    # 다시 생성해야 할 질문 ID 목록

    final_response: dict[str, Any]
    # 최종 사용자에게 반환할 결과