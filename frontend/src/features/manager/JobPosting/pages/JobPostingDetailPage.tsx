import { ArrowLeft, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { JobProgressCard as SharedJobProgressCard } from "../components/JobProgressCard";
import { Info } from "../components/JobPostingFields";
import {
  fetchActiveAnalysisJob,
  fetchAnalysisJob,
  fetchJobPosting,
  fetchJobPostingReports,
  submitExistingAnalysisJob,
} from "../services/jobPostingService";
import type {
  JobPostingAiJob,
  JobPostingAnalysisReport,
  JobPostingResponse,
} from "../types";
import { formatDateTime, riskStyle } from "../utils/display";
import { useJobPolling } from "../hooks/useJobPolling";

const ACTIVE_ANALYSIS_JOB_KEY = "hrCopilot.activeJobPostingAnalysisJob";

function readStoredAnalysisJob(postingId: number): JobPostingAiJob | null {
  try {
    const raw = window.localStorage.getItem(ACTIVE_ANALYSIS_JOB_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<JobPostingAiJob>;
    const targetId = Number(parsed.targetId ?? parsed.resultPayload?.job_posting_id);
    return typeof parsed.jobId === "number" &&
      typeof parsed.status === "string" &&
      targetId === postingId
      ? (parsed as JobPostingAiJob)
      : null;
  } catch {
    return null;
  }
}

function storeAnalysisJob(job: JobPostingAiJob | null) {
  try {
    if (job) {
      window.localStorage.setItem(ACTIVE_ANALYSIS_JOB_KEY, JSON.stringify(job));
    } else {
      window.localStorage.removeItem(ACTIVE_ANALYSIS_JOB_KEY);
    }
  } catch {
    // Best-effort refresh recovery only.
  }
}

export function JobPostingDetailPage() {
  const navigate = useNavigate();
  const { postingId } = useParams();
  const id = Number(postingId);
  const [posting, setPosting] = useState<JobPostingResponse | null>(null);
  const [reports, setReports] = useState<JobPostingAnalysisReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleAnalysisCompleted = useCallback(
    (completedJob: JobPostingAiJob) => {
      const reportId = Number(
        completedJob.resultPayload?.job_posting_analysis_report_id,
      );
      setIsAnalyzing(false);
      storeAnalysisJob(null);
      if (!reportId) {
        setErrorMessage("재분석 리포트 정보를 찾지 못했습니다.");
        return;
      }
      navigate(`/manager/job-postings/${id}/report?reportId=${reportId}`);
    },
    [id, navigate],
  );

  const {
    job: activeJob,
    startPolling: startAnalysisPolling,
    clearJob: clearAnalysisJob,
  } = useJobPolling({
    fetcher: fetchAnalysisJob,
    onCompleted: handleAnalysisCompleted,
    onFailed: (failedJob) => {
      setIsAnalyzing(false);
      storeAnalysisJob(null);
      setErrorMessage(failedJob.errorMessage || "재분석 작업이 실패했습니다.");
    },
    onError: (error) => {
      setIsAnalyzing(false);
      setErrorMessage(
        error instanceof Error ? error.message : "작업 상태를 불러오지 못했습니다.",
      );
    },
  });

  const load = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setErrorMessage("");
    try {
      const [postingData, reportData] = await Promise.all([
        fetchJobPosting(id),
        fetchJobPostingReports(id),
      ]);
      setPosting(postingData);
      setReports(reportData);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "채용공고 상세를 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const storedJob = readStoredAnalysisJob(id);
    if (storedJob) {
      setIsAnalyzing(true);
      startAnalysisPolling(storedJob);
    }
    void fetchActiveAnalysisJob(id)
      .then((activeJob) => {
        if (cancelled || !activeJob) return;
        storeAnalysisJob(activeJob);
        setIsAnalyzing(true);
        startAnalysisPolling(activeJob);
      })
      .catch(() => {
        // Local storage recovery is enough when the active-job probe is delayed.
      });
    return () => {
      cancelled = true;
    };
  }, [id, startAnalysisPolling]);

  async function handleAnalyzeExisting() {
    setIsAnalyzing(true);
    setErrorMessage("");
    clearAnalysisJob();
    try {
      const submittedJob = await submitExistingAnalysisJob(id);
      storeAnalysisJob(submittedJob);
      startAnalysisPolling(submittedJob);
    } catch (error) {
      setIsAnalyzing(false);
      setErrorMessage(
        error instanceof Error ? error.message : "재분석을 실행하지 못했습니다.",
      );
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Job Posting Detail"
        title={posting?.jobTitle ?? "채용공고 상세"}
        description="공고 원문과 Rule-RAG Baseline 분석 이력을 확인하고, 필요하면 동일 공고를 다시 평가할 수 있습니다."
        actions={
          <>
            <Link
              to="/manager/job-postings"
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
            >
              <ArrowLeft className="h-4 w-4" />
              목록
            </Link>
            <button
              type="button"
              disabled={isAnalyzing || !posting}
              onClick={() => void handleAnalyzeExisting()}
              className="inline-flex h-11 items-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white disabled:opacity-60"
            >
              <RefreshCw className={`h-4 w-4 ${isAnalyzing ? "animate-spin" : ""}`} />
              재분석
            </button>
          </>
        }
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}
      {activeJob ? <SharedJobProgressCard job={activeJob} /> : null}

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="grid gap-3 text-sm text-slate-600 md:grid-cols-4">
            <Info label="회사" value={posting?.companyName || "-"} />
            <Info label="직무군" value={posting?.targetJob || "-"} />
            <Info label="고용형태" value={posting?.employmentType || "-"} />
            <Info label="처우" value={posting?.salaryText || "-"} />
          </div>
          <div className="mt-5 rounded-2xl border border-slate-200 bg-white/80 p-4">
            <h2 className="m-0 text-base font-bold text-slate-950">공고 원문</h2>
            <pre className="mt-3 max-h-[560px] overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-700">
              {isLoading ? "불러오는 중..." : posting?.postingText}
            </pre>
          </div>
        </article>

        <aside className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <h2 className="m-0 text-base font-bold text-slate-950">분석 리포트</h2>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            최신 분석 결과부터 표시합니다. 상세 화면에서 위험 문구, 추천 수정안, 근거
            chunk를 확인할 수 있습니다.
          </p>
          <div className="mt-4 space-y-3">
            {reports.map((report) => (
              <button
                key={report.id}
                type="button"
                onClick={() =>
                  navigate(`/manager/job-postings/${id}/report?reportId=${report.id}`)
                }
                className="w-full rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-[#315fbc]/40 hover:bg-[#f5f8ff]"
              >
                <div className="flex items-center justify-between gap-3">
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(report.riskLevel)}`}
                  >
                    {report.riskLevel ?? "UNKNOWN"}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatDateTime(report.createdAt)}
                  </span>
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-950">
                  이슈 {report.issueCount}건 · 위반 {report.violationCount}건
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {report.modelName ?? "rule-rag-baseline"}
                </div>
              </button>
            ))}
            {!isLoading && reports.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
                아직 분석 리포트가 없습니다.
              </div>
            ) : null}
          </div>
        </aside>
      </section>
    </div>
  );
}
