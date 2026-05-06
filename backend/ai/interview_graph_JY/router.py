from ai.interview_graph_JY.state import AgentState


FOLLOW_UP_FLAGS = {"FOLLOW_UP_TOO_WEAK", "꼬리질문_약함"}
QUESTION_REWRITE_FLAGS = {
    "REVIEW_NOT_APPROVED",
    "EVIDENCE_TOO_WEAK",
    "LOW_JOB_RELEVANCE",
    "DUPLICATE_RISK",
}


def route_after_review(state: AgentState) -> str:
    if state.get("retry_count", 0) >= state.get("max_retry_count", 2):
        return "selector"

    summary = state.get("review_summary", {})
    quality_issues = set(summary.get("quality_issues", []))
    low_score_count = int(summary.get("low_score_count", 0) or 0)
    approved_count = int(summary.get("approved_count", 0) or 0)

    if (
        quality_issues.intersection(FOLLOW_UP_FLAGS)
        and state.get("driller_retry_count", 0) < state.get("max_driller_retry_count", 1)
    ):
        return "retry_driller"

    should_retry_questioner = (
        approved_count < 4
        or quality_issues.intersection(QUESTION_REWRITE_FLAGS)
        or low_score_count >= 3
    )
    if should_retry_questioner and state.get("questioner_retry_count", 0) < state.get(
        "max_questioner_retry_count",
        1,
    ):
        return "retry_questioner"

    return "selector"
