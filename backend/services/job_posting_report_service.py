from __future__ import annotations

from typing import Any

from models.job_posting import JobPosting


def build_structured_compliance_report(
    *,
    posting: JobPosting,
    issues: list[dict[str, Any]],
    risk_level: str,
    evidence_strength: int,
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    structured_issues = []
    for issue in issues:
        sources = issue.get("sources") or []
        related_laws = [
            {
                "law_name": source.get("law_name"),
                "article_no": source.get("article_no"),
                "source_title": source.get("title"),
                "chunk_id": source.get("chunk_id"),
            }
            for source in sources
            if source.get("law_name") or source.get("article_no")
        ]
        case_sources = [
            source
            for source in sources
            if "CASE" in str(source.get("chunk_type") or source.get("source_type") or "")
        ]
        structured_issues.append(
            {
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
                "flagged_phrase": issue.get("flagged_text"),
                "why_risky": issue.get("why_risky"),
                "related_laws": related_laws,
                "possible_penalty": find_penalty_text(sources),
                "precedent_or_case": case_sources[0] if case_sources else None,
                "recommended_revision": issue.get("recommended_revision"),
                "evidence_strength": classify_issue_evidence_strength(sources),
                "sources": sources,
            }
        )

    summary = (
        "법적 위반 및 주요 지원율 하락 요인이 발견되지 않는 정상 공고입니다."
        if not issues
        else f"{posting.job_title} 공고에서 {len(issues)}개 리스크가 탐지되었습니다."
    )
    risk_score = {"CLEAN": 0, "LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 90}[risk_level]
    return {
        "risk_level": risk_level,
        "summary": summary,
        "flagged_phrases": [
            {
                "text": issue.get("flagged_text"),
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
            }
            for issue in issues
        ],
        "issues": structured_issues,
        "evidence_strength": evidence_strength,
        "sources": evidence_items,
        "overall_score": max(0, 100 - risk_score),
        "risk_score": risk_score,
        "attractiveness_score": max(
            0,
            92 - len([issue for issue in issues if issue.get("category") == "BRANDING"]) * 12,
        ),
        "disclaimer": (
            "본 결과는 채용공고 문구의 법률 및 공정채용 가이드 리스크를 "
            "사전 점검하기 위한 참고용 분석입니다. 최종 법률 판단 및 공고 게시 결정은 "
            "내부 검토 또는 전문가 자문을 통해 확인해야 합니다."
        ),
    }


def classify_issue_evidence_strength(sources: list[dict[str, Any]]) -> str:
    has_law = any(source.get("law_name") or source.get("article_no") for source in sources)
    has_guide_or_case = any(
        source.get("source_type") in {"LEGAL_GUIDEBOOK", "LEGAL_MANUAL", "INSPECTION_CASE"}
        or "CASE" in str(source.get("chunk_type") or "")
        for source in sources
    )
    if has_law and has_guide_or_case:
        return "HIGH"
    if has_law or has_guide_or_case or len(sources) >= 2:
        return "MEDIUM"
    if sources:
        return "LOW"
    return "INSUFFICIENT"


def calculate_evidence_strength(issues: list[dict[str, Any]]) -> int:
    if not issues:
        return 92
    scores = {
        "HIGH": 90,
        "MEDIUM": 72,
        "LOW": 50,
        "INSUFFICIENT": 35,
    }
    values = [
        scores[classify_issue_evidence_strength(issue.get("sources") or [])]
        for issue in issues
    ]
    return int(sum(values) / max(len(values), 1))


def find_penalty_text(sources: list[dict[str, Any]]) -> str | None:
    for source in sources:
        content = source.get("content") or ""
        if any(keyword in content for keyword in ["벌금", "과태료", "징역", "시정명령"]):
            return content[:500]
    return None


def build_evidence_sufficiency(
    *,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = []
    for issue in issues:
        sources = issue.get("sources") or []
        strength = classify_issue_evidence_strength(sources)
        checks.append(
            {
                "issue_type": issue.get("issue_type"),
                "flagged_text": issue.get("flagged_text"),
                "evidence_count": len(sources),
                "has_law": any(source.get("law_name") or source.get("article_no") for source in sources),
                "has_case": any(
                    source.get("source_type") == "INSPECTION_CASE"
                    or "CASE" in str(source.get("chunk_type") or "")
                    for source in sources
                ),
                "evidence_strength": strength,
                "needs_review": strength in {"LOW", "INSUFFICIENT"},
            }
        )
    return {
        "checks": checks,
        "insufficient_count": len(
            [check for check in checks if check["evidence_strength"] in {"LOW", "INSUFFICIENT"}]
        ),
    }
