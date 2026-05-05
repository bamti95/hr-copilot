"""LangGraph node implementations for the JH interview graph."""

from __future__ import annotations

import logging
from typing import Any

from ai.interview_graph_JH import prompts
from ai.interview_graph_JH.config import MAX_QUESTION_TEXT_CHARS, PREDICTOR_DOCUMENT_CHARS
from ai.interview_graph_JH.content_utils import (
    clip_follow_up_text,
    clip_text,
    normalize_document_evidence,
    normalize_evaluation_guide,
    normalize_follow_up_question,
    normalize_predicted_answer,
)
from ai.interview_graph_JH.llm_usage import (
    StructuredOutputCallError,
    call_structured_output_with_usage,
)
from ai.interview_graph_JH.question_utils import (
    allocate_question_id,
    build_question_entry,
    default_regen_targets,
    difficulty_guidance,
    ensure_question_ids,
    format_questions,
    merge_document_text,
    question_id,
    questioner_mode,
    recruitment_criteria,
    requested_question_count,
    selected_questions_for_output,
    select_top_questions,
    should_refresh_follow_up,
    should_refresh_predicted_answer,
    task_instruction,
    is_approved_question,
)
from ai.interview_graph_JH.review_utils import (
    analysis_summary,
    calculate_average,
    canonical_retry_guidance,
    fallback_answer,
    fallback_follow_up,
    fallback_review,
    infer_requested_revision_fields,
    normalize_review_issue_types,
    normalize_reviewer_status,
    score_reason,
    soften_issue_types_for_interview_depth,
)
from ai.interview_graph_JH.schemas import (
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
from ai.interview_graph_JH.state import AgentState, QuestionSet

logger = logging.getLogger(__name__)


def _append_runtime_data(
    state: AgentState,
    *,
    usages: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    update: dict[str, Any] = {}
    if usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + list(usages)
    if warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + list(warnings)
    return update


def _question_lookup(questions: list[QuestionSet]) -> dict[str, QuestionSet]:
    return {str(item["id"]): item for item in questions if item.get("id")}


def _next_question_counter(questions: list[QuestionSet]) -> tuple[set[str], list[int]]:
    used_ids = {str(item.get("id")) for item in questions if item.get("id")}
    max_seen = 0
    for current_id in used_ids:
        if not current_id.startswith("q-"):
            continue
        try:
            max_seen = max(max_seen, int(current_id.removeprefix("q-")))
        except ValueError:
            continue
    return used_ids, [max_seen]


def _apply_partial_rewrite(existing: QuestionSet, patched: QuestionSet, requested_fields: list[str]) -> None:
    patch_fields = set(requested_fields)
    for field_name in ("question_text", "evaluation_guide", "generation_basis"):
        if field_name not in patch_fields:
            patched[field_name] = existing.get(field_name, patched[field_name])
    if "document_evidence" not in patch_fields:
        patched["document_evidence"] = list(existing.get("document_evidence") or [])
    if "category" not in patch_fields:
        patched["category"] = existing.get("category", patched["category"])
    if "predicted_answer" not in patch_fields:
        patched["predicted_answer"] = existing.get("predicted_answer", "")
        patched["predicted_answer_basis"] = existing.get("predicted_answer_basis", "")
        patched["answer_confidence"] = existing.get("answer_confidence", "")
        patched["answer_risk_points"] = list(existing.get("answer_risk_points") or [])
    if "follow_up_question" not in patch_fields:
        patched["follow_up_question"] = existing.get("follow_up_question", "")
        patched["follow_up_basis"] = existing.get("follow_up_basis", "")
        patched["drill_type"] = existing.get("drill_type", "")


def _clear_retry_state(question: QuestionSet) -> None:
    question["regen_targets"] = []
    question["requested_revision_fields"] = []
    question["retry_issue_types"] = []
    question["retry_guidance"] = ""


def _mark_review_failure(questions: list[QuestionSet], retry_limit: int) -> dict[str, Any]:
    for item in questions:
        if item.get("status") not in {"pending", "human_rejected", "needs_revision", "rejected"}:
            continue
        item["status"] = "needs_revision"
        item["review_status"] = "needs_revision"
        item["review_reason"] = "Reviewer 호출에 실패해 질문을 다시 검토해야 합니다."
        item["reject_reason"] = "Reviewer 실행 실패"
        item["recommended_revision"] = "프롬프트 형식과 입력 길이를 확인한 뒤 다시 검토해 주세요."
        item["requested_revision_fields"] = ["question_text", "evaluation_guide"]
        item["review_issue_types"] = ["review_execution_failure"]
        item["retry_issue_types"] = ["review_execution_failure"]
        item["retry_guidance"] = item["recommended_revision"]
        item["regen_targets"] = ["question_text", "evaluation_guide"]
    return {
        "questions": questions,
        "retry_count": retry_limit,
        "is_all_approved": False,
    }


def _fallback_question_item(question: QuestionSet, index: int) -> InterviewQuestionItem:
    current_question_id = question_id(question, index)
    question_model = QuestionCandidate.model_validate(
        {
            "id": current_question_id,
            "category": question.get("category") or "OTHER",
            "question_text": question.get("question_text") or "",
            "generation_basis": question.get("generation_basis") or "",
            "document_evidence": normalize_document_evidence(question.get("document_evidence") or []),
            "evaluation_guide": normalize_evaluation_guide(question.get("evaluation_guide") or ""),
            "risk_tags": question.get("risk_tags") or [],
            "competency_tags": question.get("competency_tags") or [],
        }
    )
    answer = fallback_answer(current_question_id)
    if question.get("predicted_answer"):
        answer = PredictedAnswer.model_validate(
            {
                "question_id": current_question_id,
                "predicted_answer": normalize_predicted_answer(question.get("predicted_answer") or ""),
                "predicted_answer_basis": question.get("predicted_answer_basis") or answer.predicted_answer_basis,
                "answer_confidence": question.get("answer_confidence") or answer.answer_confidence,
                "answer_risk_points": question.get("answer_risk_points") or answer.answer_risk_points,
            }
        )
    follow_up = fallback_follow_up(current_question_id)
    if question.get("follow_up_question"):
        follow_up = FollowUpQuestion.model_validate(
            {
                "question_id": current_question_id,
                "follow_up_question": clip_follow_up_text(question.get("follow_up_question") or ""),
                "follow_up_basis": question.get("follow_up_basis") or follow_up.follow_up_basis,
                "drill_type": question.get("drill_type") or follow_up.drill_type,
            }
        )
    review = fallback_review(current_question_id)
    if question.get("review_status"):
        review = ReviewResult.model_validate(
            {
                "question_id": current_question_id,
                "status": question.get("review_status") or "needs_revision",
                "reason": question.get("review_reason") or review.reason,
                "reject_reason": question.get("reject_reason") or "",
                "recommended_revision": question.get("recommended_revision") or "",
                "issue_types": question.get("review_issue_types") or [],
                "requested_revision_fields": question.get("requested_revision_fields") or [],
                "question_quality_scores": question.get("question_quality_scores") or {},
                "evaluation_guide_scores": question.get("evaluation_guide_scores") or {},
                "question_quality_average": question.get("question_quality_average") or 0.0,
                "evaluation_guide_average": question.get("evaluation_guide_average") or 0.0,
                "overall_score": question.get("score") or 0.0,
            }
        )

    return InterviewQuestionItem(
        id=current_question_id,
        category=question_model.category,
        question_text=question_model.question_text,
        generation_basis=question_model.generation_basis,
        document_evidence=question_model.document_evidence,
        evaluation_guide=question_model.evaluation_guide,
        predicted_answer=answer.predicted_answer,
        predicted_answer_basis=answer.predicted_answer_basis,
        answer_confidence=answer.answer_confidence,
        answer_risk_points=answer.answer_risk_points,
        follow_up_question=follow_up.follow_up_question,
        follow_up_basis=follow_up.follow_up_basis,
        drill_type=follow_up.drill_type,
        risk_tags=question_model.risk_tags,
        competency_tags=question_model.competency_tags,
        review=review,
        score=float(question.get("score") or 0.0),
        score_reason=question.get("score_reason") or "Reviewer 점수 사유가 비어 있습니다.",
    )


async def prepare_context_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions") or [])
    ensure_question_ids(questions)

    update: dict[str, Any] = {"questions": questions}
    if not state.get("candidate_context"):
        update["candidate_context"] = merge_document_text(state)
    return update


async def questioner_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions") or [])
    ensure_question_ids(questions)
    mode, targets = questioner_mode(state, questions)

    update: dict[str, Any] = {
        "human_action": None,
        "additional_instruction": None,
        "target_question_ids": [],
        "generation_mode": mode,
    }
    if mode in {"rewrite", "partial_rewrite"}:
        update["retry_count"] = state.get("retry_count", 0) + 1

    user_prompt = prompts.QUESTIONER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=difficulty_guidance(state),
        recruitment_criteria=recruitment_criteria(state),
        candidate_context=state.get("candidate_context") or "",
        mode=mode,
        additional_instruction=state.get("additional_instruction") or "(없음)",
        existing_questions=format_questions(questions, include_answer=True),
        retry_feedback=format_questions(targets, include_answer=True),
        task_instruction=task_instruction(mode, targets),
        question_text_limit=MAX_QUESTION_TEXT_CHARS,
    )

    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="questioner",
            system_prompt=prompts.QUESTIONER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=QuestionerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "questioner", "message": str(exc)})
        update["questions"] = questions
        update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
        return update

    by_id = _question_lookup(questions)
    should_append = mode in {"initial", "more", "add_question"}
    used_ids, id_counter = _next_question_counter(questions)
    target_ids = [str(item.get("id") or "") for item in targets]
    target_regen_map = {str(item.get("id") or ""): default_regen_targets(item) for item in targets}

    for index, question in enumerate(parsed.questions):
        model = question.model_dump(mode="json")
        if should_append:
            new_id = allocate_question_id(used_ids, id_counter)
            entry = build_question_entry(model, question_id=new_id, generation_mode=mode)
            questions.append(entry)
            by_id[new_id] = entry
            continue

        llm_id = str(model.get("id") or "")
        fallback_id = target_ids[index] if index < len(target_ids) else ""
        current_id = llm_id if llm_id in by_id else fallback_id
        if not current_id or current_id not in by_id:
            new_warnings.append(
                {
                    "node": "questioner",
                    "message": f"재작성 응답을 기존 질문 id에 매핑하지 못했습니다. (llm_id={llm_id or '없음'})",
                }
            )
            continue

        existing = by_id[current_id]
        requested_fields = target_regen_map.get(current_id, [])
        patched = build_question_entry(
            model,
            question_id=current_id,
            generation_mode=mode,
            existing=existing,
            requested_fields=requested_fields,
        )

        if mode == "partial_rewrite" and requested_fields:
            _apply_partial_rewrite(existing, patched, requested_fields)
        _clear_retry_state(patched)

        existing.update(patched)

    update["questions"] = questions
    update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
    return update


async def predictor_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision"}
        and should_refresh_predicted_answer(item)
    ]
    if not targets:
        return {}

    user_prompt = prompts.PREDICTOR_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=difficulty_guidance(state),
        candidate_context=clip_text(state.get("candidate_context") or "", PREDICTOR_DOCUMENT_CHARS),
        questions=format_questions(targets),
        retry_feedback=format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="predictor",
            system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PredictorOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "predictor", "message": str(exc)})
        return _append_runtime_data(state, usages=new_usages, warnings=new_warnings)

    by_id = _question_lookup(questions)
    for answer in parsed.answers:
        model = answer.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["predicted_answer"] = normalize_predicted_answer(
            model.get("predicted_answer") or "",
            issue_types=[
                str(item)
                for item in (
                    target.get("retry_issue_types")
                    or target.get("review_issue_types")
                    or []
                )
            ],
            evidence=normalize_document_evidence(target.get("document_evidence") or []),
        )
        target["predicted_answer_basis"] = model.get("predicted_answer_basis") or ""
        target["answer_confidence"] = model.get("answer_confidence") or ""
        target["answer_risk_points"] = list(model.get("answer_risk_points") or [])

    update: dict[str, Any] = {"questions": questions}
    update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
    return update


async def driller_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision"}
        and item.get("predicted_answer")
        and should_refresh_follow_up(item)
    ]
    if not targets:
        return {}

    user_prompt = prompts.DRILLER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=difficulty_guidance(state),
        recruitment_criteria=recruitment_criteria(state),
        questions=format_questions(targets, include_answer=True),
        retry_feedback=format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="driller",
            system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DrillerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "driller", "message": str(exc)})
        return _append_runtime_data(state, usages=new_usages, warnings=new_warnings)

    by_id = _question_lookup(questions)
    for follow_up in parsed.follow_ups:
        model = follow_up.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["follow_up_question"] = normalize_follow_up_question(
            model.get("follow_up_question") or "",
            target,
        )
        target["follow_up_basis"] = model.get("follow_up_basis") or ""
        target["drill_type"] = model.get("drill_type") or ""

    update: dict[str, Any] = {"questions": questions}
    update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
    return update


async def reviewer_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision", "rejected"}
    ]
    if not targets:
        return {
            "is_all_approved": bool(questions) and all(item.get("status") == "approved" for item in questions)
        }

    user_prompt = prompts.REVIEWER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=difficulty_guidance(state),
        recruitment_criteria=recruitment_criteria(state),
        questions=format_questions(targets, include_answer=True, include_retry_feedback=False),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="reviewer",
            system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ReviewerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "reviewer", "message": str(exc)})
        failure_update = _mark_review_failure(questions, state.get("max_retry_count", 3))
        failure_update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
        return failure_update

    by_id = _question_lookup(questions)
    for review in parsed.reviews:
        model = review.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue

        question_scores = {
            key: int(value)
            for key, value in dict(model.get("question_quality_scores") or {}).items()
        }
        guide_scores = {
            key: int(value)
            for key, value in dict(model.get("evaluation_guide_scores") or {}).items()
        }
        question_avg = model.get("question_quality_average") or calculate_average(
            question_scores,
            [
                "job_relevance",
                "document_grounding",
                "validation_power",
                "specificity",
                "distinctiveness",
                "interview_usability",
                "core_resume_coverage",
            ],
        )
        guide_avg = model.get("evaluation_guide_average") or calculate_average(
            guide_scores,
            [
                "guide_alignment",
                "signal_clarity",
                "good_bad_answer_separation",
                "practical_usability",
                "verification_specificity",
            ],
        )
        overall_score = model.get("overall_score") or round((question_avg * 0.6) + (guide_avg * 0.4), 2)
        raw_requested_fields = [str(item) for item in model.get("requested_revision_fields") or []]
        inferred_fields = infer_requested_revision_fields(
            [str(item) for item in model.get("issue_types") or []],
            raw_requested_fields,
        )
        issue_types = normalize_review_issue_types(
            [str(item) for item in model.get("issue_types") or []],
            inferred_fields,
        )
        issue_types = soften_issue_types_for_interview_depth(target, issue_types)
        status = normalize_reviewer_status(
            str(model.get("status") or ""),
            float(question_avg),
            float(guide_avg),
            float(overall_score),
            issue_types,
        )

        target["review_status"] = status
        target["review_reason"] = model.get("reason") or ""
        target["reject_reason"] = model.get("reject_reason") or ""
        target["recommended_revision"] = model.get("recommended_revision") or ""
        target["review_issue_types"] = issue_types
        target["requested_revision_fields"] = inferred_fields
        target["retry_guidance"] = canonical_retry_guidance(issue_types, inferred_fields, target)
        target["question_quality_scores"] = question_scores
        target["evaluation_guide_scores"] = guide_scores
        target["question_quality_average"] = float(question_avg)
        target["evaluation_guide_average"] = float(guide_avg)
        target["score"] = float(overall_score)
        target["score_reason"] = target["review_reason"] or score_reason(question_scores, guide_scores)
        target["status"] = status

        if status == "needs_revision" and not target["requested_revision_fields"]:
            target["requested_revision_fields"] = ["question_text", "evaluation_guide"]
        if status != "approved":
            target["regen_targets"] = list(target.get("requested_revision_fields") or [])
            target["retry_issue_types"] = list(target.get("review_issue_types") or [])
        else:
            _clear_retry_state(target)

    selected = select_top_questions(questions, limit=requested_question_count(state))
    update: dict[str, Any] = {
        "questions": questions,
        "is_all_approved": bool(selected) and all(item.get("status") == "approved" for item in selected),
    }
    update.update(_append_runtime_data(state, usages=new_usages, warnings=new_warnings))
    return update


def review_router(state: AgentState) -> str:
    selected_questions = selected_questions_for_output(state)
    retryable_statuses = {"needs_revision", "rejected"}
    has_retryable = any(item.get("status") in retryable_statuses for item in selected_questions)
    enough_approved = (
        sum(1 for item in selected_questions if is_approved_question(item))
        >= requested_question_count(state)
    )
    if enough_approved:
        return "end"
    if has_retryable and state.get("retry_count", 0) < state.get("max_retry_count", 3):
        return "retry"
    return "end"


def build_response(state: AgentState) -> QuestionGenerationResponse:
    selected_questions = selected_questions_for_output(state)
    items = [_fallback_question_item(question, index) for index, question in enumerate(selected_questions)]

    approved_count = sum(1 for item in items if item.review.status == "approved")
    all_approved = bool(items) and approved_count == len(items)
    hit_retry_limit = state.get("retry_count", 0) >= state.get("max_retry_count", 3)
    generation_mode = state.get("generation_mode") or "initial"
    requested_count = requested_question_count(state)
    enough_questions = (
        len(items) >= requested_count
        if generation_mode in {"initial", "more", "add_question"}
        else bool(items)
    )
    is_partial = not enough_questions or not all_approved or hit_retry_limit

    return QuestionGenerationResponse(
        session_id=state.get("session_id"),
        candidate_id=state.get("candidate_id"),
        target_job=state.get("target_job") or "",
        difficulty_level=state.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=analysis_summary(state),
        questions=items,
        generation_metadata={
            "pipeline": "interview_graph_JH",
            "generation_mode": generation_mode,
            "total_candidate_questions": len(state.get("questions", [])),
            "selected_question_count": len(items),
            "approved_selected_question_count": approved_count,
            "requested_question_count": requested_count,
            "retry_count": state.get("retry_count", 0),
            "is_all_approved": all_approved,
            "node_warnings": state.get("node_warnings", []),
            "graph": "PrepareContext -> Questioner -> Predictor -> Driller -> Reviewer -> Selector",
        },
    )
