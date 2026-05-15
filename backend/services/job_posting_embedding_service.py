"""채용공고 분석용 임베딩/리랭킹 유틸리티.

질의를 벡터로 바꾸고, 후보 문서를 재정렬하는 공통 함수를 제공한다.
실행 환경에 따라 로컬 모델을 쓰거나 해시 기반 대체 경로로 내려간다.
벡터 차원이 모델마다 달라질 수 있으므로 최종 저장 차원은 이 파일에서 맞춘다.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from functools import lru_cache
from typing import Sequence

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    """정수형 환경 변수를 읽는다.

    값이 비어 있거나 형식이 잘못되면 기본값으로 되돌린다.
    운영 설정 오류로 분석이 중단되지 않게 하는 완충 장치다.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

# 벡터 저장 차원. 모델 출력 차원이 달라도 최종 저장 형식은 이 값에 맞춘다.
EMBEDDING_DIM = _env_int("JOB_POSTING_EMBEDDING_DIM", 1536)
BGE_M3_MODEL = os.getenv("JOB_POSTING_EMBEDDING_MODEL", "BAAI/bge-m3")
BGE_RERANKER_MODEL = os.getenv(
    "JOB_POSTING_RERANKER_MODEL",
    "BAAI/bge-reranker-v2-m3",
)
# 모델을 쓸 수 없을 때도 검색 파이프라인을 유지하기 위한 대체 임베딩 이름이다.
FALLBACK_EMBEDDING_MODEL = "local-hash-embedding-v1"


def _env_flag(name: str, default: bool = False) -> bool:
    """불리언 환경 변수를 읽는다."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _env_disabled(name: str, *, enabled_name: str | None = None) -> bool:
    """비활성화 여부를 통합 해석한다.

    `DISABLE_*`와 `*_ENABLED=false`를 모두 같은 의미로 본다.
    호출부가 설정 키 차이를 신경 쓰지 않게 하려는 목적이다.
    """
    if _env_flag(name):
        return True
    if enabled_name is None:
        return False
    raw = os.getenv(enabled_name)
    if raw is None:
        return False
    return raw.strip().lower() in {"0", "false", "f", "no", "n", "off"}


def current_embedding_model_name() -> str:
    """현재 실제로 사용되는 임베딩 모델 이름을 반환한다."""
    if _env_flag("JOB_POSTING_DISABLE_EMBEDDING_MODEL"):
        return FALLBACK_EMBEDDING_MODEL
    return BGE_M3_MODEL if _get_sentence_transformer() is not None else FALLBACK_EMBEDDING_MODEL


def current_reranker_model_name() -> str:
    """현재 실제로 사용되는 리랭커 이름을 반환한다."""
    if _env_disabled("JOB_POSTING_DISABLE_RERANKER", enabled_name="JOB_POSTING_RERANKER_ENABLED"):
        return "heuristic-slot-rerank"
    return BGE_RERANKER_MODEL if _get_cross_encoder() is not None else "heuristic-slot-rerank"


def embed_text(text: str) -> list[float]:
    """텍스트를 임베딩 벡터로 변환한다.

    로컬 모델 사용이 불가능하면 해시 기반 임베딩으로 내려간다.
    호출자는 항상 동일 차원의 벡터를 받는다.
    """
    if _env_flag("JOB_POSTING_DISABLE_EMBEDDING_MODEL"):
        return _hash_embed_text(text)

    model = _get_sentence_transformer()
    if model is None:
        return _hash_embed_text(text)

    try:
        vector = model.encode(
            text or "",
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return _fit_vector_dim([float(value) for value in vector])
    except Exception as exc:
        logger.warning("bge-m3 embedding failed; falling back to hash embedding: %s", exc)
        return _hash_embed_text(text)


def rerank_pairs(query: str, documents: Sequence[str]) -> list[float]:
    """질의와 문서 쌍의 관련도 점수를 계산한다.

    점수는 높을수록 관련성이 높다는 뜻이다.
    리랭커가 비활성화되었거나 로딩에 실패하면 빈 리스트를 반환한다.
    """
    if not documents:
        return []

    if _env_disabled("JOB_POSTING_DISABLE_RERANKER", enabled_name="JOB_POSTING_RERANKER_ENABLED"):
        return []

    model = _get_cross_encoder()
    if model is None:
        return []

    try:
        scores = model.predict(
            [(query, document) for document in documents],
            show_progress_bar=False,
        )
        return [float(score) for score in scores]
    except Exception as exc:
        logger.warning("bge reranker failed; keeping heuristic rerank only: %s", exc)
        return []


@lru_cache(maxsize=1)
def _get_sentence_transformer():
    """임베딩 모델을 한 번만 로드해 재사용한다."""
    if _env_flag("JOB_POSTING_DISABLE_EMBEDDING_MODEL"):
        logger.info("BGE embedding model disabled; using hash embedding fallback.")
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(BGE_M3_MODEL)
    except Exception as exc:
        logger.warning("Could not load embedding model %s: %s", BGE_M3_MODEL, exc)
        return None


@lru_cache(maxsize=1)
def _get_cross_encoder():
    """리랭커 모델을 한 번만 로드해 재사용한다."""
    if _env_disabled("JOB_POSTING_DISABLE_RERANKER", enabled_name="JOB_POSTING_RERANKER_ENABLED"):
        logger.info("BGE reranker disabled; using heuristic slot rerank.")
        return None
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder(BGE_RERANKER_MODEL)
    except Exception as exc:
        logger.warning("Could not load reranker model %s: %s", BGE_RERANKER_MODEL, exc)
        return None


def _fit_vector_dim(vector: list[float]) -> list[float]:
    """모델 출력 벡터를 저장 차원에 맞춘다.

    차원이 길면 자른 뒤 다시 정규화한다.
    차원이 짧으면 0으로 패딩한다.
    저장 스키마를 고정하면서도 여러 모델을 붙일 수 있게 하는 규칙이다.
    """
    if len(vector) == EMBEDDING_DIM:
        return [round(value, 6) for value in vector]
    if len(vector) > EMBEDDING_DIM:
        trimmed = vector[:EMBEDDING_DIM]
        norm = math.sqrt(sum(value * value for value in trimmed)) or 1.0
        return [round(value / norm, 6) for value in trimmed]
    return [round(value, 6) for value in vector] + [0.0] * (EMBEDDING_DIM - len(vector))


def _hash_embed_text(text: str) -> list[float]:
    """모델 없이도 동작하도록 해시 기반 임베딩을 만든다.

    품질은 로컬 모델보다 낮지만, 토큰 분포를 이용해 최소한의 유사도 비교는 가능하다.
    테스트 환경이나 모델 로딩 실패 상황에서 파이프라인을 끊지 않는 것이 목적이다.
    """
    vector = [0.0] * EMBEDDING_DIM
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", (text or "").lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = -1.0 if digest[4] % 2 else 1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]
