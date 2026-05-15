import { AlertTriangle, ArrowLeft, CheckCircle2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { MetricCard } from "../components/JobPostingFields";
import { JobProgressCard } from "../components/JobProgressCard";
import {
  fetchJobPostingExperimentJob,
  fetchJobPostingExperimentRun,
} from "../services/jobPostingService";
import type {
  JobPostingAiJob,
  JobPostingExperimentCaseResult,
  JobPostingExperimentRun,
} from "../types";
import {
  formatDateTime,
  formatDurationMs,
  formatPercent,
  inputClassName,
  riskStyle,
} from "../utils/display";
import { useJobPolling } from "../hooks/useJobPolling";

export function JobPostingExperimentDetailPage() {
  const { runId } = useParams();
  const [run, setRun] = useState<JobPostingExperimentRun | null>(null);
  const [caseResults, setCaseResults] = useState<JobPostingExperimentCaseResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [keyword, setKeyword] = useState("");

  const load = useCallback(async () => {
    const id = Number(runId);
    if (!id) return;
    setIsLoading(true);
    setErrorMessage("");
    try {
      const data = await fetchJobPostingExperimentRun(id);
      setRun(data.run);
      setCaseResults(data.caseResults);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "실험 상세 결과를 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [runId]);

  const { job, startPolling } = useJobPolling({
    fetcher: fetchJobPostingExperimentJob,
    onCompleted: async () => {
      await load();
    },
    onFailed: async () => {
      await load();
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "실험 상태를 확인하지 못했습니다.");
    },
  });

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (
      run?.aiJobId &&
      run.status !== "SUCCESS" &&
      run.status !== "FAILED"
    ) {
      startPolling({
        jobId: run.aiJobId,
        status: "RUNNING",
        jobType: "JOB_POSTING_EXPERIMENT_RUN",
        targetType: null,
        targetId: run.id,
        progress: 10,
        currentStep: "experiment_running",
        errorMessage: null,
        requestPayload: { experiment_run_id: run.id },
        resultPayload: null,
        message: "실험 진행 중",
      });
    }
  }, [run?.aiJobId, run?.id, run?.status, startPolling]);

  const filteredCases = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    if (!normalized) return caseResults;
    return caseResults.filter((item) => {
      const haystack = [
        item.caseId,
        item.jobGroup ?? "",
        item.expectedLabel ?? "",
        item.predictedLabel ?? "",
        ...(item.expectedRiskTypes ?? []),
        ...(item.predictedRiskTypes ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [caseResults, keyword]);

  const failedCases = useMemo(
    () =>
      caseResults.filter(
        (item) =>
          item.status === "FAILED" ||
          item.expectedLabel !== item.predictedLabel ||
          item.sourceOmitted === true ||
          item.retrievalHitAt5 === false,
      ),
    [caseResults],
  );

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Experiment Detail"
        title={run?.title ?? "RAG 실험 상세"}
        description="실험별 핵심 지표와 케이스 단위 결과를 함께 보면서, 어떤 개선이 실제로 품질을 올렸는지 설명할 수 있게 구성했습니다."
        actions={
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void load()}
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              새로고침
            </button>
            <Link
              to="/manager/job-posting-experiments"
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
            >
              <ArrowLeft className="h-4 w-4" />
              실험 목록
            </Link>
          </div>
        }
      />

      {job ? <JobProgressCard job={job} /> : null}
      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Status" value={run?.status ?? "-"} tone={riskStyle(run?.status === "FAILED" ? "CRITICAL" : run?.status === "SUCCESS" ? "CLEAN" : "MEDIUM")} />
        <MetricCard label="Recall@5" value={formatPercent(run?.retrievalRecallAt5)} />
        <MetricCard label="Macro F1" value={formatPercent(run?.macroF1)} />
        <MetricCard label="High-risk Recall" value={formatPercent(run?.highRiskRecall)} />
        <MetricCard label="Source Omission" value={formatPercent(run?.sourceOmissionRate)} />
        <MetricCard label="Avg Latency" value={formatDurationMs(run?.avgLatencyMs)} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-lg font-bold text-slate-950">실험 개요</div>
              <p className="mt-1 text-sm text-slate-500">
                {run?.description || "설명 없이 실행된 실험입니다."}
              </p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(run?.status === "FAILED" ? "CRITICAL" : run?.status === "SUCCESS" ? "CLEAN" : "MEDIUM")}`}>
              {run?.datasetName ?? "-"} · {run?.totalCases ?? 0} cases
            </span>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <InfoLine label="실행 시각" value={formatDateTime(run?.createdAt)} />
            <InfoLine label="완료 시각" value={formatDateTime(run?.completedAt)} />
            <InfoLine label="성공 케이스" value={`${run?.completedCases ?? 0}건`} />
            <InfoLine label="실패 케이스" value={`${run?.failedCases ?? 0}건`} />
          </div>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-white/80 p-4">
            <div className="text-sm font-bold text-slate-950">핵심 해석 포인트</div>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
              <li>검색 품질은 `Recall@5`로, 정답 근거를 상위 5개 안에 얼마나 끌어왔는지 봅니다.</li>
              <li>최종 판정 품질은 `Macro F1`과 `High-risk Recall`로, 전체 균형과 위험 케이스 미탐을 함께 봅니다.</li>
              <li>근거 신뢰성은 `Source Omission Rate`로, 판정을 냈는데 출처가 빠진 경우를 추적합니다.</li>
            </ul>
          </div>
        </article>

        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="flex items-center gap-2">
            {failedCases.length > 0 ? (
              <AlertTriangle className="h-5 w-5 text-amber-600" />
            ) : (
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            )}
            <div className="text-lg font-bold text-slate-950">실패/주의 케이스</div>
          </div>
          <div className="mt-4 space-y-3">
            {failedCases.slice(0, 8).map((item) => (
              <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-semibold text-slate-950">{item.caseId}</div>
                  <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(item.status === "FAILED" ? "CRITICAL" : item.retrievalHitAt5 === false ? "HIGH" : item.sourceOmitted ? "MEDIUM" : "LOW")}`}>
                    {item.status}
                  </span>
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  expected {item.expectedLabel ?? "-"} / predicted {item.predictedLabel ?? "-"}
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <Badge label={`retrieval ${item.retrievalHitAt5 ? "hit" : "miss"}`} tone={item.retrievalHitAt5 ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-rose-200 bg-rose-50 text-rose-700"} />
                  <Badge label={`source ${item.sourceOmitted ? "omitted" : "grounded"}`} tone={item.sourceOmitted ? "border-amber-200 bg-amber-50 text-amber-700" : "border-sky-200 bg-sky-50 text-sky-700"} />
                  <Badge label={formatDurationMs(item.latencyMs)} tone="border-slate-200 bg-slate-50 text-slate-600" />
                </div>
                {item.errorMessage ? (
                  <div className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-700">
                    {item.errorMessage}
                  </div>
                ) : null}
              </div>
            ))}
            {!isLoading && failedCases.length === 0 ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-10 text-center text-sm text-emerald-800">
                현재 상세 기준으로 분류 불일치, retrieval miss, 출처 누락 케이스가 없습니다.
              </div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-lg font-bold text-slate-950">케이스별 결과</div>
            <p className="mt-1 text-sm text-slate-500">
              검색 hit 여부와 출처 누락 여부까지 같이 보면서 개선 포인트를 추적합니다.
            </p>
          </div>
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="case id, job group, risk type 검색"
            className={`${inputClassName} md:w-88`}
          />
        </div>

        <div className="mt-5 overflow-hidden rounded-2xl border border-[var(--line)] bg-white/70">
          <table className="w-full min-w-[1180px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
              <tr>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Expected</th>
                <th className="px-4 py-3">Predicted</th>
                <th className="px-4 py-3">Expected Risks</th>
                <th className="px-4 py-3">Predicted Risks</th>
                <th className="px-4 py-3">Recall@5</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCases.map((item) => (
                <tr key={item.id} className="transition hover:bg-[#f5f8ff]">
                  <td className="px-4 py-4">
                    <div className="font-semibold text-slate-950">{item.caseId}</div>
                    <div className="mt-1 text-xs text-slate-500">{item.jobGroup || "-"}</div>
                  </td>
                  <td className="px-4 py-4 text-slate-700">{item.expectedLabel || "-"}</td>
                  <td className="px-4 py-4 text-slate-700">{item.predictedLabel || "-"}</td>
                  <td className="px-4 py-4 text-slate-600">{(item.expectedRiskTypes || []).join(", ") || "-"}</td>
                  <td className="px-4 py-4 text-slate-600">{(item.predictedRiskTypes || []).join(", ") || "-"}</td>
                  <td className="px-4 py-4">
                    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${item.retrievalHitAt5 ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-rose-200 bg-rose-50 text-rose-700"}`}>
                      {item.retrievalHitAt5 ? "hit" : "miss"}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${item.sourceOmitted ? "border-amber-200 bg-amber-50 text-amber-700" : "border-sky-200 bg-sky-50 text-sky-700"}`}>
                      {item.sourceOmitted ? "omitted" : "grounded"}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-slate-700">{formatDurationMs(item.latencyMs)}</td>
                  <td className="px-4 py-4">
                    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(item.status === "FAILED" ? "CRITICAL" : item.status === "SUCCESS" ? "CLEAN" : "MEDIUM")}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
              {!isLoading && filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-sm text-slate-500">
                    조건에 맞는 케이스 결과가 없습니다.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function InfoLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function Badge({ label, tone }: { label: string; tone: string }) {
  return <span className={`rounded-full border px-3 py-1 font-semibold ${tone}`}>{label}</span>;
}
