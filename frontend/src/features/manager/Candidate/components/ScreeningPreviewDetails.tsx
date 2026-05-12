import type { ScreeningPreviewResult } from "../types";
import {
  getScreeningRiskEvidence,
  getScreeningScoreValue,
  SCREENING_SCORE_CRITERIA,
} from "../utils/screening";

interface ScreeningPreviewDetailsProps {
  screening: ScreeningPreviewResult | null;
}

export function ScreeningPreviewDetails({ screening }: ScreeningPreviewDetailsProps) {
  if (!screening) {
    return <span className="text-xs text-slate-400">선별 결과 없음</span>;
  }

  const riskEvidence = getScreeningRiskEvidence(screening);

  return (
    <div className="min-w-[260px] max-w-[360px]">
      <details className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
        <summary className="cursor-pointer text-xs font-bold text-slate-700">
          정량 기준 / 리스크 근거
        </summary>

        <div className="mt-3 space-y-2">
          {SCREENING_SCORE_CRITERIA.map((criterion) => {
            const score = getScreeningScoreValue(screening, criterion.key);
            const scoreRange =
              "minScore" in criterion
                ? `${criterion.minScore}~+${criterion.maxScore}`
                : `0~${criterion.maxScore}`;

            return (
              <div
                key={criterion.key}
                className="rounded-lg border border-slate-100 bg-white px-3 py-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-bold text-slate-600">{criterion.label}</p>
                  <p className="text-xs font-bold text-slate-900">
                    {score ?? "-"} / {scoreRange}
                  </p>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {criterion.description}
                </p>
              </div>
            );
          })}

          <div className="rounded-lg border border-rose-100 bg-rose-50 px-3 py-2">
            <p className="text-xs font-bold text-rose-700">리스크 근거</p>
            <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-slate-700">
              <span>중복: {riskEvidence.duplicateCandidateId ?? "-"}</span>
              <span>오류: {riskEvidence.errorCount}</span>
              <span>경고: {riskEvidence.warningCount}</span>
              <span>민감 신호: {riskEvidence.sensitiveTerms.length}</span>
            </div>
            {screening.riskFactors.length > 0 ? (
              <ul className="mt-2 space-y-1 text-xs leading-5 text-rose-700">
                {screening.riskFactors.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
            {screening.missingEvidence.length > 0 ? (
              <ul className="mt-2 space-y-1 text-xs leading-5 text-amber-700">
                {screening.missingEvidence.slice(0, 3).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      </details>
    </div>
  );
}
