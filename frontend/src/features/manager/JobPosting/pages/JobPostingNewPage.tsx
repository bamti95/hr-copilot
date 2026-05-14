import { ArrowLeft, ShieldCheck, Upload } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { JobProgressCard as SharedJobProgressCard } from "../components/JobProgressCard";
import { Field } from "../components/JobPostingFields";
import {
  cancelAnalysisJob,
  fetchActiveAnalysisJob,
  fetchAnalysisJob,
  submitAnalyzeFileJob,
  submitAnalyzeTextJob,
} from "../services/jobPostingService";
import type { JobPostingAiJob, JobPostingCreateRequest } from "../types";
import { inputClassName, textareaClassName } from "../utils/display";
import {
  forgetIgnoredJobId,
  isIgnoredJobId,
  rememberIgnoredJobId,
} from "../utils/ignoredJobs";
import { useJobPolling } from "../hooks/useJobPolling";

const ACTIVE_ANALYSIS_JOB_KEY = "hrCopilot.activeJobPostingAnalysisJob";
const IGNORED_ANALYSIS_JOB_IDS_KEY = "hrCopilot.ignoredJobPostingAnalysisJobIds";
const ANALYSIS_POLLING_TIMEOUT_MS = 5 * 60 * 1000;

function readStoredAnalysisJob(): JobPostingAiJob | null {
  try {
    const raw = window.localStorage.getItem(ACTIVE_ANALYSIS_JOB_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<JobPostingAiJob>;
    return typeof parsed.jobId === "number" &&
      typeof parsed.status === "string" &&
      !isIgnoredJobId(IGNORED_ANALYSIS_JOB_IDS_KEY, parsed.jobId)
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

export function JobPostingNewPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"TEXT" | "FILE">("TEXT");
  const [form, setForm] = useState<JobPostingCreateRequest>({
    companyName: "",
    jobTitle: "",
    targetJob: "",
    careerLevel: "",
    location: "",
    employmentType: "",
    salaryText: "",
    postingText: "",
    analysisType: "FULL",
  });
  const [file, setFile] = useState<File | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleAnalysisCompleted = useCallback(
    (completedJob: JobPostingAiJob) => {
      const resultPayload = completedJob.resultPayload ?? {};
      const postingId = Number(resultPayload.job_posting_id ?? completedJob.targetId);
      const reportId = Number(resultPayload.job_posting_analysis_report_id);
      setIsSaving(false);
      storeAnalysisJob(null);
      if (!postingId || !reportId) {
        setErrorMessage("분석 결과 리포트 정보를 찾지 못했습니다.");
        return;
      }
      navigate(`/manager/job-postings/${postingId}/report?reportId=${reportId}`);
    },
    [navigate],
  );

  const {
    job: activeJob,
    startPolling: startAnalysisPolling,
    clearJob: clearAnalysisJob,
  } = useJobPolling({
    fetcher: fetchAnalysisJob,
    maxPollingMs: ANALYSIS_POLLING_TIMEOUT_MS,
    onCompleted: handleAnalysisCompleted,
    onFailed: (failedJob) => {
      setIsSaving(false);
      storeAnalysisJob(null);
      setErrorMessage(failedJob.errorMessage || "채용공고 분석 작업이 실패했습니다.");
    },
    onError: (error) => {
      setIsSaving(false);
      setErrorMessage(
        error instanceof Error ? error.message : "작업 상태를 불러오지 못했습니다.",
      );
    },
    onTimeout: (timedOutJob) => {
      setIsSaving(false);
      storeAnalysisJob(null);
      rememberIgnoredJobId(IGNORED_ANALYSIS_JOB_IDS_KEY, timedOutJob.jobId);
      setErrorMessage(
        "분석 작업 상태 조회를 중단했습니다. 서버 작업이 계속 실행 중이면 상세 화면에서 다시 확인할 수 있습니다.",
      );
    },
  });

  useEffect(() => {
    let cancelled = false;
    const storedJob = readStoredAnalysisJob();
    if (storedJob) {
      setIsSaving(true);
      startAnalysisPolling(storedJob);
    }
    void fetchActiveAnalysisJob()
      .then((activeJob) => {
        if (cancelled || !activeJob) return;
        if (isIgnoredJobId(IGNORED_ANALYSIS_JOB_IDS_KEY, activeJob.jobId)) {
          storeAnalysisJob(null);
          return;
        }
        storeAnalysisJob(activeJob);
        setIsSaving(true);
        startAnalysisPolling(activeJob);
      })
      .catch(() => {
        // Local storage recovery is enough when the active-job probe is delayed.
      });
    return () => {
      cancelled = true;
    };
  }, [startAnalysisPolling]);

  async function handleAnalyze() {
    if (!form.jobTitle.trim()) {
      setErrorMessage("공고명은 필수입니다.");
      return;
    }
    if (mode === "TEXT" && !form.postingText.trim()) {
      setErrorMessage("분석할 채용공고 본문을 입력해 주세요.");
      return;
    }
    if (mode === "FILE" && !file) {
      setErrorMessage("분석할 PDF 또는 문서 파일을 선택해 주세요.");
      return;
    }

    setIsSaving(true);
    setErrorMessage("");
    clearAnalysisJob();
    try {
      const submittedJob =
        mode === "FILE" && file
          ? await submitAnalyzeFileJob({
              file,
              jobTitle: form.jobTitle,
              companyName: form.companyName || undefined,
            })
          : await submitAnalyzeTextJob(form);
      forgetIgnoredJobId(IGNORED_ANALYSIS_JOB_IDS_KEY, submittedJob.jobId);
      storeAnalysisJob(submittedJob);
      startAnalysisPolling(submittedJob);
    } catch (error) {
      setIsSaving(false);
      setErrorMessage(
        error instanceof Error ? error.message : "채용공고 분석을 실행하지 못했습니다.",
      );
    }
  }

  async function handleCancelAnalysisJob(job: JobPostingAiJob) {
    rememberIgnoredJobId(IGNORED_ANALYSIS_JOB_IDS_KEY, job.jobId);
    setIsSaving(false);
    setErrorMessage("");
    try {
      const cancelledJob = await cancelAnalysisJob(job.jobId);
      storeAnalysisJob(null);
      clearAnalysisJob();
      setErrorMessage(cancelledJob.errorMessage || "채용공고 분석 작업을 취소했습니다.");
    } catch (error) {
      storeAnalysisJob(null);
      clearAnalysisJob();
      setErrorMessage(
        error instanceof Error ? error.message : "채용공고 분석 작업 취소에 실패했습니다.",
      );
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Rule-RAG Baseline"
        title="채용공고 등록 및 Agentic RAG 평가"
        description="공고 본문 또는 파일을 입력하면 작업 ID를 먼저 발급하고, 백그라운드에서 Hybrid RAG 근거 검색과 리스크 분석을 수행합니다."
        actions={
          <Link
            to="/manager/job-postings"
            className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
          >
            <ArrowLeft className="h-4 w-4" />
            목록
          </Link>
        }
      />

      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.25fr)]">
        <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="mb-4 inline-flex rounded-2xl border border-[var(--line)] bg-white p-1">
            {(["TEXT", "FILE"] as const).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setMode(item)}
                className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                  mode === item
                    ? "bg-[#315fbc] text-white"
                    : "text-slate-500 hover:bg-slate-50"
                }`}
              >
                {item === "TEXT" ? "본문 입력" : "파일 업로드"}
              </button>
            ))}
          </div>

          <div className="grid gap-4">
            <Field label="공고명">
              <input
                value={form.jobTitle}
                onChange={(event) =>
                  setForm((current) => ({ ...current, jobTitle: event.target.value }))
                }
                className={inputClassName}
                placeholder="예: AI 데이터 플랫폼 엔지니어"
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="회사명">
                <input
                  value={form.companyName ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      companyName: event.target.value,
                    }))
                  }
                  className={inputClassName}
                  placeholder="예: 에이치알"
                />
              </Field>
              <Field label="직무군">
                <input
                  value={form.targetJob ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, targetJob: event.target.value }))
                  }
                  className={inputClassName}
                  placeholder="예: AI_DEV_DATA"
                />
              </Field>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="경력">
                <input
                  value={form.careerLevel ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      careerLevel: event.target.value,
                    }))
                  }
                  className={inputClassName}
                  placeholder="예: 경력 3년 이상"
                />
              </Field>
              <Field label="근무지">
                <input
                  value={form.location ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, location: event.target.value }))
                  }
                  className={inputClassName}
                  placeholder="예: 서울"
                />
              </Field>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="고용형태">
                <input
                  value={form.employmentType ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      employmentType: event.target.value,
                    }))
                  }
                  className={inputClassName}
                  placeholder="예: 정규직"
                />
              </Field>
              <Field label="연봉/처우">
                <input
                  value={form.salaryText ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, salaryText: event.target.value }))
                  }
                  className={inputClassName}
                  placeholder="예: 4,000만 ~ 5,500만"
                />
              </Field>
            </div>
          </div>

          {errorMessage ? (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {errorMessage}
            </div>
          ) : null}

          {activeJob ? (
            <SharedJobProgressCard
              job={activeJob}
              onCancelJob={() => void handleCancelAnalysisJob(activeJob)}
            />
          ) : null}

          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">
            분석은 AiJob 백그라운드 작업으로 실행됩니다. 작업 중에도 다른 화면으로
            이동할 수 있으며, 완료 후 리포트 페이지에서 근거와 workflow trace를 확인할
            수 있습니다.
          </div>

          <button
            type="button"
            disabled={isSaving}
            onClick={() => void handleAnalyze()}
            className="mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mode === "FILE" ? (
              <Upload className="h-4 w-4" />
            ) : (
              <ShieldCheck className="h-4 w-4" />
            )}
            {isSaving ? "백그라운드 분석 진행 중..." : "비동기 리스크 분석 실행"}
          </button>
        </div>

        <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          {mode === "TEXT" ? (
            <Field label="채용공고 본문">
              <textarea
                value={form.postingText}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    postingText: event.target.value,
                  }))
                }
                className={textareaClassName}
                placeholder="실제 채용공고 본문을 붙여 넣어 주세요. 주요 업무, 자격요건, 우대사항, 근무조건, 전형절차가 포함될수록 평가 품질이 좋아집니다."
              />
            </Field>
          ) : (
            <div>
              <label className="flex min-h-[360px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/70 px-6 py-10 text-center transition hover:border-[#315fbc] hover:bg-[#f5f8ff]">
                <Upload className="h-9 w-9 text-[#315fbc]" />
                <strong className="mt-3 text-sm text-slate-950">
                  PDF 또는 문서 파일 선택
                </strong>
                <span className="mt-2 max-w-sm text-xs leading-5 text-slate-500">
                  백엔드의 텍스트 추출 결과에 따라 분석 품질이 달라질 수 있습니다. 스캔
                  PDF는 OCR 결과를 확인해 주세요.
                </span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.hwp,.xlsx,.xls,.csv"
                  className="sr-only"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </label>
              {file ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                  선택 파일: <strong>{file.name}</strong>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
