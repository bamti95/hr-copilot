from typing import Any


def llm_usage_update(new_usages: list[dict[str, Any]] | None) -> dict[str, Any]:
    """새로 생성된 LLM 사용량(Usage) 레코드에 대한 LangGraph 업데이트 페이로드를 반환"""
    usages = list(new_usages or [])
    if not usages:
        return {}
    return {"llm_usages": usages}


def collect_llm_usage_update(
    node_update: Any,
    saved_usage_count: int = 0,
    *,
    cumulative: bool = False,
) -> tuple[list[dict[str, Any]], int, bool]:
    """노드 업데이트에서 중복 저장 없이 LLM 사용량(Usage)을 추출

    대부분의 그래프는 현재 노드에서 생성된 사용량만 반환
    일부 구형 그래프 구현체는 누적된 `llm_usages` 리스트를 반환하므로,
    이러한 러너의 경우 `cumulative=True`로 설정하여 아직 수집되지 않은 레코드만 추출
    """
    if not isinstance(node_update, dict):
        return [], saved_usage_count, False

    usages = list(node_update.get("llm_usages") or [])
    if not usages:
        return [], saved_usage_count, False

    if not cumulative:
        return usages, saved_usage_count + len(usages), True

    if len(usages) < saved_usage_count:
        return usages, len(usages), True

    return usages[saved_usage_count:], len(usages), True
