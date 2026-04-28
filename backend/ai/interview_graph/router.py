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
    summary = state.get("review_summary", {})

    if retry_count >= max_retry_count:
        return "selector"

    quality_issues = set(summary.get("quality_issues", []))

    if quality_issues.intersection(FOLLOW_UP_WEAK_FLAGS):
        return "retry_driller"

    if summary.get("approved_count", 0) < 5:
        return "retry_questioner"

    if summary.get("avg_score", 0) < 80:
        return "retry_questioner"

    if quality_issues.intersection(QUESTION_REWRITE_FLAGS):
        return "retry_questioner"

    return "selector"
