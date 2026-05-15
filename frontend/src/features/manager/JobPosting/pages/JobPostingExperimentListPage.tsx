import { FlaskConical, Play, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { JobProgressCard } from "../components/JobProgressCard";
import {
  createJobPostingExperimentRun,
  fetchJobPostingExperimentJob,
  fetchJobPostingExperimentRuns,
  submitJobPostingExperimentRunJob,
} from "../services/jobPostingService";
import type {
  JobPostingAiJob,
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

const ACTIVE_EXPERIMENT_JOB_KEY = "hrCopilot.activeJobPostingExperimentJob";

function readStoredExperimentJob(): JobPostingAiJob | null {
  const raw = window.localStorage.getItem(ACTIVE_EXPERIMENT_JOB_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as JobPostingAiJob;
  } catch {
    return null;
  }
}

function storeExperimentJob(job: JobPostingAiJob | null) {
  if (!job) {
    window.localStorage.removeItem(ACTIVE_EXPERIMENT_JOB_KEY);
    return;
  }
  window.localStorage.setItem(ACTIVE_EXPERIMENT_JOB_KEY, JSON.stringify(job));
}

export function JobPostingExperimentListPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<JobPostingExperimentRun[]>([]);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadRuns = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const data = await fetchJobPostingExperimentRuns({ page, size: 10 });
      setItems(data.items);
      setTotalPages(data.totalPages);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "실험 목록을 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  const handleCompleted = useCallback(async () => {
    storeExperimentJob(null);
    setSuccessMessage("실험 배치 실행이 완료되었습니다.");
    await loadRuns();
  }, [loadRuns]);

  const handleFailed = useCallback((job: JobPostingAiJob) => {
    storeExperimentJob(job);
    setErrorMessage(job.errorMessage || "실험 실행이 실패했습니다.");
  }, []);

  const { job, startPolling, clearJob } = useJobPolling({
    fetcher: fetchJobPostingExperimentJob,
    onCompleted: handleCompleted,
    onFailed: handleFailed,
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "실험 작업 상태 확인에 실패했습니다.");
    },
  });

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    const stored = readStoredExperimentJob();
    if (stored) {
      startPolling(stored);
    }
  }, [startPolling]);

  const activeRunId = useMemo(() => {
    const payload = job?.requestPayload;
    const runId = payload?.experiment_run_id ?? payload?.experimentRunId;
    return typeof runId === "number" ? runId : typeof runId === "string" ? Number(runId) : null;
  }, [job]);

  const handleCreateAndRun = useCallback(async () => {
    if (!title.trim()) {
      setErrorMessage("실험 제목을 입력해 주세요.");
      return;
    }
    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const run = await createJobPostingExperimentRun({
        title: title.trim(),
        description: description.trim() || null,
        datasetName: "job_posting_risk_50",
        experimentType: "RAG_EVAL",
      });
      const createdJob = await submitJobPostingExperimentRunJob(run.id);
      storeExperimentJob(createdJob);
      startPolling(createdJob);
      setTitle("");
      setDescription("");
      setSuccessMessage(`"${run.title}" 실험을 시작했습니다.`);
      await loadRuns();
      navigate(`/manager/job-posting-experiments/${run.id}`);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "실험 생성 또는 실행에 실패했습니다.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }, [description, loadRuns, navigate, startPolling, title]);

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="RAG Experiment Lab"
        title="채용공고 RAG 실험 기록"
        description="50건 고정 평가셋을 반복 실행하면서 검색 성능, 최종 판정 성능, 출처 기반성을 같은 형식으로 기록합니다."
        actions={
          <Link
            to="/manager/job-postings"
            className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
          >
            <FlaskConical className="h-4 w-4" />
            채용공고 점검
          </Link>
        }
      />

      <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <div className="space-y-4">
            <div>
              <div className="text-sm font-bold text-slate-950">새 실험 실행</div>
              <p className="mt-1 text-sm leading-6 text-slate-500">
                예: `baseline`, `query rewrite v1`, `reranker 적용`. 제목 자체가 포트폴리오의 실험 히스토리가 됩니다.
              </p>
            </div>
            <div className="grid gap-3">
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Experiment Title
                </span>
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="예: 첫번째 실험"
                  className={`${inputClassName} mt-2`}
                />
              </label>
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Notes
                </span>
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="예: query rewrite 추가 전 baseline 측정"
                  className="mt-2 min-h-28 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-3 text-sm text-[var(--text)] outline-none transition focus:border-[var(--primary)]"
                />
              </label>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void handleCreateAndRun()}
                disabled={isSubmitting}
                className="inline-flex h-11 items-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)] disabled:opacity-60"
              >
                <Play className="h-4 w-4" />
                생성 후 실행
              </button>
              <button
                type="button"
                onClick={() => void loadRuns()}
                className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                목록 새로고침
              </button>
            </div>
          </div>

          <div className="rounded-[24px] border border-[#d9e6ff] bg-linear-to-br from-[#f8fbff] via-white to-[#eef4ff] p-5">
            <div className="text-sm font-bold text-slate-950">평가셋 및 핵심 지표</div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <SummaryStat label="Dataset" value="job_posting_risk_50" />
              <SummaryStat label="Cases" value="50 fixed cases" />
              <SummaryStat label="Search" value="Recall@5" />
              <SummaryStat label="Decision" value="Macro F1 / High-risk Recall" />
              <SummaryStat label="Grounding" value="Source Omission Rate" />
              <SummaryStat label="Goal" value="반복 개선 증명" />
            </div>
          </div>
        </div>

        {job ? (
          <div className="mt-5 space-y-3">
            <JobProgressCard job={job} />
            <div className="flex items-center gap-3">
              {activeRunId ? (
                <Link
                  to={`/manager/job-posting-experiments/${activeRunId}`}
                  className="text-sm font-semibold text-[#315fbc]"
                >
                  실행 중인 실험 상세 보기
                </Link>
              ) : null}
              <button
                type="button"
                onClick={() => {
                  clearJob();
                  storeExperimentJob(null);
                }}
                className="text-xs font-semibold text-slate-500"
              >
                진행 카드 닫기
              </button>
            </div>
          </div>
        ) : null}

        {errorMessage ? (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </div>
        ) : null}
        {successMessage ? (
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {successMessage}
          </div>
        ) : null}
      </section>

      <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-lg font-bold text-slate-950">실험 이력</div>
            <p className="mt-1 text-sm text-slate-500">
              같은 50건 평가셋을 기준으로 반복 측정한 run 목록입니다.
            </p>
          </div>
        </div>

        <div className="mt-5 overflow-hidden rounded-2xl border border-[var(--line)] bg-white/70">
          <table className="w-full min-w-[1080px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
              <tr>
                <th className="px-4 py-3">실험</th>
                <th className="px-4 py-3">상태</th>
                <th className="px-4 py-3">Recall@5</th>
                <th className="px-4 py-3">Macro F1</th>
                <th className="px-4 py-3">High-risk Recall</th>
                <th className="px-4 py-3">Source Omission</th>
                <th className="px-4 py-3">Avg Latency</th>
                <th className="px-4 py-3">실행일</th>
                <th className="px-4 py-3 text-right">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.id} className="transition hover:bg-[#f5f8ff]">
                  <td className="px-4 py-4">
                    <div className="font-semibold text-slate-950">{item.title}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {item.datasetName} · {item.totalCases || 0} cases
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(item.status === "FAILED" ? "CRITICAL" : item.status === "SUCCESS" ? "CLEAN" : "MEDIUM")}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-slate-700">{formatPercent(item.retrievalRecallAt5)}</td>
                  <td className="px-4 py-4 text-slate-700">{formatPercent(item.macroF1)}</td>
                  <td className="px-4 py-4 text-slate-700">{formatPercent(item.highRiskRecall)}</td>
                  <td className="px-4 py-4 text-slate-700">{formatPercent(item.sourceOmissionRate)}</td>
                  <td className="px-4 py-4 text-slate-700">{formatDurationMs(item.avgLatencyMs)}</td>
                  <td className="px-4 py-4 text-slate-500">{formatDateTime(item.createdAt)}</td>
                  <td className="px-4 py-4 text-right">
                    <Link
                      to={`/manager/job-posting-experiments/${item.id}`}
                      className="rounded-xl border border-[#315fbc]/20 bg-[#edf4ff] px-3 py-2 text-xs font-semibold text-[#315fbc] transition hover:bg-[#dfeaff]"
                    >
                      상세 보기
                    </Link>
                  </td>
                </tr>
              ))}
              {!isLoading && items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-sm text-slate-500">
                    아직 생성된 실험 run이 없습니다. 위에서 첫 번째 실험을 실행해 보세요.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
          <span>
            {isLoading ? "불러오는 중..." : `페이지 ${page + 1} / ${Math.max(totalPages, 1)}`}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 0}
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 disabled:opacity-40"
            >
              이전
            </button>
            <button
              type="button"
              disabled={totalPages > 0 ? page + 1 >= totalPages : true}
              onClick={() => setPage((current) => current + 1)}
              className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 disabled:opacity-40"
            >
              다음
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/80 px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-sm font-bold text-slate-950">{value}</div>
    </div>
  );
}

export default JobPostingExperimentListPage;
