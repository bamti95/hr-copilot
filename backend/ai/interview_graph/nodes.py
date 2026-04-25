import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from ai.interview_graph import prompts
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
    ScoreResult,
    ScorerOutput,
)
from ai.interview_graph.state import AgentState
from ai.llm_client import client, get_openai_model

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_DOCUMENT_CHARS = 18000


async def _call_structured_output(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> T:
    last_error: Exception | None = None
    for _ in range(2):
        try:
            response = await client.responses.parse(
                model=get_openai_model(),
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=response_model,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("Structured output was empty.")
            return parsed
        except Exception as exc:  # noqa: BLE001 - preserve original SDK/validation error.
            last_error = exc
            logger.warning(
                "Structured output call failed for %s: %s",
                response_model.__name__,
                exc,
            )
    raise RuntimeError(
        f"Structured output call failed for {response_model.__name__}"
    ) from last_error


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _merge_document_text(payload: dict[str, Any]) -> tuple[str, bool]:
    candidate = payload.get("candidate", {})
    session = payload.get("session", {})
    documents = payload.get("candidate_documents", [])

    sections = [
        "[Session]",
        f"target_job: {session.get('target_job')}",
        f"difficulty_level: {session.get('difficulty_level')}",
        "",
        "[Candidate]",
        f"candidate_id: {candidate.get('candidate_id')}",
        f"name: {candidate.get('name')}",
        f"job_position: {candidate.get('job_position')}",
        f"apply_status: {candidate.get('apply_status')}",
    ]

    has_extracted_text = False
    remaining_chars = MAX_DOCUMENT_CHARS

    for document in documents:
        extracted_text = (document.get("extracted_text") or "").strip()
        if extracted_text:
            has_extracted_text = True
        if remaining_chars <= 0:
            break

        clipped = extracted_text[:remaining_chars]
        remaining_chars -= len(clipped)
        sections.extend(
            [
                "",
                "[Document]",
                f"document_id: {document.get('document_id')}",
                f"document_type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                f"extract_status: {document.get('extract_status')}",
                "extracted_text:",
                clipped or "(no extracted text)",
            ]
        )

    return "\n".join(sections), has_extracted_text


def _question_id(question: dict[str, Any], index: int) -> str:
    value = str(question.get("id") or "").strip()
    return value or f"q_{index + 1:03d}"


def _find_by_question_id(items: list[dict[str, Any]], question_id: str) -> dict[str, Any]:
    return next((item for item in items if item.get("question_id") == question_id), {})


def _fallback_review(question_id: str) -> ReviewResult:
    return ReviewResult(
        question_id=question_id,
        status="rejected",
        reason="질문 검토 결과가 없어 보수적으로 반려 처리했습니다.",
        reject_reason="review_missing",
    )


def _fallback_score(question_id: str) -> ScoreResult:
    return ScoreResult(
        question_id=question_id,
        score=0,
        score_reason="질문 점수 결과가 없어 0점으로 처리했습니다.",
        quality_flags=["SCORE_MISSING"],
    )


def _fallback_answer(question_id: str) -> PredictedAnswer:
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="문서 근거가 부족하여 현실적인 예상 답변을 생성하지 못했습니다.",
        predicted_answer_basis="predicted_answer_missing",
        answer_confidence="low",
        answer_risk_points=["ANSWER_MISSING"],
    )


def _fallback_follow_up(question_id: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="방금 답변하신 내용 중 본인이 직접 수행한 범위와 근거를 구체적으로 설명해주시겠어요?",
        follow_up_basis="follow_up_missing",
        drill_type="ROLE_VERIFICATION",
    )


async def build_state_node(state: AgentState) -> AgentState:
    payload = state.get("source_payload", {})
    candidate_text, has_extracted_text = _merge_document_text(payload)
    prompt_profile = payload.get("prompt_profile") or {}

    recruitment_criteria = {
        "prompt_profile_id": prompt_profile.get("id"),
        "profile_key": prompt_profile.get("profile_key"),
        "target_job": prompt_profile.get("target_job"),
        "system_prompt": prompt_profile.get("system_prompt"),
        "output_schema": prompt_profile.get("output_schema"),
        "has_prompt_profile": bool(prompt_profile),
        "has_extracted_text": has_extracted_text,
    }

    return {
        **state,
        "candidate_text": candidate_text,
        "recruitment_criteria": recruitment_criteria,
        "retry_count": state.get("retry_count", 0),
        "max_retry_count": state.get("max_retry_count", 3),
    }


async def analyzer_node(state: AgentState) -> AgentState:
    result = await _call_structured_output(
        system_prompt=prompts.ANALYZER_SYSTEM_PROMPT,
        user_prompt=prompts.ANALYZER_USER_PROMPT.format(
            candidate_text=state.get("candidate_text", ""),
            recruitment_criteria=_json(state.get("recruitment_criteria", {})),
        ),
        response_model=DocumentAnalysisOutput,
    )
    return {**state, "document_analysis": result.model_dump(mode="json")}


async def questioner_node(state: AgentState) -> AgentState:
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    existing_questions = state.get("questions", [])
    human_action = state.get("human_action")
    regen_ids = set(state.get("regen_question_ids") or [])

    profile_prompt = (state.get("recruitment_criteria") or {}).get("system_prompt")
    system_prompt = prompts.QUESTIONER_SYSTEM_PROMPT
    if profile_prompt:
        system_prompt = f"{profile_prompt}\n\n{system_prompt}"

    result = await _call_structured_output(
        system_prompt=system_prompt,
        user_prompt=prompts.QUESTIONER_USER_PROMPT.format(
            target_job=session.get("target_job"),
            difficulty_level=session.get("difficulty_level"),
            human_action=human_action,
            additional_instruction=state.get("additional_instruction"),
            regen_question_ids=list(regen_ids),
            candidate_text=state.get("candidate_text", ""),
            document_analysis=_json(state.get("document_analysis", {})),
            existing_questions=_json(existing_questions),
        ),
        response_model=QuestionerOutput,
    )

    new_questions = [
        question.model_dump(mode="json")
        for question in result.questions
    ]
    if human_action == "more_questions":
        questions = existing_questions + new_questions
    elif human_action == "regenerate_question" and regen_ids:
        replacements = {question["id"]: question for question in new_questions}
        questions = [
            replacements.get(question.get("id"), question)
            if question.get("id") in regen_ids
            else question
            for question in existing_questions
        ]
        missing_replacements = [
            question for question in new_questions if question.get("id") not in replacements
        ]
        questions.extend(missing_replacements)
    else:
        questions = new_questions

    normalized_questions = []
    for index, question in enumerate(questions):
        normalized_questions.append({**question, "id": _question_id(question, index)})

    return {**state, "questions": normalized_questions}


async def predictor_node(state: AgentState) -> AgentState:
    result = await _call_structured_output(
        system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
        user_prompt=prompts.PREDICTOR_USER_PROMPT.format(
            candidate_text=state.get("candidate_text", ""),
            document_analysis=_json(state.get("document_analysis", {})),
            questions=_json(state.get("questions", [])),
        ),
        response_model=PredictorOutput,
    )
    return {
        **state,
        "answers": [answer.model_dump(mode="json") for answer in result.answers],
    }


async def driller_node(state: AgentState) -> AgentState:
    result = await _call_structured_output(
        system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
        user_prompt=prompts.DRILLER_USER_PROMPT.format(
            questions=_json(state.get("questions", [])),
            answers=_json(state.get("answers", [])),
            document_analysis=_json(state.get("document_analysis", {})),
        ),
        response_model=DrillerOutput,
    )
    return {
        **state,
        "follow_ups": [
            follow_up.model_dump(mode="json")
            for follow_up in result.follow_ups
        ],
    }


async def reviewer_node(state: AgentState) -> AgentState:
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    result = await _call_structured_output(
        system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
        user_prompt=prompts.REVIEWER_USER_PROMPT.format(
            target_job=session.get("target_job"),
            recruitment_criteria=_json(state.get("recruitment_criteria", {})),
            questions=_json(state.get("questions", [])),
            answers=_json(state.get("answers", [])),
            follow_ups=_json(state.get("follow_ups", [])),
        ),
        response_model=ReviewerOutput,
    )
    return {
        **state,
        "reviews": [review.model_dump(mode="json") for review in result.reviews],
    }


async def scorer_node(state: AgentState) -> AgentState:
    result = await _call_structured_output(
        system_prompt=prompts.SCORER_SYSTEM_PROMPT,
        user_prompt=prompts.SCORER_USER_PROMPT.format(
            questions=_json(state.get("questions", [])),
            answers=_json(state.get("answers", [])),
            follow_ups=_json(state.get("follow_ups", [])),
            reviews=_json(state.get("reviews", [])),
        ),
        response_model=ScorerOutput,
    )

    scores = [score.model_dump(mode="json") for score in result.scores]
    reviews = state.get("reviews", [])
    approved_count = sum(1 for review in reviews if review.get("status") == "approved")
    rejected_count = sum(1 for review in reviews if review.get("status") == "rejected")
    avg_score = (
        sum(score.get("score", 0) for score in scores) / len(scores)
        if scores
        else 0
    )
    quality_issues = sorted(
        {
            flag
            for score in scores
            for flag in score.get("quality_flags", [])
        }
    )

    return {
        **state,
        "scores": scores,
        "review_summary": {
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "avg_score": round(avg_score, 2),
            "quality_issues": quality_issues,
        },
    }


async def increment_retry_for_questioner_node(state: AgentState) -> AgentState:
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "router_decision": "questioner",
    }


async def increment_retry_for_driller_node(state: AgentState) -> AgentState:
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "router_decision": "driller",
    }


async def selector_node(state: AgentState) -> AgentState:
    questions = state.get("questions", [])
    reviews_by_id = {
        review.get("question_id"): review
        for review in state.get("reviews", [])
    }
    scores_by_id = {
        score.get("question_id"): score
        for score in state.get("scores", [])
    }

    unique_questions: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for question in questions:
        text_key = " ".join(str(question.get("question_text", "")).split()).lower()
        if not text_key or text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        unique_questions.append(question)

    sorted_questions = sorted(
        unique_questions,
        key=lambda question: (
            reviews_by_id.get(question.get("id"), {}).get("status") == "approved",
            scores_by_id.get(question.get("id"), {}).get("score", 0),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    used_categories: set[str] = set()

    risk_question = next(
        (
            question
            for question in sorted_questions
            if question.get("category") == "RISK"
        ),
        None,
    )
    if risk_question:
        selected.append(risk_question)
        used_categories.add(str(risk_question.get("category")))

    for question in sorted_questions:
        if len(selected) >= 5:
            break
        if question in selected:
            continue
        category = str(question.get("category"))
        if category in used_categories and len(selected) < 3:
            continue
        selected.append(question)
        used_categories.add(category)

    for question in sorted_questions:
        if len(selected) >= 5:
            break
        if question not in selected:
            selected.append(question)

    return {
        **state,
        "selected_questions": selected,
        "router_decision": state.get("router_decision") or "selector",
    }


async def final_formatter_node(state: AgentState) -> AgentState:
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    candidate = payload.get("candidate", {})
    selected_questions = state.get("selected_questions", [])
    answers = state.get("answers", [])
    follow_ups = state.get("follow_ups", [])
    reviews = state.get("reviews", [])
    scores = state.get("scores", [])

    items: list[InterviewQuestionItem] = []
    for index, question in enumerate(selected_questions):
        question_id = _question_id(question, index)
        answer = PredictedAnswer.model_validate(
            _find_by_question_id(answers, question_id) or _fallback_answer(question_id)
        )
        follow_up = FollowUpQuestion.model_validate(
            _find_by_question_id(follow_ups, question_id)
            or _fallback_follow_up(question_id)
        )
        review = ReviewResult.model_validate(
            _find_by_question_id(reviews, question_id) or _fallback_review(question_id)
        )
        score = ScoreResult.model_validate(
            _find_by_question_id(scores, question_id) or _fallback_score(question_id)
        )
        question_model = QuestionCandidate.model_validate(question)

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
                score=score.score,
                score_reason=score.score_reason,
            )
        )

    analysis = DocumentAnalysisOutput.model_validate(
        state.get("document_analysis")
        or {
            "job_fit": "분석 결과가 없어 직무 적합성을 판단하지 못했습니다.",
        }
    )
    has_extracted_text = (state.get("recruitment_criteria") or {}).get(
        "has_extracted_text",
        False,
    )
    approved_count = sum(1 for item in items if item.review.status == "approved")
    is_partial = (
        not has_extracted_text
        or len(items) < 5
        or approved_count < 5
        or state.get("retry_count", 0) >= state.get("max_retry_count", 3)
    )

    response = QuestionGenerationResponse(
        session_id=session.get("session_id"),
        candidate_id=candidate.get("candidate_id"),
        target_job=session.get("target_job"),
        difficulty_level=session.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=analysis,
        questions=items,
        generation_metadata={
            "total_candidate_questions": len(state.get("questions", [])),
            "selected_question_count": len(items),
            "retry_count": state.get("retry_count", 0),
            "router_decision": state.get("router_decision", "selector"),
            "is_all_approved": bool(items) and approved_count == len(items),
            "review_summary": state.get("review_summary", {}),
        },
    )

    return {**state, "final_response": response.model_dump(mode="json")}
