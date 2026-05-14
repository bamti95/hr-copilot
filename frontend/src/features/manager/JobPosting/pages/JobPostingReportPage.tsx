import { AlertTriangle, ArrowLeft, CheckCircle2, FileText } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { MetricCard } from "../components/JobPostingFields";
import {
  fetchJobPosting,
  fetchJobPostingReport,
  fetchJobPostingReports,
} from "../services/jobPostingService";
import type {
  EvidenceSource,
  JobPostingAnalysisReport,
  JobPostingImprovementSuggestion,
  JobPostingIssue,
  JobPostingResponse,
} from "../types";
import {
  formatScore,
  riskStyle,
  toEvidenceList,
  toImprovementSuggestionList,
  toIssueList,
} from "../utils/display";

export function JobPostingReportPage() {
  const { postingId } = useParams();
  const reportId = new URLSearchParams(window.location.search).get("reportId");
  const [posting, setPosting] = useState<JobPostingResponse | null>(null);
  const [report, setReport] = useState<JobPostingAnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const id = Number(postingId);
    const rid = Number(reportId);
    if (!id) return;
    async function load() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const [postingData, reportData] = await Promise.all([
          fetchJobPosting(id),
          rid
            ? fetchJobPostingReport(rid)
            : fetchJobPostingReports(id).then((rows) => rows[0]),
        ]);
        setPosting(postingData);
        setReport(reportData ?? null);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "분석 리포트를 불러오지 못했습니다.",
        );
      } finally {
        setIsLoading(false);
      }
    }
    void load();
  }, [postingId, reportId]);

  const issues = useMemo(() => toIssueList(report?.issueSummary ?? null), [report]);
  const evidence = useMemo(
    () => toEvidenceList(report?.matchedEvidence ?? null),
    [report],
  );
  const suggestions = useMemo(
    () => toImprovementSuggestionList(report?.improvementSuggestions ?? null),
    [report],
  );

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Analysis Report"
        title={posting?.jobTitle ?? "분석 리포트"}
        description="기본 리스크 평가 결과입니다. 위험 문구와 추천 수정안, keyword 기반 매칭 근거를 함께 확인합니다."
        actions={
          <Link
            to={`/manager/job-postings/${postingId}`}
            className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
          >
            <ArrowLeft className="h-4 w-4" />
            공고 상세
          </Link>
        }
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          label="위험 등급"
          value={report?.riskLevel ?? "-"}
          tone={riskStyle(report?.riskLevel)}
        />
        <MetricCard label="감지 이슈" value={`${report?.issueCount ?? 0}건`} />
        <MetricCard label="법적 위반 후보" value={`${report?.violationCount ?? 0}건`} />
        <MetricCard
          label="종합 점수"
          value={formatScore(report?.overallScore)}
        />
        <MetricCard
          label="리스크 점수"
          value={formatScore(report?.riskScore)}
        />
        <MetricCard
          label="신뢰도"
          value={`${report?.confidenceScore ?? "-"}${report?.confidenceScore ? "%" : ""}`}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <div className="space-y-4">
          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <div className="flex items-center gap-2">
              {report?.riskLevel === "CLEAN" ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-amber-600" />
              )}
              <h2 className="m-0 text-lg font-bold text-slate-950">요약</h2>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              {isLoading
                ? "불러오는 중..."
                : report?.summaryText || "요약 정보가 없습니다."}
            </p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-xs leading-5 text-slate-500">
              분석 파이프라인:{" "}
              {report?.pipelineVersion ?? "job-posting-compliance-rag-v1"} · 모델:{" "}
              {report?.modelName ?? "rule-rag-baseline"}
            </div>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <h2 className="m-0 text-lg font-bold text-slate-950">위험 문구 및 수정안</h2>
            <div className="mt-4 space-y-3">
              {issues.map((issue, index) => (
                <IssueCard
                  key={`${issue.issueType}-${index}`}
                  issue={issue}
                  suggestion={findSuggestion(issue, suggestions)}
                />
              ))}
              {!isLoading && issues.length === 0 ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-10 text-center text-sm text-emerald-800">
                  감지된 주요 리스크가 없습니다.
                </div>
              ) : null}
            </div>
          </article>
        </div>

        <aside className="space-y-4">
          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-[#315fbc]" />
              <h2 className="m-0 text-lg font-bold text-slate-950">매칭 근거</h2>
            </div>
            <div className="mt-4 space-y-3">
              {evidence.slice(0, 8).map((item, index) => (
                <EvidenceCard
                  key={`${item.chunkId ?? index}`}
                  evidence={item}
                />
              ))}
              {!isLoading && evidence.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
                  매칭된 근거 chunk가 없습니다.
                </div>
              ) : null}
            </div>
          </article>
        </aside>
      </section>
    </div>
  );
}

function IssueCard({
  issue,
  suggestion,
}: {
  issue: JobPostingIssue;
  suggestion: JobPostingImprovementSuggestion | null;
}) {
  const sources = issue.sources ?? [];
  const evidenceStrength = suggestion?.evidenceStrength;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(issue.severity)}`}
          >
            {issue.severity || "RISK"}
          </span>
          <span className="text-sm font-bold text-slate-950">
            {issue.issueType || "UNKNOWN"}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-500">
          {typeof issue.confidence === "number" ? (
            <span className="rounded-full bg-slate-100 px-2 py-1">
              탐지 신뢰도 {issue.confidence}%
            </span>
          ) : null}
          {evidenceStrength ? (
            <span className="rounded-full bg-[#edf4ff] px-2 py-1 text-[#315fbc]">
              근거 강도 {evidenceStrength}
            </span>
          ) : null}
        </div>
      </div>

      <blockquote className="mt-3 rounded-xl border-l-4 border-[#315fbc] bg-[#f5f8ff] px-4 py-3 text-sm text-slate-700">
        {issue.flaggedText || "문구 정보 없음"}
      </blockquote>

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border border-rose-100 bg-rose-50/60 px-4 py-3">
          <div className="text-xs font-bold text-rose-700">위험 판단</div>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {issue.whyRisky || "위험 사유가 제공되지 않았습니다."}
          </p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
          <div className="text-xs font-bold text-emerald-800">개선 제안</div>
          <p className="mt-2 text-sm leading-6 text-emerald-950">
            {suggestion?.recommendedRevision ||
              issue.recommendedRevision ||
              "수정 예시가 제공되지 않았습니다."}
          </p>
        </div>
      </div>

      {sources.length > 0 ? (
        <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3">
          <div className="text-xs font-bold text-slate-700">이 문구에 연결된 근거</div>
          <div className="mt-2 space-y-2">
            {sources.slice(0, 3).map((source, index) => (
              <EvidenceSummary key={`${source.chunkId ?? index}`} evidence={source} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function EvidenceSummary({ evidence }: { evidence: EvidenceSource }) {
  return (
    <div className="rounded-lg bg-white px-3 py-2 text-xs text-slate-600">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold text-slate-900">
          {evidence.title || evidence.lawName || "근거 문서"}
        </span>
        <span className="font-bold text-[#315fbc]">
          {formatScore(evidence.score ?? evidence.rerankScore ?? evidence.hybridScore)}
        </span>
      </div>
      <div className="mt-1">
        {[evidence.lawName, evidence.articleNo || evidence.articleRef, evidence.sectionTitle]
          .filter(Boolean)
          .join(" · ") || evidence.chunkType || "-"}
      </div>
    </div>
  );
}

function EvidenceCard({ evidence }: { evidence: EvidenceSource }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold text-slate-950">
            {evidence.title || evidence.lawName || "근거 문서"}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {[evidence.lawName, evidence.articleNo || evidence.articleRef, evidence.sectionTitle]
              .filter(Boolean)
              .join(" · ") || evidence.chunkType || "-"}
          </div>
        </div>
        <span className="rounded-full bg-[#edf4ff] px-2 py-1 text-xs font-bold text-[#315fbc]">
          {formatScore(evidence.score ?? evidence.rerankScore ?? evidence.hybridScore)}
        </span>
      </div>

      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <ScoreChip label="hybrid" value={evidence.hybridScore} />
        <ScoreChip label="rerank" value={evidence.rerankScore} />
        <ScoreChip label="text" value={evidence.textScore} />
        <ScoreChip label="vector" value={evidence.vectorScore} />
      </div>

      {evidence.matchedTerms?.length ? (
        <div className="mt-3 flex flex-wrap gap-1">
          {evidence.matchedTerms.slice(0, 6).map((term) => (
            <span
              key={term}
              className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600"
            >
              {term}
            </span>
          ))}
        </div>
      ) : null}

      <p className="mt-3 line-clamp-6 text-xs leading-5 text-slate-600">
        {evidence.content || "근거 내용 없음"}
      </p>
    </div>
  );
}

function ScoreChip({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 px-2 py-1.5">
      <span className="font-semibold text-slate-500">{label}</span>{" "}
      <span className="font-bold text-slate-900">{formatScore(value)}</span>
    </div>
  );
}

function findSuggestion(
  issue: JobPostingIssue,
  suggestions: JobPostingImprovementSuggestion[],
) {
  return (
    suggestions.find(
      (suggestion) =>
        suggestion.issueType === issue.issueType &&
        suggestion.flaggedText === issue.flaggedText,
    ) ??
    suggestions.find((suggestion) => suggestion.issueType === issue.issueType) ??
    null
  );
}
