"""JY 인터뷰 그래프 노드별 OpenAI 모델 이름 결정 (latency 실험용)."""

import json
import logging
import os
from pathlib import Path

from ai.llm_client import get_openai_model

logger = logging.getLogger(__name__)

_MAP_ENV = "JY_GRAPH_MODEL_MAP"


def _backend_dotenv_path() -> Path:
    """`backend/ai/interview_graph_JY/` → `backend/.env`."""
    return Path(__file__).resolve().parents[2] / ".env"


def _env_value(key: str) -> str:
    """프로세스 환경변수 우선. 비어 있거나 없으면 `backend/.env`에서 보조 조회.

    `load_dotenv(..., override=False)` 때문에 시스템/셸에 빈 값이 이미 있으면 `.env`가
    적용되지 않는 경우가 있어, 실험용 JY 라우팅 키만 파일에서 한 번 더 읽는다.
    """
    direct = os.environ.get(key)
    if direct is not None and str(direct).strip():
        return str(direct).strip()
    try:
        from dotenv import dotenv_values

        raw = dotenv_values(_backend_dotenv_path()).get(key)
    except OSError:
        return ""
    return str(raw or "").strip()


def _routing_map_from_env() -> dict[str, str]:
    raw = _env_value(_MAP_ENV)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JY_GRAPH_MODEL_MAP JSON 파싱 실패 — 무시합니다.")
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in data.items():
        model = str(value or "").strip()
        if model:
            out[str(key)] = model
    return out


def resolve_model(node_name: str) -> str:
    """노드별 오버라이드가 없으면 전역 기본 모델(`get_openai_model`)을 사용합니다.

    우선순위:
    1. 환경변수 `JY_GRAPH_MODEL_MAP` JSON 객체의 `node_name` 키
    2. 환경변수 `JY_GRAPH_MODEL_<NODE_NAME_UPPER>` (예: jy_analyzer → JY_GRAPH_MODEL_JY_ANALYZER)
    3. `get_openai_model()`
    """
    mapped = _routing_map_from_env().get(node_name)
    if mapped:
        return mapped

    env_key = f"JY_GRAPH_MODEL_{node_name.upper()}"
    per_node = _env_value(env_key)
    if per_node:
        return per_node

    return get_openai_model()
