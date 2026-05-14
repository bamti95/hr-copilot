from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from functools import lru_cache
from typing import Sequence

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536
BGE_M3_MODEL = os.getenv("JOB_POSTING_EMBEDDING_MODEL", "BAAI/bge-m3")
BGE_RERANKER_MODEL = os.getenv(
    "JOB_POSTING_RERANKER_MODEL",
    "BAAI/bge-reranker-v2-m3",
)
FALLBACK_EMBEDDING_MODEL = "local-hash-embedding-v1"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def current_embedding_model_name() -> str:
    if _env_flag("JOB_POSTING_DISABLE_EMBEDDING_MODEL"):
        return FALLBACK_EMBEDDING_MODEL
    return BGE_M3_MODEL if _get_sentence_transformer() is not None else FALLBACK_EMBEDDING_MODEL


def current_reranker_model_name() -> str:
    if _env_flag("JOB_POSTING_DISABLE_RERANKER"):
        return "heuristic-slot-rerank"
    return BGE_RERANKER_MODEL if _get_cross_encoder() is not None else "heuristic-slot-rerank"


def embed_text(text: str) -> list[float]:
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
    if not documents:
        return []

    if _env_flag("JOB_POSTING_DISABLE_RERANKER"):
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
    if _env_flag("JOB_POSTING_DISABLE_RERANKER"):
        logger.info("BGE reranker disabled; using heuristic slot rerank.")
        return None
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder(BGE_RERANKER_MODEL)
    except Exception as exc:
        logger.warning("Could not load reranker model %s: %s", BGE_RERANKER_MODEL, exc)
        return None


def _fit_vector_dim(vector: list[float]) -> list[float]:
    if len(vector) == EMBEDDING_DIM:
        return [round(value, 6) for value in vector]
    if len(vector) > EMBEDDING_DIM:
        trimmed = vector[:EMBEDDING_DIM]
        norm = math.sqrt(sum(value * value for value in trimmed)) or 1.0
        return [round(value / norm, 6) for value in trimmed]
    return [round(value, 6) for value in vector] + [0.0] * (EMBEDDING_DIM - len(vector))


def _hash_embed_text(text: str) -> list[float]:
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
