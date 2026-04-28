import asyncio
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from ai.llm_client import client, get_openai_model
from core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input_per_1m": 0.15, "output_per_1m": 0.60},
    "gpt-4o": {"input_per_1m": 2.50, "output_per_1m": 10.00},
}


class StructuredOutputCallError(RuntimeError):
    def __init__(self, message: str, usages: list[dict[str, Any]]):
        super().__init__(message)
        self.usages = usages


def calculate_estimated_cost(
    *,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    pricing = MODEL_PRICING.get(model_name)
    if pricing is None:
        return 0.0

    input_cost = input_tokens / 1_000_000 * pricing["input_per_1m"]
    output_cost = output_tokens / 1_000_000 * pricing["output_per_1m"]
    return round(input_cost + output_cost, 6)


def _usage_value(usage: Any, key: str, default: int = 0) -> int:
    if usage is None:
        return default
    if isinstance(usage, dict):
        value = usage.get(key, default)
    else:
        value = getattr(usage, key, default)
    return int(value or default)


async def call_structured_output_with_usage(
    *,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> tuple[T, list[dict[str, Any]]]:
    model_name = get_openai_model()
    usages: list[dict[str, Any]] = []
    last_error: Exception | None = None

    for _ in range(2):
        started_at = time.perf_counter()
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
            usages.append(
                {
                    "node": node_name,
                    "model_name": model_name,
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
                }
            )
            return parsed, usages
        except Exception as exc:  # noqa: BLE001 - preserve SDK/validation details.
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            last_error = exc
            usages.append(
                {
                    "node": node_name,
                    "model_name": model_name,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "call_status": "failed",
                    "elapsed_ms": elapsed_ms,
                    "error_message": str(exc),
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
