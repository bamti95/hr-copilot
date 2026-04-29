"""`interview_graph_JH`의 LangGraph 노드 구현 파일.

각 노드는 `AgentState`를 입력받아 필요한 필드만 갱신합니다.
흐름은 `prepare_context -> questioner -> predictor -> driller -> reviewer`이며,
Reviewer가 반려한 질문은 Questioner로 되돌려 재작성합니다.
최종 응답 변환(`build_response`)도 이 파일에서 담당합니다.
"""

import json
import logging
from typing import Any

from ai.interview_graph.llm_usage import (
    StructuredOutputCallError,
    call_structured_output_with_usage,
)
from ai.interview_graph.schemas import (
    DocumentAnalysisOutput,
    DrillerOutput,
    FollowUpQuestion,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionCandidate,
    QuestionGenerationResponse,
    QuestionerOutput,
    ReviewResult,
    ReviewerOutput,
)
from ai.interview_graph_JH import prompts
from ai.interview_graph_JH.state import AgentState, QuestionSet

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 18000
PREDICTOR_DOCUMENT_CHARS = 7000
DEFAULT_QUESTION_COUNT = 5
MORE_QUESTION_COUNT = 3
ADD_QUESTION_COUNT = 2


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip(value: str, max_chars: int) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n...(길이 제한으로 일부 생략)"


def _recruitment_criteria(state: AgentState) -> str:
    prompt_profile = state.get("prompt_profile") or {}
    return str(prompt_profile.get("system_prompt") or "채용 평가 기준이 별도로 제공되지 않았습니다.")


def _merge_document_text(state: AgentState) -> str:
    sections = [
        "[Session]",
        f"session_id: {state.get('session_id')}",
        f"target_job: {state.get('target_job')}",
        f"difficulty_level: {state.get('difficulty_level')}",
        "",
        "[Candidate]",
        f"candidate_id: {state.get('candidate_id')}",
        f"name: {state.get('candidate_name')}",
    ]

    remaining = MAX_DOCUMENT_CHARS
    for document in state.get("documents", []):
        extracted_text = str(document.get("extracted_text") or "").strip()
        if remaining <= 0:
            break
        clipped = extracted_text[:remaining]
        remaining -= len(clipped)
        sections.extend(
            [
                "",
                f"[Document #{document.get('document_id')}]",
                f"type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                clipped or "(추출 텍스트 없음)",
            ]
        )

    return "\n".join(sections)


def _format_questions(items: list[QuestionSet], *, include_answer: bool = False) -> str:
    if not items:
        return "(없음)"
    compact: list[dict[str, Any]] = []
    for item in items:
        data: dict[str, Any] = {
            "id": item.get("id"),
            "category": item.get("category"),
            "question_text": item.get("question_text"),
            "generation_basis": item.get("generation_basis"),
            "document_evidence": item.get("document_evidence", []),
            "evaluation_guide": item.get("evaluation_guide"),
            "risk_tags": item.get("risk_tags", []),
            "competency_tags": item.get("competency_tags", []),
            "status": item.get("status"),
            "reject_reason": item.get("reject_reason") or item.get("recommended_revision"),
        }
        if include_answer:
            data.update(
                {
                    "predicted_answer": item.get("predicted_answer"),
                    "predicted_answer_basis": item.get("predicted_answer_basis"),
                    "follow_up_question": item.get("follow_up_question"),
                    "follow_up_basis": item.get("follow_up_basis"),
                }
            )
        compact.append(data)
    return _json(compact)


def _question_id(question: QuestionSet, index: int) -> str:
    """질문의 stable id를 반환.

    질문 객체에 이미 id가 있으면 그대로 사용하고, 없으면 인덱스 기반 fallback을
    사용한다. fallback은 안전망일 뿐이고, 정상 흐름에서는 prepare_context_node
    에서 모든 질문에 id를 미리 박아두므로 인덱스 의존이 발생하지 않는다.
    """
    return str(question.get("id") or f"jh-q-{index + 1}")


def _allocate_question_id(used_ids: set[str], counter: list[int]) -> str:
    """append 모드에서 기존 id와 충돌하지 않는 새 질문 id를 발급.

    [로직 순서]
    1. 호출자가 넘긴 카운터를 1 증가시킨다(리스트로 받아서 in-place 갱신).
    2. f"jh-q-{n}" 형태로 후보 id를 만든다.
    3. used_ids에 이미 있으면 카운터를 더 올려 다음 후보를 만든다.
    4. 충돌이 없으면 used_ids에 등록하고 그 id를 반환한다.
    """
    while True:
        counter[0] += 1
        candidate = f"jh-q-{counter[0]}"
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate


def _ensure_question_ids(questions: list[QuestionSet]) -> None:
    """질문 리스트에 stable id를 보장한다.

    [로직 순서]
    1. 이미 부여된 id를 모아 used_ids 집합으로 만든다.
    2. id가 비어 있는 항목에 대해 _allocate_question_id로 새 id를 부여한다.
    3. 카운터는 기존 jh-q-N 패턴 중 최댓값 + 1부터 시작해 충돌을 줄인다.
    """
    used_ids: set[str] = set()
    max_seen = 0
    for question in questions:
        question_id = str(question.get("id") or "")
        if not question_id:
            continue
        used_ids.add(question_id)
        if question_id.startswith("jh-q-"):
            try:
                max_seen = max(max_seen, int(question_id.removeprefix("jh-q-")))
            except ValueError:
                continue

    counter = [max_seen]
    for question in questions:
        if not question.get("id"):
            question["id"] = _allocate_question_id(used_ids, counter)


async def prepare_context_node(state: AgentState) -> dict[str, Any]:
    """[0] 입력 문서 정리 노드.

    [로직 순서]
    1. 기존 질문에 stable id가 없으면 jh-q-N 형태로 부여(이후 모든 노드의 id 기준점)
    2. 이미 candidate_context가 있으면 재생성하지 않고 그대로 사용
    3. 세션/지원자 메타데이터와 제출 문서를 하나의 텍스트 블록으로 병합
    4. 이후 Questioner/Predictor가 같은 문맥을 보도록 변경된 필드만 반환
    """
    questions = list(state.get("questions") or [])
    _ensure_question_ids(questions)

    update: dict[str, Any] = {"questions": questions}
    if not state.get("candidate_context"):
        update["candidate_context"] = _merge_document_text(state)
    return update


def _questioner_mode(state: AgentState, questions: list[QuestionSet]) -> tuple[str, list[QuestionSet]]:
    """Questioner가 어떤 생성 모드로 동작할지 결정.

    [우선순위]
    1. Reviewer가 반려한 질문이 있으면 review_rewrite
    2. 서비스 레이어가 특정 질문 재생성을 요청하면 regenerate
    3. 더보기 요청이면 more
    4. 추가 지시사항 기반 요청이면 add_question
    5. 그 외 최초 실행은 initial
    """
    rejected = [item for item in questions if item.get("status") == "rejected"]
    if rejected:
        return "review_rewrite", rejected

    human_action = (state.get("human_action") or "").strip()
    target_ids = {str(qid) for qid in (state.get("target_question_ids") or [])}
    if human_action in {"regenerate", "regenerate_question"} and target_ids:
        targets = [
            item
            for item in questions
            if str(item.get("id") or "") in target_ids
        ]
        return "regenerate", targets
    if human_action in {"more", "more_questions"}:
        return "more", []
    if human_action in {"add_question", "generate_follow_up", "risk_questions", "different_perspective"}:
        return "add_question", []
    return "initial", []


def _task_instruction(mode: str, targets: list[QuestionSet]) -> str:
    if mode == "initial":
        return f"새 질문 {DEFAULT_QUESTION_COUNT}개를 생성하세요."
    if mode == "more":
        return f"기존 질문과 중복되지 않는 새 질문 {MORE_QUESTION_COUNT}개를 추가 생성하세요."
    if mode == "add_question":
        return f"추가 지시사항을 반영해 새 질문 {ADD_QUESTION_COUNT}개를 생성하세요."
    target_block = _format_questions(targets, include_answer=True)
    return (
        "아래 대상 질문만 id를 유지한 채 재작성하세요. "
        "반려 사유와 보완 제안을 반드시 반영하세요. "
        "regen_targets가 있으면 해당 필드(question_text, evaluation_guide, "
        "follow_up_question 등)를 우선 보완하세요.\n"
        f"{target_block}"
    )


async def questioner_node(state: AgentState) -> dict[str, Any]:
    """[1] Questioner: 질문 초안 생성/재작성.

    [로직 순서]
    1. 현재 상태를 보고 최초 생성/더보기/추가질문/재생성/리뷰반려 모드 결정
    2. 지원자 서류, 채용 기준, 기존 질문, 반려 피드백을 프롬프트에 주입
    3. 구조화 출력(QuestionerOutput)으로 질문 후보를 받음
    4. append 모드는 LLM이 준 id를 무시하고 _allocate_question_id로 충돌 없는 신규 id 발급
    5. 재작성 모드는 기존 id가 명시된 응답만 update, 미스매치는 경고로 기록
    6. 다음 노드가 처리할 수 있게 status를 pending으로 초기화
    """
    questions = list(state.get("questions") or [])
    _ensure_question_ids(questions)
    mode, targets = _questioner_mode(state, questions)

    update: dict[str, Any] = {
        # human_action은 1회성 요청이므로 노드 종료 시 항상 초기화
        "human_action": None,
        "additional_instruction": None,
        "target_question_ids": [],
    }
    if mode == "review_rewrite":
        update["retry_count"] = state.get("retry_count", 0) + 1

    # [1] 모드별 작업 지시를 포함한 Questioner 프롬프트 구성
    user_prompt = prompts.QUESTIONER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        recruitment_criteria=_recruitment_criteria(state),
        candidate_context=state.get("candidate_context") or "",
        mode=mode,
        additional_instruction=state.get("additional_instruction") or "(없음)",
        existing_questions=_format_questions(questions, include_answer=True),
        retry_feedback=_format_questions(targets, include_answer=True),
        task_instruction=_task_instruction(mode, targets),
    )

    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        # [2] LLM 구조화 출력 호출 + 비용/토큰 사용량 수집
        parsed, usages = await call_structured_output_with_usage(
            node_name="jh_questioner",
            system_prompt=prompts.QUESTIONER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=QuestionerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "jh_questioner", "message": str(exc)})
        update["questions"] = questions
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
        return update

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    should_append = mode in {"initial", "more", "add_question"}

    # [3] append 모드에서 LLM이 우연히 기존 id와 같은 값을 반환해도 데이터를
    # 덮어쓰지 않도록, 항상 카운터로 새 id를 발급한다.
    used_ids: set[str] = set(by_id.keys())
    max_seen = 0
    for existing_id in used_ids:
        if existing_id.startswith("jh-q-"):
            try:
                max_seen = max(max_seen, int(existing_id.removeprefix("jh-q-")))
            except ValueError:
                continue
    id_counter = [max_seen]

    target_ids = [str(item.get("id") or "") for item in targets]
    for index, question in enumerate(parsed.questions):
        model = question.model_dump(mode="json")
        if should_append:
            # LLM이 반환한 id는 무시하고 충돌 없는 신규 id를 발급한다.
            question_id = _allocate_question_id(used_ids, id_counter)
        else:
            llm_id = str(model.get("id") or "")
            fallback_id = target_ids[index] if index < len(target_ids) else ""
            question_id = llm_id if llm_id in by_id else fallback_id
            if not question_id or question_id not in by_id:
                new_warnings.append(
                    {
                        "node": "jh_questioner",
                        "message": (
                            "재작성 응답이 기존 질문 id와 매칭되지 않아 건너뜁니다 "
                            f"(llm_id={llm_id or '없음'})."
                        ),
                    }
                )
                continue
        entry: QuestionSet = {
            "id": question_id,
            "category": model.get("category") or "OTHER",
            "generation_basis": model.get("generation_basis") or "",
            "document_evidence": model.get("document_evidence") or [],
            "question_text": model.get("question_text") or "",
            "evaluation_guide": model.get("evaluation_guide") or "",
            "risk_tags": model.get("risk_tags") or [],
            "competency_tags": model.get("competency_tags") or [],
            "predicted_answer": "",
            "predicted_answer_basis": "",
            "follow_up_question": "",
            "follow_up_basis": "",
            "review_status": "needs_revision",
            "review_reason": "",
            "reject_reason": "",
            "recommended_revision": "",
            "score": 75,
            "score_reason": "Reviewer 결과 기반 기본 점수입니다.",
            "status": "pending",
        }
        if should_append:
            questions.append(entry)
            by_id[question_id] = entry
        else:
            by_id[question_id].update(entry)

    update["questions"] = questions
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


async def predictor_node(state: AgentState) -> dict[str, Any]:
    """[2] Predictor: 지원자 예상 답변 생성.

    [로직 순서]
    1. pending/human_rejected 중 아직 예상 답변이 없는 질문만 선별
    2. 지원자 서류·직무·난이도와 질문 목록을 기반으로 현실적인 답변을 생성
    3. question_id 기준으로 원래 QuestionSet에 predicted_answer를 병합
    4. 이미 답변이 있는 기존 질문은 비용 절감을 위해 재호출하지 않음
    """
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected"} and not item.get("predicted_answer")
    ]
    if not targets:
        return {}

    # [1] Predictor는 전체 문서를 다 읽지 않도록 입력 길이를 제한
    user_prompt = prompts.PREDICTOR_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        candidate_context=_clip(state.get("candidate_context") or "", PREDICTOR_DOCUMENT_CHARS),
        questions=_format_questions(targets),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        # [2] 예상 답변 구조화 출력 호출
        parsed, usages = await call_structured_output_with_usage(
            node_name="jh_predictor",
            system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PredictorOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "jh_predictor", "message": str(exc)})
        return {
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for answer in parsed.answers:
        model = answer.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["predicted_answer"] = model.get("predicted_answer") or ""
        target["predicted_answer_basis"] = model.get("predicted_answer_basis") or ""

    update: dict[str, Any] = {"questions": questions}
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


async def driller_node(state: AgentState) -> dict[str, Any]:
    """[3] Driller: 예상 답변 기반 꼬리 질문 생성.

    [로직 순서]
    1. 예상 답변은 있지만 꼬리 질문이 없는 질문만 선별
    2. 원 질문과 예상 답변의 빈틈을 파고드는 follow-up을 생성
    3. question_id 기준으로 follow_up_question/follow_up_basis를 병합
    4. 이미 꼬리 질문이 있는 기존 질문은 재호출하지 않음
    """
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected"}
        and item.get("predicted_answer")
        and not item.get("follow_up_question")
    ]
    if not targets:
        return {}

    # [1] Driller는 질문+예상답변 세트를 보고 검증 포인트를 좁힘
    user_prompt = prompts.DRILLER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        recruitment_criteria=_recruitment_criteria(state),
        questions=_format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        # [2] 꼬리 질문 구조화 출력 호출
        parsed, usages = await call_structured_output_with_usage(
            node_name="jh_driller",
            system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DrillerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "jh_driller", "message": str(exc)})
        return {
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for follow_up in parsed.follow_ups:
        model = follow_up.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["follow_up_question"] = model.get("follow_up_question") or ""
        target["follow_up_basis"] = model.get("follow_up_basis") or ""

    update: dict[str, Any] = {"questions": questions}
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


async def reviewer_node(state: AgentState) -> dict[str, Any]:
    """[4] Reviewer: 질문 세트 품질 검수.

    [로직 순서]
    1. 아직 검토가 필요한 pending/human_rejected 질문만 선별
    2. 질문/근거/평가가이드/예상답변/꼬리질문 전체 세트를 검토
    3. approved면 최종 통과, needs_revision/rejected면 rejected 상태로 표시
    4. rejected가 남아 있으면 review_router가 Questioner로 재작성 루프를 보냄
    5. Reviewer 호출 자체가 실패하면 백그라운드 잡 중단을 막기 위해 임시 needs_revision 처리
    """
    questions = list(state.get("questions") or [])
    targets = [item for item in questions if item.get("status") in {"pending", "human_rejected"}]
    if not targets:
        return {
            "is_all_approved": bool(questions)
            and all(item.get("status") == "approved" for item in questions)
        }

    # [1] Reviewer는 최종 사용성/근거/공정성/중복 위험을 함께 본다
    user_prompt = prompts.REVIEWER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        recruitment_criteria=_recruitment_criteria(state),
        questions=_format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        # [2] 품질 검수 구조화 출력 호출
        parsed, usages = await call_structured_output_with_usage(
            node_name="jh_reviewer",
            system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ReviewerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "jh_reviewer", "message": str(exc)})
        # Reviewer 호출 실패 시 retry_count를 강제로 max로 올려 무한 루프를 차단한다.
        for item in targets:
            item["status"] = "rejected"
            item["review_status"] = "needs_revision"
            item["review_reason"] = "Reviewer 호출 실패로 품질 검수를 완료하지 못했습니다."
            item["reject_reason"] = "Reviewer 호출 실패"
            item["recommended_revision"] = "품질 검수 재실행 또는 프롬프트/입력 길이 점검이 필요합니다."
        return {
            "questions": questions,
            "retry_count": state.get("max_retry_count", 3),
            "is_all_approved": False,
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for review in parsed.reviews:
        model = review.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        status = str(model.get("status") or "needs_revision")
        target["review_status"] = status
        target["review_reason"] = model.get("reason") or ""
        target["reject_reason"] = model.get("reject_reason") or ""
        target["recommended_revision"] = model.get("recommended_revision") or ""
        target["status"] = "approved" if status == "approved" else "rejected"
        target["score"] = 90 if status == "approved" else 70 if status == "needs_revision" else 45
        target["score_reason"] = target["review_reason"] or target["recommended_revision"]

    update: dict[str, Any] = {
        "questions": questions,
        "is_all_approved": bool(questions)
        and all(item.get("status") == "approved" for item in questions),
    }
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


def review_router(state: AgentState) -> str:
    """Reviewer 결과에 따라 재작성 루프 여부 결정.

    [로직 순서]
    1. rejected 상태 질문이 있는지 확인
    2. retry_count가 max_retry_count 미만이면 Questioner로 재진입
    3. 모두 승인됐거나 재시도 한도에 도달하면 그래프 종료
    """
    has_rejected = any(item.get("status") == "rejected" for item in state.get("questions", []))
    if has_rejected and state.get("retry_count", 0) < state.get("max_retry_count", 3):
        return "retry"
    return "end"


def _fallback_answer(question_id: str) -> PredictedAnswer:
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="예상 답변을 생성하지 못했습니다.",
        predicted_answer_basis="예상 답변 생성 결과가 없습니다.",
        answer_confidence="low",
        answer_risk_points=["예상_답변_누락"],
    )


def _fallback_follow_up(question_id: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="앞선 답변에서 가장 구체적으로 확인해야 할 부분을 추가로 설명해 주시겠어요?",
        follow_up_basis="꼬리 질문 생성 결과가 없어 기본 질문을 사용했습니다.",
        drill_type="OTHER",
    )


def _fallback_review(question_id: str) -> ReviewResult:
    return ReviewResult(
        question_id=question_id,
        status="needs_revision",
        reason="Reviewer 결과가 없어 보완 필요로 처리했습니다.",
        reject_reason="",
        recommended_revision="질문 근거와 평가 기준을 다시 확인하세요.",
    )


def _analysis_summary(state: AgentState) -> DocumentAnalysisOutput:
    questions = state.get("questions", [])
    risk_tags = sorted(
        {
            tag
            for item in questions
            for tag in item.get("risk_tags", [])
            if tag
        }
    )
    return DocumentAnalysisOutput(
        strengths=[],
        weaknesses=[],
        risks=risk_tags[:8],
        document_evidence=[],
        job_fit=(
            "이 그래프는 별도 Analyzer 노드 없이 질문 생성 근거와 Reviewer 결과를 기반으로 "
            "직무 적합성 검증 질문을 구성했습니다."
        ),
        questionable_points=[
            item.get("generation_basis", "")
            for item in questions[:5]
            if item.get("generation_basis")
        ],
    )


def build_response(state: AgentState) -> QuestionGenerationResponse:
    """그래프 State를 기존 서비스 저장용 응답으로 변환.

    [로직 순서]
    1. QuestionSet 리스트를 InterviewQuestionItem 리스트로 변환
    2. 누락된 예상 답변/꼬리 질문/리뷰는 fallback 값으로 보완
    3. 승인 개수, 재시도 한도, 노드 경고를 기준으로 completed/partial_completed 결정
    4. generation_metadata에 pipeline=jh와 그래프 구조를 기록

    DB 저장 로직은 공용 QuestionGenerationService가 담당하므로,
    여기서는 기존 저장 스키마에 맞는 응답 객체만 만든다.
    """
    items: list[InterviewQuestionItem] = []
    for index, question in enumerate(state.get("questions", [])):
        question_id = _question_id(question, index)
        question_model = QuestionCandidate.model_validate(
            {
                "id": question_id,
                "category": question.get("category") or "OTHER",
                "question_text": question.get("question_text") or "",
                "generation_basis": question.get("generation_basis") or "",
                "document_evidence": question.get("document_evidence") or [],
                "evaluation_guide": question.get("evaluation_guide") or "",
                "risk_tags": question.get("risk_tags") or [],
                "competency_tags": question.get("competency_tags") or [],
            }
        )
        answer = PredictedAnswer.model_validate(
            {
                "question_id": question_id,
                "predicted_answer": question.get("predicted_answer") or "예상 답변을 생성하지 못했습니다.",
                "predicted_answer_basis": question.get("predicted_answer_basis") or "예상 답변 근거가 없습니다.",
                "answer_confidence": "medium",
                "answer_risk_points": [],
            }
        )
        follow_up = FollowUpQuestion.model_validate(
            {
                "question_id": question_id,
                "follow_up_question": question.get("follow_up_question")
                or _fallback_follow_up(question_id).follow_up_question,
                "follow_up_basis": question.get("follow_up_basis")
                or _fallback_follow_up(question_id).follow_up_basis,
                "drill_type": "OTHER",
            }
        )
        review = ReviewResult.model_validate(
            {
                "question_id": question_id,
                "status": question.get("review_status") or "needs_revision",
                "reason": question.get("review_reason") or _fallback_review(question_id).reason,
                "reject_reason": question.get("reject_reason") or "",
                "recommended_revision": question.get("recommended_revision") or "",
            }
        )
        items.append(
            InterviewQuestionItem(
                id=question_id,
                category=question_model.category,
                question_text=question_model.question_text,
                generation_basis=question_model.generation_basis,
                document_evidence=question_model.document_evidence,
                evaluation_guide=question_model.evaluation_guide,
                predicted_answer=answer.predicted_answer,
                predicted_answer_basis=answer.predicted_answer_basis,
                follow_up_question=follow_up.follow_up_question,
                follow_up_basis=follow_up.follow_up_basis,
                risk_tags=question_model.risk_tags,
                competency_tags=question_model.competency_tags,
                review=review,
                score=int(question.get("score") or 75),
                score_reason=question.get("score_reason") or "Reviewer 결과 기반 점수입니다.",
            )
        )

    # is_partial 판정 기준
    # - 질문 개수가 기준치 미만: 실제로 모자란 상태
    # - 승인되지 않은 질문 존재: 품질 미통과
    # - 재시도 한도 도달: 더 이상 개선 시도 불가
    # node_warnings는 메타데이터로만 보존하고 사용자 노출 status에는 영향을 주지
    # 않는다(예: Reviewer가 미매칭 응답 1개를 흘려도 모든 질문이 승인됐다면
    # completed로 표시).
    approved_count = sum(1 for item in items if item.review.status == "approved")
    all_approved = bool(items) and approved_count == len(items)
    hit_retry_limit = state.get("retry_count", 0) >= state.get("max_retry_count", 3)
    is_partial = (
        len(items) < DEFAULT_QUESTION_COUNT
        or not all_approved
        or hit_retry_limit
    )
    return QuestionGenerationResponse(
        session_id=state.get("session_id"),
        candidate_id=state.get("candidate_id"),
        target_job=state.get("target_job") or "",
        difficulty_level=state.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=_analysis_summary(state),
        questions=items,
        generation_metadata={
            "pipeline": "jh",
            "total_candidate_questions": len(state.get("questions", [])),
            "selected_question_count": len(items),
            "retry_count": state.get("retry_count", 0),
            "is_all_approved": approved_count == len(items) and bool(items),
            "node_warnings": state.get("node_warnings", []),
            "graph": "PrepareContext -> Questioner -> Predictor -> Driller -> Reviewer",
        },
    )
