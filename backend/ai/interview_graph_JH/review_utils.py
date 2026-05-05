"""Review and fallback helpers for the JH interview graph."""

from __future__ import annotations

from ai.interview_graph_JH.config import EVALUATION_GUIDE_KEYS, QUESTION_QUALITY_KEYS
from ai.interview_graph_JH.schemas import (
    DocumentAnalysisOutput,
    EvaluationGuideRubric,
    FollowUpQuestion,
    PredictedAnswer,
    QuestionQualityRubric,
    ReviewResult,
)
from ai.interview_graph_JH.state import AgentState, QuestionSet
from ai.interview_graph_JH.question_utils import selected_questions_for_output


def normalize_review_issue_types(issue_types: list[str], requested_fields: list[str]) -> list[str]:
    del requested_fields
    normalized: list[str] = []
    for issue_type in issue_types:
        if issue_type not in normalized:
            normalized.append(issue_type)
    return normalized


def calculate_average(scores: dict[str, int], expected_keys: list[str]) -> float:
    values = [max(1, min(5, int(scores[key]))) for key in expected_keys if key in scores]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def score_reason(question_scores: dict[str, int], guide_scores: dict[str, int]) -> str:
    q_avg = calculate_average(question_scores, QUESTION_QUALITY_KEYS)
    g_avg = calculate_average(guide_scores, EVALUATION_GUIDE_KEYS)
    return f"question_quality_avg={q_avg}, evaluation_guide_avg={g_avg}"


def infer_requested_revision_fields(issue_types: list[str], existing_fields: list[str]) -> list[str]:
    field_order = [
        "question_text",
        "generation_basis",
        "evaluation_guide",
        "predicted_answer",
        "follow_up_question",
        "document_evidence",
    ]
    if existing_fields:
        normalized = [field for field in existing_fields if field in field_order]
        deduped: list[str] = []
        for field in normalized:
            if field not in deduped:
                deduped.append(field)
        return deduped or ["question_text", "evaluation_guide"]

    issue_map = {
        "job_relevance_issue": ["question_text", "generation_basis"],
        "weak_evidence": ["question_text", "evaluation_guide"],
        "doc_evidence_missing": ["question_text", "follow_up_question"],
        "followup_not_specific": ["follow_up_question"],
        "duplicate_question": ["question_text"],
        "too_generic": ["question_text", "evaluation_guide"],
        "fairness_risk": ["question_text", "evaluation_guide"],
        "too_long_for_interview": ["follow_up_question", "evaluation_guide"],
        "difficulty_mismatch": ["question_text", "evaluation_guide"],
        "weak_evaluation_guide": ["evaluation_guide"],
        "over_specific_predicted_answer": ["predicted_answer", "follow_up_question"],
    }
    mapped: list[str] = []
    for issue_type in issue_types:
        for field_name in issue_map.get(issue_type, []):
            if field_name not in mapped:
                mapped.append(field_name)
    return mapped or ["question_text", "evaluation_guide"]


def canonical_retry_guidance(
    issue_types: list[str],
    requested_fields: list[str],
    question: QuestionSet,
) -> str:
    issue_set = set(issue_types)
    field_set = set(requested_fields)
    parts: list[str] = []

    if "question_text" in field_set and "weak_evidence" in issue_set:
        parts.append("question_text는 문서에 직접 근거가 있는 검증 포인트만 남기고 과도한 가정을 줄이세요.")
    if "question_text" in field_set and "doc_evidence_missing" in issue_set:
        parts.append("question_text는 문서에서 확인 가능한 역할과 행동 중심으로 다시 좁혀 주세요.")
    if "question_text" in field_set and "too_generic" in issue_set:
        parts.append("question_text는 검증 포인트를 하나로 줄이고 더 구체적인 행동 확인형으로 바꿔 주세요.")
    if "evaluation_guide" in field_set or "weak_evaluation_guide" in issue_set:
        parts.append("evaluation_guide는 상중하 3줄 형식을 지키고 점수 차이가 나는 근거를 명확히 적어 주세요.")
    if "predicted_answer" in field_set or "over_specific_predicted_answer" in issue_set:
        parts.append("predicted_answer는 문서에 없는 사실을 단정하지 말고 조심스러운 추정 표현으로 낮춰 주세요.")
    if "follow_up_question" in field_set and {"followup_not_specific", "too_long_for_interview"} & issue_set:
        parts.append("follow_up_question은 한 문장으로 줄이고 검증 포인트 하나만 남겨 주세요.")
    if "follow_up_question" in field_set and "doc_evidence_missing" in issue_set:
        parts.append("follow_up_question은 없는 수치를 전제하지 말고 탐색형 표현으로 바꿔 주세요.")
    if not parts:
        parts.append("문서 근거와 면접 사용성을 우선으로 다시 다듬어 주세요.")

    guidance = " ".join(parts).strip()
    if "Slack" in guidance and "Slack" not in str(question.get("question_text") or ""):
        guidance = guidance.replace("Slack", "협업 도구")
    return guidance[:280]


def overall_status_from_score(
    question_avg: float,
    guide_avg: float,
    overall_score: float,
    issue_types: list[str],
) -> str:
    issue_set = set(issue_types)
    hard_issue_types = {"fairness_risk", "job_relevance_issue"}
    revision_required_issue_types = {
        "weak_evidence",
        "doc_evidence_missing",
        "followup_not_specific",
        "too_generic",
        "too_long_for_interview",
        "difficulty_mismatch",
        "weak_evaluation_guide",
        "over_specific_predicted_answer",
        "duplicate_question",
    }
    if hard_issue_types & issue_set:
        return "needs_revision" if overall_score >= 3.2 else "rejected"
    if revision_required_issue_types & issue_set:
        return "needs_revision" if overall_score >= 2.6 else "rejected"
    if overall_score >= 4.3 and question_avg >= 4.3 and guide_avg >= 4.0:
        return "approved"
    if overall_score >= 3.1:
        return "needs_revision"
    return "rejected"


def normalize_reviewer_status(
    raw_status: str,
    question_avg: float,
    guide_avg: float,
    overall_score: float,
    issue_types: list[str],
) -> str:
    normalized = overall_status_from_score(
        question_avg,
        guide_avg,
        overall_score,
        issue_types,
    )
    if raw_status == "approved":
        return "approved" if normalized == "approved" and not issue_types else "needs_revision"
    if raw_status in {"needs_revision", "rejected"}:
        return raw_status
    return normalized


def fallback_answer(question_id: str) -> PredictedAnswer:
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="예상 답변을 생성하지 못했습니다.",
        predicted_answer_basis="Predictor 결과가 없어 기본 문구를 사용했습니다.",
        answer_confidence="low",
        answer_risk_points=["예상답변_누락"],
    )


def fallback_follow_up(question_id: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="방금 말씀하신 경험에서 본인의 역할과 실제 기여를 조금 더 구체적으로 설명해 주실 수 있을까요?",
        follow_up_basis="Driller 결과가 없어 기본 검증형 꼬리질문을 사용했습니다.",
        drill_type="OTHER",
    )


def fallback_review(question_id: str) -> ReviewResult:
    return ReviewResult(
        question_id=question_id,
        status="needs_revision",
        reason="Reviewer 결과가 없어 수동 검토가 필요합니다.",
        reject_reason="",
        recommended_revision="직무 관련성, 문서 근거, 면접 사용성을 다시 확인해 주세요.",
        question_quality_scores=QuestionQualityRubric.model_validate({}),
        evaluation_guide_scores=EvaluationGuideRubric.model_validate({}),
    )


def analysis_summary(state: AgentState) -> DocumentAnalysisOutput:
    questions = selected_questions_for_output(state)
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
        job_fit="그래프는 질문 생성 근거와 reviewer 결과를 바탕으로 직무 적합성 신호를 정리합니다.",
        questionable_points=[
            item.get("generation_basis", "")
            for item in questions[:5]
            if item.get("generation_basis")
        ],
    )
