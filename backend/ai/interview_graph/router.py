from ai.interview_graph.state import AgentState


def route_after_scoring(state: AgentState) -> str:
    retry_count = state.get("retry_count", 0)
    max_retry_count = state.get("max_retry_count", 3)
    summary = state.get("review_summary", {})

    if retry_count >= max_retry_count:
        return "selector"

    if summary.get("approved_count", 0) < 5:
        return "retry_questioner"

    if summary.get("avg_score", 0) < 80:
        return "retry_questioner"

    if "FOLLOW_UP_TOO_WEAK" in summary.get("quality_issues", []):
        return "retry_driller"

    return "selector"
