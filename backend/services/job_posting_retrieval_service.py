"""채용공고 분석용 근거 검색 서비스.

위험 이슈별로 검색 질의를 만들고, metadata 검색과 vector 검색을 먼저 수행한다.
근거가 부족할 때만 BM25/full-text를 보조 경로로 실행한다.
최종 후보는 휴리스틱 재정렬과 모델 재정렬을 거쳐 리포트용 근거로 반환한다.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.job_posting_knowledge_chunk import JobPostingKnowledgeChunk
from models.job_posting_knowledge_source import JobPostingKnowledgeSourceType
from repositories.job_posting_knowledge_repository import JobPostingKnowledgeChunkRepository
from services.job_posting_knowledge_service import (
    calculate_keyword_score,
    document_priority,
    embed_text,
    extract_query_terms,
    normalize_embedding,
)
from services.job_posting_embedding_service import (
    current_reranker_model_name,
    rerank_pairs,
)


logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# BM25는 기본 경로가 아니라 fallback 경로로 다루는 것이 기본 전략이다.
BM25_ENABLED = _env_flag("JOB_POSTING_BM25_ENABLED", True)
BM25_MODE = os.getenv("JOB_POSTING_BM25_MODE", "fallback_only").strip().lower()
# BM25가 길게 물리면 전체 분석 시간이 급격히 늘어나므로 초 단위 상한을 둔다.
BM25_TIMEOUT_SECONDS = _env_float("JOB_POSTING_BM25_TIMEOUT_SECONDS", 3.0)
BM25_TOP_K = _env_int("JOB_POSTING_BM25_TOP_K", 5)
VECTOR_TOP_K = _env_int("JOB_POSTING_VECTOR_TOP_K", 12)
FINAL_EVIDENCE_LIMIT = _env_int("JOB_POSTING_FINAL_EVIDENCE_LIMIT", 5)
RERANKER_ENABLED = _env_flag("JOB_POSTING_RERANKER_ENABLED", True)
# 리랭커는 비용이 큰 편이라 상위 후보만 태운다.
RERANK_CANDIDATE_LIMIT = _env_int("JOB_POSTING_RERANK_CANDIDATE_LIMIT", 5)


@dataclass(slots=True)
class RetrievedEvidence:
    """검색 후보 1건을 리포트에 싣기 위한 중간 객체.

    text/vector/keyword/hybrid/rerank 점수를 함께 들고 다닌다.
    어떤 단계에서 점수가 올라갔는지 추적하기 쉽게 설계했다.
    """
    chunk: JobPostingKnowledgeChunk
    text_score: float = 0.0
    vector_score: float = 0.0
    keyword_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: float = 0.0
    matched_terms: list[str] | None = None

    def to_payload(self) -> dict[str, Any]:
        """리포트와 로그 저장에 쓰기 쉬운 형태로 직렬화한다."""
        source = getattr(self.chunk, "knowledge_source", None)
        content = self.chunk.content or ""
        metadata = self.chunk.metadata_json or {}
        return {
            "chunk_id": self.chunk.id,
            "source_id": self.chunk.knowledge_source_id,
            "title": getattr(source, "title", None),
            "source_type": getattr(source, "source_type", None),
            "doc_id": metadata.get("doc_id"),
            "chunk_type": self.chunk.chunk_type,
            "section_title": self.chunk.section_title,
            "page_start": self.chunk.page_start or metadata.get("page"),
            "page_end": self.chunk.page_end,
            "law_name": self.chunk.law_name,
            "article_no": self.chunk.article_no,
            "article_ref": metadata.get("article_ref"),
            "effective_date": metadata.get("effective_date"),
            "is_latest": metadata.get("is_latest"),
            "content": content[:900],
            "text_score": round(self.text_score, 4),
            "vector_score": round(self.vector_score, 4),
            "keyword_score": round(self.keyword_score, 4),
            "hybrid_score": round(self.hybrid_score, 4),
            "rerank_score": round(self.rerank_score, 4),
            "matched_terms": self.matched_terms or [],
        }


class JobPostingRetrievalService:
    """이슈별 근거 검색을 총괄한다.

    검색 순서는 metadata -> vector -> BM25 fallback이다.
    마지막 실행의 세부 시간과 후보 수는 `last_trace`에 남긴다.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.chunk_repo = JobPostingKnowledgeChunkRepository(db)
        self.last_trace: dict[str, Any] = {}

    async def retrieve_for_issue(
        self,
        *,
        issue: dict[str, Any],
        limit: int = 12,
    ) -> list[RetrievedEvidence]:
        """단일 이슈에 대한 근거 후보를 수집하고 재정렬한다.

        빠른 경로에서 충분한 후보를 확보하면 BM25는 건너뛴다.
        반환값은 최종 점수 기준으로 정렬된 근거 목록이다.
        """
        trace: dict[str, Any] = {
            "bm25_enabled": BM25_ENABLED,
            "bm25_mode": BM25_MODE,
            "bm25_timeout_seconds": BM25_TIMEOUT_SECONDS,
            "bm25_used": False,
            "bm25_timeout": False,
            "metadata_elapsed_ms": 0,
            "vector_elapsed_ms": 0,
            "bm25_elapsed_ms": 0,
            "merge_elapsed_ms": 0,
            "rerank_elapsed_ms": 0,
            "metadata_count": 0,
            "vector_count": 0,
            "bm25_count": 0,
        }
        queries = build_query_candidates(issue)
        base_query = queries[0]
        text_rows: list[tuple[JobPostingKnowledgeChunk, float]] = []
        vector_rows: list[tuple[JobPostingKnowledgeChunk, float]] = []

        for query in queries:
            query_terms = extract_query_terms(query)
            query_embedding = embed_text(query)

            # issue_code, risk_category 같은 구조화된 값은 DB 비용이 낮아 먼저 조회한다.
            started_at = time.perf_counter()
            metadata_rows = await self.chunk_repo.search_by_metadata_exact(
                issue_type=issue.get("issue_type"),
                query_terms=query_terms,
                limit=min(limit, FINAL_EVIDENCE_LIMIT),
            )
            trace["metadata_elapsed_ms"] += int((time.perf_counter() - started_at) * 1000)
            trace["metadata_count"] += len(metadata_rows)
            text_rows.extend(metadata_rows)

            # vector 검색은 의미 유사도를 빠르게 확보하는 기본 경로다.
            started_at = time.perf_counter()
            try:
                vector_rows.extend(
                    await self.chunk_repo.search_by_vector(
                        query_embedding=query_embedding,
                        limit=max(limit, VECTOR_TOP_K),
                    )
                )
            except Exception:
                vector_rows.extend(
                    await self._python_vector_fallback(
                        query_embedding=query_embedding,
                        query_terms=query_terms,
                        limit=max(limit, VECTOR_TOP_K),
                    )
                )
            trace["vector_elapsed_ms"] += int((time.perf_counter() - started_at) * 1000)
            trace["vector_count"] = len(vector_rows)

        merge_started_at = time.perf_counter()
        merged = merge_retrieval_rows(
            issue=issue,
            query_terms=extract_query_terms(" ".join(queries)),
            text_rows=dedupe_rows(text_rows),
            vector_rows=dedupe_rows(vector_rows),
        )
        trace["merge_elapsed_ms"] += int((time.perf_counter() - merge_started_at) * 1000)

        # 빠른 경로에서 후보가 약하면 그때만 BM25 fallback을 실행한다.
        if should_run_bm25(merged, limit=limit):
            for query in queries[:1]:
                query_terms = extract_query_terms(query)
                bm25_rows, bm25_trace = await self._bm25_retrieve_with_timeout(
                    query=query,
                    query_terms=query_terms,
                    limit=min(limit, BM25_TOP_K),
                )
                trace["bm25_used"] = True
                trace["bm25_timeout"] = trace["bm25_timeout"] or bm25_trace["timeout"]
                trace["bm25_elapsed_ms"] += bm25_trace["elapsed_ms"]
                trace["bm25_count"] += len(bm25_rows)
                text_rows.extend(bm25_rows)

            merge_started_at = time.perf_counter()
            merged = merge_retrieval_rows(
                issue=issue,
                query_terms=extract_query_terms(" ".join(queries)),
                text_rows=dedupe_rows(text_rows),
                vector_rows=dedupe_rows(vector_rows),
            )
            trace["merge_elapsed_ms"] += int((time.perf_counter() - merge_started_at) * 1000)

        rerank_started_at = time.perf_counter()
        reranked = rerank_evidence(issue=issue, evidences=merged)
        apply_model_rerank(query=base_query, evidences=reranked)
        trace["rerank_elapsed_ms"] = int((time.perf_counter() - rerank_started_at) * 1000)
        trace["final_count"] = len(reranked[:limit])
        self.last_trace = trace
        return reranked[:limit]

    async def _bm25_retrieve_with_timeout(
        self,
        *,
        query: str,
        query_terms: list[str],
        limit: int,
    ) -> tuple[list[tuple[JobPostingKnowledgeChunk, float]], dict[str, Any]]:
        """BM25/full-text fallback을 제한 시간 안에서 실행한다.

        timeout이 나면 전체 분석을 실패시키지 않고 빈 결과로 넘긴다.
        목적은 근거 보강이지, 느린 검색 때문에 전체 파이프라인을 멈추는 것이 아니다.
        """
        if not BM25_ENABLED:
            return [], {"elapsed_ms": 0, "timeout": False}

        started_at = time.perf_counter()
        try:
            rows = await asyncio.wait_for(
                self.chunk_repo.search_by_full_text(
                    query=query,
                    query_terms=query_terms,
                    limit=limit,
                ),
                timeout=BM25_TIMEOUT_SECONDS,
            )
            if len(rows) < limit:
                rows.extend(
                    await self.chunk_repo.search_by_keyword_fallback(
                        query_terms=query_terms,
                        limit=limit - len(rows),
                    )
                )
            return rows, {
                "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                "timeout": False,
            }
        except TimeoutError:
            logger.warning(
                "Job posting BM25 retrieval timed out. timeout_seconds=%s query=%s",
                BM25_TIMEOUT_SECONDS,
                query[:120],
            )
            return [], {
                "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                "timeout": True,
            }
        except Exception as exc:
            logger.warning("Job posting BM25 retrieval failed; fallback skipped: %s", exc)
            return [], {
                "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                "timeout": False,
                "error": str(exc),
            }

    async def _python_vector_fallback(
        self,
        *,
        query_embedding: list[float],
        query_terms: list[str],
        limit: int,
    ) -> list[tuple[JobPostingKnowledgeChunk, float]]:
        """DB vector 연산을 쓸 수 없을 때 파이썬에서 코사인 유사도를 계산한다."""
        pool = await self.chunk_repo.find_search_pool(query_terms=query_terms, limit=500)
        if not pool:
            pool = await self.chunk_repo.find_search_pool(query_terms=[], limit=1000)
        scored = [
            (chunk, cosine_similarity(query_embedding, normalize_embedding(chunk.embedding)))
            for chunk in pool
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]


def build_issue_query(issue: dict[str, Any]) -> str:
    """이슈의 핵심 필드를 한 문장 질의로 합친다."""
    parts = [
        issue.get("issue_type") or "",
        issue.get("flagged_text") or "",
        issue.get("why_risky") or "",
        " ".join(issue.get("query_terms") or []),
    ]
    return " ".join(part for part in parts if part).strip()


def build_query_candidates(issue: dict[str, Any]) -> list[str]:
    """기본 질의를 바탕으로 검색 변형 질의를 만든다.

    한 질의로 놓칠 수 있는 법령형 표현과 기준형 표현을 보강하려는 목적이다.
    동일 문장은 중복 제거한다.
    """
    base_query = build_issue_query(issue)
    candidates = [base_query]
    flagged_text = issue.get("flagged_text") or ""
    issue_label = issue_type_to_korean(issue.get("issue_type"))
    terms = " ".join(issue.get("query_terms") or [])
    if issue_label and flagged_text:
        candidates.append(f"{issue_label} {flagged_text} 법령 가이드 사례")
    if issue_label and terms:
        candidates.append(f"{issue_label} {terms} 채용공고 금지 기준")
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        normalized = " ".join(candidate.split()).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def issue_type_to_korean(issue_type: str | None) -> str:
    """영문 issue code를 사람이 읽기 쉬운 한글 이름으로 바꾼다."""
    labels = {
        "GENDER_DISCRIMINATION": "성별 차별",
        "AGE_DISCRIMINATION": "연령 차별",
        "IRRELEVANT_PERSONAL_INFO": "직무무관 개인정보",
        "PHYSICAL_CONDITION": "신체조건 차별",
        "FALSE_JOB_AD": "거짓 채용광고",
        "UNFAVORABLE_CONDITION_CHANGE": "불리한 근로조건 변경",
        "WORKING_CONDITION_AMBIGUITY": "근로조건 불명확",
    }
    return labels.get(issue_type or "", issue_type or "")


def dedupe_rows(
    rows: list[tuple[JobPostingKnowledgeChunk, float]],
) -> list[tuple[JobPostingKnowledgeChunk, float]]:
    """같은 chunk가 여러 검색 경로에서 잡혀도 최고 점수만 남긴다."""
    by_chunk_id: dict[int, tuple[JobPostingKnowledgeChunk, float]] = {}
    for chunk, score in rows:
        current = by_chunk_id.get(chunk.id)
        if current is None or float(score or 0.0) > current[1]:
            by_chunk_id[chunk.id] = (chunk, float(score or 0.0))
    return list(by_chunk_id.values())


def merge_retrieval_rows(
    *,
    issue: dict[str, Any],
    query_terms: list[str],
    text_rows: list[tuple[JobPostingKnowledgeChunk, float]],
    vector_rows: list[tuple[JobPostingKnowledgeChunk, float]],
) -> list[RetrievedEvidence]:
    """검색 경로별 결과를 하나의 hybrid 점수로 합친다.

    텍스트 점수, 벡터 점수, 키워드 점수에 문서 종류와 최신성 보너스를 더한다.
    issue_code가 정확히 맞는 근거는 추가 가점을 받아 상위로 올라간다.
    """
    by_id: dict[int, RetrievedEvidence] = {}

    for rank, (chunk, score) in enumerate(text_rows, start=1):
        evidence = by_id.setdefault(chunk.id, RetrievedEvidence(chunk=chunk))
        evidence.text_score = max(evidence.text_score, normalize_rank_score(score, rank))

    for rank, (chunk, score) in enumerate(vector_rows, start=1):
        evidence = by_id.setdefault(chunk.id, RetrievedEvidence(chunk=chunk))
        evidence.vector_score = max(evidence.vector_score, normalize_rank_score(score, rank))

    merged = list(by_id.values())
    for evidence in merged:
        keyword_score, matched_terms = calculate_keyword_score(
            query_terms=query_terms,
            chunk=evidence.chunk,
        )
        evidence.keyword_score = keyword_score
        evidence.matched_terms = matched_terms
        text_weight, vector_weight = retrieval_weights(evidence.chunk)
        source = getattr(evidence.chunk, "knowledge_source", None)
        source_priority = document_priority(getattr(source, "source_type", "") or "")
        # 검색 의도와 issue_code가 정확히 맞는 근거는 설명력이 높아 별도 가점을 준다.
        issue_match_bonus = 0.15 if evidence.chunk.issue_code == issue.get("issue_type") else 0.0
        freshness_bonus = source_freshness_bonus(evidence.chunk)
        evidence.hybrid_score = (
            (evidence.text_score * text_weight)
            + (evidence.vector_score * vector_weight)
            + (keyword_score * 0.2)
            + issue_match_bonus
            + freshness_bonus
            + (0.03 / max(source_priority, 1))
        )

    merged.sort(key=lambda item: item.hybrid_score, reverse=True)
    return merged


def should_run_bm25(evidences: list[RetrievedEvidence], *, limit: int) -> bool:
    """BM25 fallback이 필요한지 판단한다.

    후보 수가 부족하거나, 상위 점수가 낮거나, issue 직접 매칭과 vector 신호가 약하면 실행한다.
    빠른 경로가 충분히 강한 경우에는 BM25를 생략해 시간을 아낀다.
    """
    if not BM25_ENABLED:
        return False
    if BM25_MODE in {"off", "disabled", "false"}:
        return False
    if BM25_MODE in {"always", "full"}:
        return True

    required_count = min(limit, FINAL_EVIDENCE_LIMIT)
    if len(evidences) < required_count:
        return True

    top_score = max((item.hybrid_score for item in evidences), default=0.0)
    has_issue_match = any(item.chunk.issue_code and item.rerank_score >= 0 for item in evidences)
    has_vector_signal = any(item.vector_score >= 0.01 for item in evidences)
    return top_score < 0.25 or not (has_issue_match or has_vector_signal)


def normalize_rank_score(score: float, rank: int) -> float:
    """원본 점수와 순위를 함께 반영해 점수를 안정화한다.

    점수가 비어 있어도 하위 순위 기본값은 남기므로 병합 과정에서 완전히 0이 되지 않는다.
    """
    return max(float(score or 0.0), 1.0 / (60 + rank))


def source_freshness_bonus(chunk: JobPostingKnowledgeChunk) -> float:
    """최신 자료일수록 작은 가점을 준다."""
    metadata = chunk.metadata_json or {}
    if metadata.get("is_latest") is True:
        return 0.05
    if metadata.get("effective_date"):
        return 0.02
    return 0.0


def retrieval_weights(chunk: JobPostingKnowledgeChunk) -> tuple[float, float]:
    """문서 종류에 따라 text/vector 가중치를 다르게 준다.

    법령 원문은 정확한 문구 일치가 중요해 text 가중치를 높인다.
    가이드와 사례는 의미 유사도가 중요해 vector 비중을 조금 더 높인다.
    """
    source = getattr(chunk, "knowledge_source", None)
    source_type = getattr(source, "source_type", None)
    if source_type == JobPostingKnowledgeSourceType.LAW_TEXT.value:
        return 0.6, 0.4
    if source_type in {
        JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value,
        JobPostingKnowledgeSourceType.LEGAL_MANUAL.value,
        JobPostingKnowledgeSourceType.INSPECTION_CASE.value,
    }:
        return 0.4, 0.6
    return 0.45, 0.55


def rerank_evidence(
    *,
    issue: dict[str, Any],
    evidences: list[RetrievedEvidence],
) -> list[RetrievedEvidence]:
    """법령, 사례, 가이드 우선순위를 반영해 1차 재정렬한다."""
    issue_type = issue.get("issue_type")
    for evidence in evidences:
        chunk = evidence.chunk
        source = getattr(chunk, "knowledge_source", None)
        source_type = getattr(source, "source_type", "") or ""
        legal_bonus = 0.25 if chunk.law_name or chunk.article_no else 0.0
        case_bonus = 0.15 if source_type == JobPostingKnowledgeSourceType.INSPECTION_CASE.value else 0.0
        guide_bonus = 0.1 if source_type in {
            JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value,
            JobPostingKnowledgeSourceType.LEGAL_MANUAL.value,
        } else 0.0
        issue_bonus = 0.2 if chunk.issue_code == issue_type else 0.0
        evidence.rerank_score = evidence.hybrid_score + legal_bonus + case_bonus + guide_bonus + issue_bonus

    evidences.sort(key=lambda item: item.rerank_score, reverse=True)
    return apply_slot_policy(evidences)


def apply_slot_policy(evidences: list[RetrievedEvidence]) -> list[RetrievedEvidence]:
    """근거 구성이 한쪽으로 쏠리지 않게 슬롯 기반으로 재배치한다.

    법령 2개, 가이드 2개, 사례 1개를 우선 확보하려고 시도한다.
    그 뒤 남은 후보를 원래 점수 순서대로 붙인다.
    """
    law = [item for item in evidences if item.chunk.law_name or item.chunk.article_no]
    guide = [
        item
        for item in evidences
        if getattr(getattr(item.chunk, "knowledge_source", None), "source_type", None)
        in {
            JobPostingKnowledgeSourceType.LEGAL_GUIDEBOOK.value,
            JobPostingKnowledgeSourceType.LEGAL_MANUAL.value,
        }
    ]
    case = [
        item
        for item in evidences
        if getattr(getattr(item.chunk, "knowledge_source", None), "source_type", None)
        == JobPostingKnowledgeSourceType.INSPECTION_CASE.value
    ]
    selected: list[RetrievedEvidence] = []
    for bucket, count in ((law, 2), (guide, 2), (case, 1)):
        for item in bucket:
            if item not in selected:
                selected.append(item)
            if len([candidate for candidate in selected if candidate in bucket]) >= count:
                break
    for item in evidences:
        if item not in selected:
            selected.append(item)
    return selected


def apply_model_rerank(*, query: str, evidences: list[RetrievedEvidence]) -> None:
    """상위 후보에만 모델 리랭커를 적용한다.

    휴리스틱 점수 70%, 모델 점수 30% 비율로 합친다.
    모델 점수만 맹신하지 않고 기존 우선순위를 유지하려는 판단이다.
    """
    if not RERANKER_ENABLED or RERANK_CANDIDATE_LIMIT <= 0:
        return
    candidates = evidences[:RERANK_CANDIDATE_LIMIT]
    if len(candidates) <= 1:
        return

    scores = rerank_pairs(query, [item.chunk.content or "" for item in candidates])
    if not scores:
        return
    max_score = max(scores) or 1.0
    min_score = min(scores)
    span = max(max_score - min_score, 1e-9)
    for evidence, score in zip(candidates, scores, strict=False):
        normalized = (score - min_score) / span
        evidence.rerank_score = (evidence.rerank_score * 0.7) + (normalized * 0.3)
        if evidence.matched_terms is None:
            evidence.matched_terms = []
        evidence.matched_terms.append(f"reranker:{current_reranker_model_name()}")
    evidences.sort(key=lambda item: item.rerank_score, reverse=True)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """두 벡터의 코사인 유사도를 0~1 범위로 반환한다."""
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if not left_norm or not right_norm:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))
