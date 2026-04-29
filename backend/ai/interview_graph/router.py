from ai.interview_graph.state import AgentState

FOLLOW_UP_WEAK_FLAGS = {
    "FOLLOW_UP_TOO_WEAK",
    "꼬리질문_약함",
    "꼬리질문_연결성_부족",
    "꼬리질문_보강_필요",
} 
QUESTION_REWRITE_FLAGS = {
    "QUESTION_REWRITE_NEEDED",
    "REVIEW_NOT_APPROVED",
    "LOW_SCORE",
    "QUESTION_TOO_GENERIC",
    "EVIDENCE_TOO_WEAK",
    "LOW_JOB_RELEVANCE",
    "DUPLICATE_RISK",
    "질문_일반적",
    "문서_근거_부족",
    "직무_관련성_부족",
    "중복_위험",
    "보완_필요",
    "재작성_권장",
}

def route_after_scoring(state: AgentState) -> str:
    retry_count = state.get("retry_count", 0)
    max_retry_count = state.get("max_retry_count", 3)
    questioner_retry_count = state.get("questioner_retry_count", 0)
    driller_retry_count = state.get("driller_retry_count", 0)
    max_questioner_retry_count = state.get("max_questioner_retry_count", 1)
    max_driller_retry_count = state.get("max_driller_retry_count", 1)
    summary = state.get("review_summary", {})

    if retry_count >= max_retry_count:
        return "selector"

    quality_issues = set(summary.get("quality_issues", []))
    dominant_quality_flags = set(summary.get("dominant_quality_flags", []))
    low_score_count = int(summary.get("low_score_count", 0) or 0)
    scored_question_count = int(summary.get("scored_question_count", 0) or 0)
    approved_count = int(summary.get("approved_count", 0) or 0)
    needs_revision_count = int(
        (summary.get("review_status_counts", {}) or {}).get("needs_revision", 0)
        or 0
    )
    rejected_count = int(summary.get("rejected_count", 0) or 0)

    has_follow_up_issue = bool(
        quality_issues.intersection(FOLLOW_UP_WEAK_FLAGS)
        or dominant_quality_flags.intersection(FOLLOW_UP_WEAK_FLAGS)
        or summary.get("follow_up_issue_question_ids")
    )
    has_question_rewrite_issue = bool(
        quality_issues.intersection(QUESTION_REWRITE_FLAGS)
        or dominant_quality_flags.intersection(QUESTION_REWRITE_FLAGS)
        or summary.get("question_rewrite_question_ids")
    )

    if has_follow_up_issue and driller_retry_count < max_driller_retry_count:
        return "retry_driller"

    if (
        0 < low_score_count <= 2
        and questioner_retry_count < max_questioner_retry_count
    ):
        return "retry_questioner"

    majority_low_score = bool(
        scored_question_count
        and low_score_count > scored_question_count / 2
    )
    if (
        (majority_low_score or approved_count < 5 or rejected_count > 0)
        and questioner_retry_count < max_questioner_retry_count
    ):
        return "retry_questioner"

    if (
        has_question_rewrite_issue
        and needs_revision_count > 0
        and questioner_retry_count < max_questioner_retry_count
    ):
        return "retry_questioner"

    return "selector"
