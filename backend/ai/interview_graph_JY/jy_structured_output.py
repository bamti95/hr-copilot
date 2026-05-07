"""JY 그래프 전용: 노드별 model 인자를 받는 structured output 호출."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, TypeVar

from pydantic import BaseModel

from ai.interview_graph.llm_usage import StructuredOutputCallError, calculate_estimated_cost
from ai.llm_client import client
from core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _usage_value(usage: Any, key: str, default: int = 0) -> int:
    if usage is None:
        return default
    if isinstance(usage, dict):
        value = usage.get(key, default)
    else:
        value = getattr(usage, key, default)
    return int(value or default)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


async def call_structured_output_with_model(
    *,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    model_name: str,
) -> tuple[T, list[dict[str, Any]]]:
    usages: list[dict[str, Any]] = []
    last_error: Exception | None = None

    for _ in range(2):
        started_at = time.perf_counter()
        started_datetime = datetime.now(timezone.utc)
        request_json = {
            "node": node_name,
            "model": model_name,
            "response_model": response_model.__name__,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = await asyncio.wait_for(
                client.responses.parse(
                    model=model_name,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    text_format=response_model,
                ),
                timeout=settings.OPENAI_TIMEOUT_SECONDS,
            )
            ended_datetime = datetime.now(timezone.utc)
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            usage = getattr(response, "usage", None) or getattr(
                response,
                "usage_metadata",
                None,
            )
            input_tokens = _usage_value(usage, "input_tokens")
            output_tokens = _usage_value(usage, "output_tokens")
            total_tokens = _usage_value(
                usage,
                "total_tokens",
                input_tokens + output_tokens,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("Structured output was empty.")
            output_json = _jsonable(parsed)
            usages.append(
                {
                    "node": node_name,
                    "model_name": model_name,
                    "request_json": request_json,
                    "output_json": output_json,
                    "response_json": _jsonable(response),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": calculate_estimated_cost(
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    ),
                    "call_status": "success",
                    "elapsed_ms": elapsed_ms,
                    "started_at": started_datetime,
                    "ended_at": ended_datetime,
                }
            )
            return parsed, usages
        except Exception as exc:  # noqa: BLE001 - preserve SDK/validation details.
            ended_datetime = datetime.now(timezone.utc)
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            last_error = exc
            usages.append(
                {
                    "node": node_name,
                    "model_name": model_name,
                    "request_json": request_json,
                    "output_json": None,
                    "response_json": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "call_status": "failed",
                    "elapsed_ms": elapsed_ms,
                    "error_message": str(exc),
                    "started_at": started_datetime,
                    "ended_at": ended_datetime,
                }
            )
            logger.warning(
                "Structured output call failed for %s at node %s: %s",
                response_model.__name__,
                node_name,
                exc,
            )

    raise StructuredOutputCallError(
        f"Structured output call failed for {response_model.__name__}",
        usages,
    ) from last_error
