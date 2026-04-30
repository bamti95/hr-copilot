from __future__ import annotations

import json
import logging
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field

from ai.interview_graph.llm_usage import call_structured_output_with_usage
from ai.interview_graph.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
from schemas.session_generation import CandidateInterviewPrepInput

from . import prompts
from .state import AgentState, QuestionSet

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _merge_candidate_text(payload: CandidateInterviewPrepInput, max_chars: int = 18000) -> str:
    sections = [
        f"candidate_id: {payload.candidate.candidate_id}",
        f"name: {payload.candidate.name}",
        f"target_job: {payload.session.target_job}",
        f"difficulty_level: {payload.session.difficulty_level}",
        "",
    ]

    remaining = max_chars
    for doc in payload.candidate_documents:
        if remaining <= 0:
            break
        extracted = (doc.extracted_text or "").strip()
        clipped = extracted[:remaining]
        remaining -= len(clipped)
        sections.extend(
            [
                "[Document]",
                f"document_id: {doc.document_id}",
                f"document_type: {doc.document_type}",
                f"title: {doc.title}",
                f"extract_status: {doc.extract_status}",
                "extracted_text:",
                clipped or "(no extracted text)",
                "",
            ]
        )
    return "\n".join(sections).strip()


def _recruitment_criteria(payload: CandidateInterviewPrepInput) -> str:
    if payload.prompt_profile and payload.prompt_profile.system_prompt:
        return payload.prompt_profile.system_prompt
    return f"target_job: {payload.session.target_job}"


async def _call_structured_output(
    *,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> tuple[T, list[dict[str, Any]]]:
    return await call_structured_output_with_usage(
        node_name=node_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=response_model,
    )


class _QuestionItem(BaseModel):
    generation_basis: str
    document_evidence: list[str] = Field(default_factory=list)
    question_text: str
    evaluation_guide: str


class _QuestionerOutput(BaseModel):
    questions: list[_QuestionItem] = Field(default_factory=list)


class _PredictorItem(BaseModel):
    id: str
    predicted_answer: str


class _PredictorOutput(BaseModel):
    answers: list[_PredictorItem] = Field(default_factory=list)


class _DrillerItem(BaseModel):
    id: str
    follow_up_question: str


class _DrillerOutput(BaseModel):
    follow_ups: list[_DrillerItem] = Field(default_factory=list)


class _ReviewDecision(BaseModel):
    id: str
    status: Literal["approved", "rejected"]
    reason: str
    reject_reason: str = ""
    recommended_revision: str = ""
    quality_flags: list[str] = Field(default_factory=list)
    duplicate_with: str = ""
    score: int = 0
    score_reason: str = ""


class _ReviewerOutput(BaseModel):
    decisions: list[_ReviewDecision] = Field(default_factory=list)


def _normalize_flags(value: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in value or []:
        label = str(item).strip()
        if not label:
            continue
        normalized.append(label.upper().replace(" ", "_"))
    return normalized


def _default_question_state(question_id: str) -> QuestionSet:
    return {
        "id": question_id,
        "generation_basis": "",
        "document_evidence": [],
        "question_text": "",
        "evaluation_guide": "",
        "predicted_answer": "",
        "follow_up_question": "",
        "status": "pending",
        "review_reason": "",
        "reject_reason": "",
        "recommended_revision": "",
        "quality_flags": [],
        "duplicate_with": "",
        "score": 0,
        "score_reason": "",
        "regen_targets": [],
    }


async def build_state_node(state: AgentState) -> AgentState:
    payload: CandidateInterviewPrepInput = state["_payload"]

    base_questions: list[QuestionSet] = []
    for idx, existing in enumerate(payload.existing_questions or []):
        question_id = str(existing.get("id") or f"q_{idx + 1:03d}")
        question = _default_question_state(question_id)
        question["generation_basis"] = str(existing.get("generation_basis") or "")
        question["document_evidence"] = [str(item) for item in (existing.get("document_evidence") or [])]
        question["question_text"] = str(existing.get("question_text") or "")
        question["evaluation_guide"] = str(existing.get("evaluation_guide") or "")
        question["predicted_answer"] = str(existing.get("predicted_answer") or "")
        question["follow_up_question"] = str(existing.get("follow_up_question") or "")
        question["review_reason"] = str(existing.get("review_reason") or existing.get("review_reason_text") or "")
        question["reject_reason"] = str(existing.get("reject_reason") or "")
        question["recommended_revision"] = str(existing.get("recommended_revision") or "")
        question["quality_flags"] = _normalize_flags(list(existing.get("quality_flags") or []))
        question["duplicate_with"] = str(existing.get("duplicate_with") or "")
        question["score"] = int(existing.get("score") or 0)
        question["score_reason"] = str(existing.get("score_reason") or "")
        base_questions.append(question)

    return {
        "candidate_text": _merge_candidate_text(payload),
        "recruitment_criteria": _recruitment_criteria(payload),
        "questions": base_questions,
        "retry_count": 0,
        "max_retry_count": 3,
        "is_all_approved": False,
        "human_action": payload.human_action,
        "additional_instruction": payload.additional_instruction,
        "regen_question_ids": payload.target_question_ids or None,
        "node_warnings": [],
        "llm_usages": [],
    }


async def questioner_node(state: AgentState) -> AgentState:
    instruction = state.get("additional_instruction") or ""

    if state.get("human_action") == "more":
        instruction = (instruction + "\n\n기존 질문과 의도가 겹치지 않게 추가 질문을 만드세요.").strip()
    elif state.get("human_action") == "regenerate_all":
        state["questions"] = []
    elif state.get("human_action") in {"regenerate_partial", "regenerate_question"}:
        regen_ids = set(state.get("regen_question_ids") or [])
        if regen_ids:
            state["questions"] = [q for q in state.get("questions", []) if q.get("id") not in regen_ids]

    # Retry 시에는 이전 반려 사유를 구조적으로 다시 주입해서 같은 실수를 막는다.
    if state.get("retry_count", 0) > 0:
        rejected = [q for q in state.get("questions", []) if q.get("status") == "rejected"][:10]
        if rejected:
            feedback_lines: list[str] = []
            for q in rejected:
                question_id = str(q.get("id") or "")
                review_reason = str(q.get("review_reason") or "").strip()
                reject_reason = str(q.get("reject_reason") or "").strip()
                recommended = str(q.get("recommended_revision") or "").strip()
                flags = ", ".join([str(flag) for flag in (q.get("quality_flags") or []) if flag])

                line = f"- {question_id}: {review_reason or reject_reason}"
                if flags:
                    line += f" | flags={flags}"
                if recommended:
                    line += f" | 수정지침={recommended}"
                feedback_lines.append(line)

            instruction = (
                instruction
                + "\n\n[이전 라운드 반려 피드백 - 같은 실수 금지]\n"
                + "\n".join(feedback_lines)
            ).strip()

    count = 5 if not state.get("questions") else 3
    user_prompt = prompts.QUESTIONER_USER.format(
        candidate_text=state.get("candidate_text", ""),
        recruitment_criteria=state.get("recruitment_criteria", ""),
        instruction=instruction or "(none)",
        count=count,
    )
    output, usages = await _call_structured_output(
        node_name="HY_questioner",
        system_prompt=prompts.QUESTIONER_SYSTEM,
        user_prompt=user_prompt,
        response_model=_QuestionerOutput,
    )

    existing = state.get("questions", [])
    start_idx = len(existing)
    for index, item in enumerate(output.questions):
        question_id = f"q_{start_idx + index + 1:03d}"
        question = _default_question_state(question_id)
        question["generation_basis"] = item.generation_basis.strip()
        question["document_evidence"] = [str(evidence).strip() for evidence in item.document_evidence if str(evidence).strip()]
        question["question_text"] = item.question_text.strip()
        question["evaluation_guide"] = item.evaluation_guide.strip()
        existing.append(question)

    return {"questions": existing, "llm_usages": usages}


async def predictor_node(state: AgentState) -> AgentState:
    questions = state.get("questions", [])
    if not questions:
        return {}

    user_prompt = prompts.PREDICTOR_USER.format(
        candidate_text=state.get("candidate_text", ""),
        questions_json=_json(
            [{"id": q.get("id"), "question_text": q.get("question_text")} for q in questions]
        ),
    )
    output, usages = await _call_structured_output(
        node_name="HY_predictor",
        system_prompt=prompts.PREDICTOR_SYSTEM,
        user_prompt=user_prompt,
        response_model=_PredictorOutput,
    )

    answer_by_id = {item.id: item.predicted_answer for item in output.answers}
    for question in questions:
        question_id = str(question.get("id"))
        if question_id in answer_by_id:
            question["predicted_answer"] = answer_by_id[question_id].strip()

    return {"questions": questions, "llm_usages": usages}


async def driller_node(state: AgentState) -> AgentState:
    questions = state.get("questions", [])
    if not questions:
        return {}

    user_prompt = prompts.DRILLER_USER.format(
        candidate_text=state.get("candidate_text", ""),
        questions_json=_json(
            [
                {
                    "id": q.get("id"),
                    "question_text": q.get("question_text"),
                    "predicted_answer": q.get("predicted_answer"),
                }
                for q in questions
            ]
        ),
    )
    output, usages = await _call_structured_output(
        node_name="HY_driller",
        system_prompt=prompts.DRILLER_SYSTEM,
        user_prompt=user_prompt,
        response_model=_DrillerOutput,
    )

    follow_by_id = {item.id: item.follow_up_question for item in output.follow_ups}
    for question in questions:
        question_id = str(question.get("id"))
        if question_id in follow_by_id:
            question["follow_up_question"] = follow_by_id[question_id].strip()

    return {"questions": questions, "llm_usages": usages}


async def reviewer_node(state: AgentState) -> AgentState:
    questions = state.get("questions", [])
    if not questions:
        return {"is_all_approved": True}

    user_prompt = prompts.REVIEWER_USER.format(
        recruitment_criteria=state.get("recruitment_criteria", ""),
        questions_json=_json(questions),
    )
    output, usages = await _call_structured_output(
        node_name="HY_reviewer",
        system_prompt=prompts.REVIEWER_SYSTEM,
        user_prompt=user_prompt,
        response_model=_ReviewerOutput,
    )

    decision_by_id = {decision.id: decision for decision in output.decisions}
    rejected_ids: list[str] = []

    for question in questions:
        question_id = str(question.get("id"))
        decision = decision_by_id.get(question_id)
        if decision is None:
            continue

        question["status"] = decision.status
        question["review_reason"] = decision.reason.strip()
        question["reject_reason"] = decision.reject_reason.strip()
        question["recommended_revision"] = decision.recommended_revision.strip()
        question["quality_flags"] = _normalize_flags(list(decision.quality_flags or []))
        question["duplicate_with"] = decision.duplicate_with.strip()
        question["score"] = max(0, min(100, int(decision.score or 0)))
        question["score_reason"] = decision.score_reason.strip()

        if decision.status == "approved":
            question["regen_targets"] = []
        else:
            question["regen_targets"] = ["question_text", "generation_basis", "evaluation_guide", "document_evidence"]
            rejected_ids.append(question_id)

    is_all_approved = all(q.get("status") == "approved" for q in questions) if questions else True
    return {
        "questions": questions,
        "is_all_approved": is_all_approved,
        "llm_usages": usages,
        "regen_question_ids": rejected_ids or None,
    }


def route_after_review(state: AgentState) -> str:
    if state.get("is_all_approved"):
        return "final"
    if (state.get("retry_count") or 0) >= (state.get("max_retry_count") or 3):
        return "final"
    return "retry"


async def increment_retry_node(state: AgentState) -> AgentState:
    return {"retry_count": int(state.get("retry_count") or 0) + 1}


async def final_formatter_node(state: AgentState) -> AgentState:
    payload: CandidateInterviewPrepInput = state["_payload"]

    analysis = DocumentAnalysisOutput(
        job_fit="HY graph analysis is derived from question generation and reviewer scoring.",
        strengths=[],
        weaknesses=[],
        risks=[],
        document_evidence=[],
        questionable_points=[],
    )

    items: list[dict[str, Any]] = []
    for question in state.get("questions", []):
        items.append(
            {
                "id": question.get("id") or "",
                "category": "OTHER",
                "question_text": question.get("question_text") or "",
                "generation_basis": question.get("generation_basis") or "",
                "document_evidence": question.get("document_evidence") or [],
                "evaluation_guide": question.get("evaluation_guide") or "",
                "predicted_answer": question.get("predicted_answer") or "",
                "predicted_answer_basis": "",
                "follow_up_question": question.get("follow_up_question") or "",
                "follow_up_basis": "",
                "risk_tags": question.get("quality_flags") or [],
                "competency_tags": [],
                "review": {
                    "question_id": question.get("id") or "",
                    "status": "approved" if question.get("status") == "approved" else "rejected",
                    "reason": question.get("review_reason") or "",
                    "reject_reason": question.get("reject_reason") or "",
                    "recommended_revision": question.get("recommended_revision") or "",
                },
                "score": int(question.get("score") or 0),
                "score_reason": question.get("score_reason") or "",
            }
        )

    status = "completed" if state.get("is_all_approved") else "partial_completed"
    response = QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status=status,
        analysis_summary=analysis,
        questions=[],
        generation_metadata={
            "retry_count": state.get("retry_count", 0),
            "is_all_approved": bool(state.get("is_all_approved")),
        },
    ).model_dump(mode="json")
    response["questions"] = items

    return {"final_response": response}
