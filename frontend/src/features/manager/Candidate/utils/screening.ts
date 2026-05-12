import type {
  DocumentBulkImportPreviewRow,
  ScreeningPreviewResult,
} from "../types";

export const SCREENING_RECOMMENDATION_LABEL: Record<string, string> = {
  RECOMMEND: "추천",
  HOLD: "보류",
  NOT_RECOMMENDED: "비추천",
  NEEDS_REVIEW: "검토 필요",
};

export const SCREENING_DECISION_STATUS_LABEL: Record<string, string> = {
  PENDING: "대기",
  CONFIRMED: "확정",
  HELD: "보류",
  EXCLUDED: "제외",
};

export function formatScreeningRecommendation(value?: string | null) {
  if (!value) {
    return "-";
  }
  return SCREENING_RECOMMENDATION_LABEL[value] ?? value;
}

export function formatScreeningDecisionStatus(value?: string | null) {
  if (!value) {
    return "-";
  }
  return SCREENING_DECISION_STATUS_LABEL[value] ?? value;
}

export function isRecommendedImportRow(row: DocumentBulkImportPreviewRow) {
  return row.status === "READY" && row.screeningPreview?.recommendation === "RECOMMEND";
}

export function getDefaultScreeningSelectedRowIds(rows: DocumentBulkImportPreviewRow[]) {
  return rows.filter(isRecommendedImportRow).map((row) => row.rowId);
}

export function getScreeningPillClassName(screening?: ScreeningPreviewResult | null) {
  switch (screening?.recommendation) {
    case "RECOMMEND":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    case "HOLD":
      return "border-amber-200 bg-amber-50 text-amber-700";
    case "NOT_RECOMMENDED":
      return "border-slate-200 bg-slate-100 text-slate-600";
    case "NEEDS_REVIEW":
      return "border-rose-200 bg-rose-50 text-rose-700";
    default:
      return "border-slate-200 bg-white text-slate-500";
  }
}

export function getScreeningSummary(rows: DocumentBulkImportPreviewRow[]) {
  return rows.reduce(
    (summary, row) => {
      if (row.status === "READY") {
        summary.ready += 1;
      }
      switch (row.screeningPreview?.recommendation) {
        case "RECOMMEND":
          summary.recommended += 1;
          break;
        case "HOLD":
          summary.hold += 1;
          break;
        case "NOT_RECOMMENDED":
          summary.notRecommended += 1;
          break;
        case "NEEDS_REVIEW":
          summary.needsReview += 1;
          break;
        default:
          break;
      }
      return summary;
    },
    {
      ready: 0,
      recommended: 0,
      hold: 0,
      notRecommended: 0,
      needsReview: 0,
    },
  );
}

export const SCREENING_SCORE_CRITERIA = [
  {
    key: "profile_completeness_score",
    label: "프로필 완성도",
    maxScore: 20,
    description: "이름, 연락처, 지원 직무, 요약, 추론 신뢰도",
  },
  {
    key: "document_readiness_score",
    label: "문서 준비도",
    maxScore: 20,
    description: "이력서/경력기술서/포트폴리오 존재, 추출 성공, 추출 품질",
  },
  {
    key: "job_fit_signal_score",
    label: "직무 적합 신호",
    maxScore: 30,
    description: "지원 직무 키워드, 경력/신입 신호, 직무명 직접 매칭",
  },
  {
    key: "evidence_quality_score",
    label: "근거 품질",
    maxScore: 20,
    description: "성과 수치, 역할, 프로젝트 등 구체적 근거",
  },
  {
    key: "risk_adjustment_score",
    label: "리스크 조정",
    maxScore: 10,
    minScore: -20,
    description: "중복, 오류, 경고, 직무 무관 개인정보 후보 감점",
  },
] as const;

export function getScreeningScoreValue(
  screening: ScreeningPreviewResult,
  key: string,
) {
  const value = screening.scoreBreakdown[key];
  return typeof value === "number" ? value : null;
}

export function getScreeningRiskEvidence(screening: ScreeningPreviewResult) {
  const riskBreakdown = screening.scoreBreakdown.risk;
  const risk =
    riskBreakdown && typeof riskBreakdown === "object"
      ? (riskBreakdown as Record<string, unknown>)
      : {};
  const sensitiveTerms = Array.isArray(risk.sensitive_terms)
    ? risk.sensitive_terms.filter((item): item is string => typeof item === "string")
    : [];

  return {
    duplicateCandidateId:
      typeof risk.duplicate_candidate_id === "number" ? risk.duplicate_candidate_id : null,
    errorCount: typeof risk.error_count === "number" ? risk.error_count : 0,
    warningCount: typeof risk.warning_count === "number" ? risk.warning_count : 0,
    sensitiveTerms,
  };
}
