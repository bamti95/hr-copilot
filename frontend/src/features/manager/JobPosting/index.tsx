import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  FileSearch,
  FileText,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
} from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageIntro } from "../../../common/components/PageIntro";
import {
  analyzeExistingJobPosting,
  analyzeJobPostingFile,
  analyzeJobPostingText,
  fetchKnowledgeChunks,
  fetchJobPosting,
  fetchJobPostingReport,
  fetchJobPostingReports,
  fetchJobPostings,
  fetchKnowledgeSources,
  indexKnowledgeSource,
  searchKnowledgeSources,
  seedSourceData,
  uploadKnowledgeSource,
} from "./services/jobPostingService";
import type {
  EvidenceSource,
  JobPostingAnalysisReport,
  JobPostingCreateRequest,
  JobPostingIssue,
  JobPostingResponse,
  KnowledgeChunk,
  KnowledgeSearchResponse,
  KnowledgeSource,
} from "./types";

const inputClassName =
  "h-11 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm text-[var(--text)] outline-none transition focus:border-[var(--primary)]";
const textareaClassName =
  "min-h-[360px] w-full resize-y rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-3 text-sm leading-6 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function riskStyle(level?: string | null) {
  const normalized = (level ?? "UNKNOWN").toUpperCase();
  if (normalized === "CRITICAL") return "border-rose-200 bg-rose-50 text-rose-700";
  if (normalized === "HIGH") return "border-orange-200 bg-orange-50 text-orange-700";
  if (normalized === "MEDIUM") return "border-amber-200 bg-amber-50 text-amber-700";
  if (normalized === "LOW") return "border-sky-200 bg-sky-50 text-sky-700";
  if (normalized === "CLEAN") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function toIssueList(value: JobPostingAnalysisReport["issueSummary"]): JobPostingIssue[] {
  return Array.isArray(value) ? value : [];
}

function toEvidenceList(
  value: JobPostingAnalysisReport["matchedEvidence"],
): EvidenceSource[] {
  return Array.isArray(value) ? value : [];
}

export default function JobPostingPage() {
  return <JobPostingListPage />;
}

export function JobPostingListPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<JobPostingResponse[]>([]);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const load = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const data = await fetchJobPostings({ page, size: 10, keyword });
      setItems(data.items);
      setTotalPages(data.totalPages);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "채용공고 목록을 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [keyword, page]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Job Posting Compliance"
        title="채용공고 리스크 분석"
        description="현재는 Rule-RAG Baseline 기반의 기본 리스크 점검입니다. 정규식 후보 탐지와 keyword 기반 법률 근거 매칭으로 공고 문구의 초기 위험도를 확인합니다."
        actions={
          <>
            <Link
              to="/manager/job-postings/knowledge-sources"
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
            >
              <FileText className="h-4 w-4" />
              기반지식
            </Link>
            <Link
              to="/manager/job-postings/new"
              className="inline-flex h-11 items-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)]"
            >
              <FileSearch className="h-4 w-4" />
              새 분석
            </Link>
          </>
        }
      />

      <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <form
            className="relative w-full md:max-w-md"
            onSubmit={(event) => {
              event.preventDefault();
              setPage(0);
              setKeyword(keywordInput.trim());
            }}
          >
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={keywordInput}
              onChange={(event) => setKeywordInput(event.target.value)}
              className={`${inputClassName} pl-10`}
              placeholder="회사명, 공고명, 직무로 검색"
            />
          </form>
          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)] transition hover:bg-white"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            새로고침
          </button>
        </div>

        {errorMessage ? (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </div>
        ) : null}

        <div className="mt-5 overflow-hidden rounded-2xl border border-[var(--line)] bg-white/70">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
              <tr>
                <th className="px-4 py-3">공고</th>
                <th className="px-4 py-3">회사/직무</th>
                <th className="px-4 py-3">고용형태</th>
                <th className="px-4 py-3">등록일</th>
                <th className="px-4 py-3 text-right">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.id} className="transition hover:bg-[#f5f8ff]">
                  <td className="px-4 py-4">
                    <div className="font-semibold text-slate-950">{item.jobTitle}</div>
                    <div className="mt-1 line-clamp-1 text-xs text-slate-500">
                      {item.salaryText || "연봉 정보 미기재"}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-slate-600">
                    <div>{item.companyName || "회사명 미기재"}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {item.targetJob || item.location || "-"}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-slate-600">
                    {item.employmentType || "-"}
                  </td>
                  <td className="px-4 py-4 text-slate-500">
                    {formatDateTime(item.createdAt)}
                  </td>
                  <td className="px-4 py-4 text-right">
                    <button
                      type="button"
                      onClick={() => navigate(`/manager/job-postings/${item.id}`)}
                      className="rounded-xl border border-[#315fbc]/20 bg-[#edf4ff] px-3 py-2 text-xs font-semibold text-[#315fbc] transition hover:bg-[#dfeaff]"
                    >
                      상세 보기
                    </button>
                  </td>
                </tr>
              ))}
              {!isLoading && items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-sm text-slate-500">
                    등록된 채용공고가 없습니다. 새 분석으로 첫 공고를 점검해 보세요.
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
    try {
      const result =
        mode === "FILE" && file
          ? await analyzeJobPostingFile({
              file,
              jobTitle: form.jobTitle,
              companyName: form.companyName || undefined,
            })
          : await analyzeJobPostingText(form);
      navigate(
        `/manager/job-postings/${result.jobPosting.id}/report?reportId=${result.report.id}`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "채용공고 분석을 실행하지 못했습니다.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Rule-RAG Baseline"
        title="채용공고 등록 및 기본 리스크 점검"
        description="공고 본문 또는 파일을 입력하면 현재 백엔드의 regex 후보 탐지와 keyword 근거 검색으로 리스크 리포트를 생성합니다."
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
                  placeholder="예: 에이치알랩"
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
                  placeholder="예: 4,000만 원~5,500만 원"
                />
              </Field>
            </div>
          </div>

          {errorMessage ? (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">
            현재 분석은 완전한 Agentic RAG가 아니라 기본 점검입니다. 결과는 공고 게시 전
            사전 검토용으로 사용하고, 최종 법률 판단은 내부 검토 절차를 거쳐야 합니다.
          </div>

          <button
            type="button"
            disabled={isSaving}
            onClick={() => void handleAnalyze()}
            className="mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mode === "FILE" ? <Upload className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
            {isSaving ? "분석 중..." : "기본 리스크 분석 실행"}
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
                placeholder="실제 채용공고 본문을 붙여넣어 주세요. 주요 업무, 자격요건, 우대사항, 근무조건, 전형절차가 포함될수록 점검 품질이 좋아집니다."
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
                  백엔드의 텍스트 추출 품질에 따라 분석 품질이 달라집니다. 스캔 PDF는 OCR
                  결과를 확인해 주세요.
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

export function JobPostingDetailPage() {
  const navigate = useNavigate();
  const { postingId } = useParams();
  const id = Number(postingId);
  const [posting, setPosting] = useState<JobPostingResponse | null>(null);
  const [reports, setReports] = useState<JobPostingAnalysisReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

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
        error instanceof Error
          ? error.message
          : "채용공고 상세를 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleAnalyzeExisting() {
    setIsAnalyzing(true);
    setErrorMessage("");
    try {
      const report = await analyzeExistingJobPosting(id);
      navigate(`/manager/job-postings/${id}/report?reportId=${report.id}`);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "재분석을 실행하지 못했습니다.",
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Job Posting Detail"
        title={posting?.jobTitle ?? "채용공고 상세"}
        description="공고 원문과 Rule-RAG Baseline 분석 이력을 확인하고, 필요하면 동일 공고를 다시 점검할 수 있습니다."
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
            최신 분석 결과부터 표시됩니다. 상세 화면에서 위험 문구, 추천 수정안,
            근거 chunk를 확인할 수 있습니다.
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
                  <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(report.riskLevel)}`}>
                    {report.riskLevel ?? "UNKNOWN"}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatDateTime(report.createdAt)}
                  </span>
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-950">
                  이슈 {report.issueCount}개 · 위반 {report.violationCount}개
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
          rid ? fetchJobPostingReport(rid) : fetchJobPostingReports(id).then((rows) => rows[0]),
        ]);
        setPosting(postingData);
        setReport(reportData ?? null);
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "분석 리포트를 불러오지 못했습니다.",
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

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Analysis Report"
        title={posting?.jobTitle ?? "분석 리포트"}
        description="기본 리스크 점검 결과입니다. 위험 문구와 추천 수정안, keyword 기반 매칭 근거를 함께 확인합니다."
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

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard label="위험등급" value={report?.riskLevel ?? "-"} tone={riskStyle(report?.riskLevel)} />
        <MetricCard label="탐지 이슈" value={`${report?.issueCount ?? 0}개`} />
        <MetricCard label="법적 위반 후보" value={`${report?.violationCount ?? 0}개`} />
        <MetricCard label="신뢰도" value={`${report?.confidenceScore ?? "-"}${report?.confidenceScore ? "%" : ""}`} />
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
              {isLoading ? "불러오는 중..." : report?.summaryText || "요약 정보가 없습니다."}
            </p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-xs leading-5 text-slate-500">
              분석 파이프라인: {report?.pipelineVersion ?? "job-posting-compliance-rag-v1"} · 모델:
              {" "}
              {report?.modelName ?? "rule-rag-baseline"}
            </div>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <h2 className="m-0 text-lg font-bold text-slate-950">위험 문구 및 수정안</h2>
            <div className="mt-4 space-y-3">
              {issues.map((issue, index) => (
                <div key={`${issue.issueType}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskStyle(issue.severity)}`}>
                      {issue.severity || "RISK"}
                    </span>
                    <span className="text-sm font-bold text-slate-950">
                      {issue.issueType || "UNKNOWN"}
                    </span>
                  </div>
                  <blockquote className="mt-3 rounded-xl border-l-4 border-[#315fbc] bg-[#f5f8ff] px-4 py-3 text-sm text-slate-700">
                    {issue.flaggedText || "문구 정보 없음"}
                  </blockquote>
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {issue.whyRisky || "위험 사유가 제공되지 않았습니다."}
                  </p>
                  <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm leading-6 text-emerald-900">
                    {issue.recommendedRevision || "수정 예시가 제공되지 않았습니다."}
                  </div>
                </div>
              ))}
              {!isLoading && issues.length === 0 ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-10 text-center text-sm text-emerald-800">
                  탐지된 주요 리스크가 없습니다.
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
                <div key={`${item.chunkId ?? index}`} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-bold text-slate-950">
                        {item.title || item.lawName || "근거 문서"}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {item.articleNo || item.sectionTitle || item.chunkType || "-"}
                      </div>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                      {item.score ? Math.round(item.score * 100) : "-"}점
                    </span>
                  </div>
                  <p className="mt-3 line-clamp-5 text-xs leading-5 text-slate-600">
                    {item.content || "근거 내용 없음"}
                  </p>
                </div>
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

export function JobPostingKnowledgePage() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [versionLabel, setVersionLabel] = useState("");
  const [query, setQuery] = useState("혼인 여부와 가족관계 기재 요구");
  const [searchMode, setSearchMode] = useState<"HYBRID" | "KEYWORD" | "VECTOR">(
    "HYBRID",
  );
  const [searchResult, setSearchResult] =
    useState<KnowledgeSearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState<number | null>(null);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const loadSources = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const data = await fetchKnowledgeSources({
        page: 0,
        size: 50,
        keyword,
      });
      setSources(data.items);
      if (!selectedSourceId && data.items[0]) {
        setSelectedSourceId(data.items[0].id);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "기반지식 문서 목록을 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [keyword, selectedSourceId]);

  useEffect(() => {
    void loadSources();
  }, [loadSources]);

  useEffect(() => {
    if (!selectedSourceId) {
      setChunks([]);
      return;
    }
    async function loadChunks() {
      try {
        setChunks(await fetchKnowledgeChunks(selectedSourceId));
      } catch {
        setChunks([]);
      }
    }
    void loadChunks();
  }, [selectedSourceId]);

  async function handleUpload() {
    if (!file) {
      setErrorMessage("업로드할 법률 PDF 또는 문서 파일을 선택해 주세요.");
      return;
    }
    setIsUploading(true);
    setErrorMessage("");
    setMessage("");
    try {
      const source = await uploadKnowledgeSource({
        file,
        title: title || undefined,
        versionLabel: versionLabel || undefined,
      });
      setMessage("기반지식 문서가 업로드되었습니다. 인덱싱을 실행해 주세요.");
      setSelectedSourceId(source.id);
      setFile(null);
      setTitle("");
      setVersionLabel("");
      await loadSources();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "문서 업로드에 실패했습니다.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleIndex(sourceId: number) {
    setIsIndexing(sourceId);
    setErrorMessage("");
    setMessage("");
    try {
      const result = await indexKnowledgeSource(sourceId);
      setMessage(`인덱싱 완료: ${result.chunkCount}개 chunk가 생성되었습니다.`);
      setSelectedSourceId(sourceId);
      await loadSources();
      setChunks(await fetchKnowledgeChunks(sourceId));
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "문서 인덱싱에 실패했습니다.",
      );
    } finally {
      setIsIndexing(null);
    }
  }

  async function handleSeed() {
    setIsSeeding(true);
    setErrorMessage("");
    setMessage("");
    try {
      const result = await seedSourceData();
      setMessage(
        `source_data 적재 완료: ${result.totalSources}개 문서, ${result.totalChunks}개 chunk`,
      );
      await loadSources();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "source_data 적재에 실패했습니다.",
      );
    } finally {
      setIsSeeding(false);
    }
  }

  async function handleSearch() {
    if (!query.trim()) {
      setErrorMessage("검색할 위반 사례 또는 법률 쟁점을 입력해 주세요.");
      return;
    }
    setIsSearching(true);
    setErrorMessage("");
    try {
      setSearchResult(
        await searchKnowledgeSources({
          query,
          searchMode,
          limit: 10,
        }),
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "기반지식 검색에 실패했습니다.",
      );
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Knowledge Base RAG"
        title="채용공고 법률 기반지식"
        description="채용절차법 지도점검 결과, 법령, 가이드 PDF를 업로드하거나 source_data를 일괄 적재해 chunk와 embedding을 생성하고, 분석에 사용할 근거 검색 품질을 확인합니다."
        actions={
          <Link
            to="/manager/job-postings"
            className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
          >
            <ArrowLeft className="h-4 w-4" />
            공고 분석
          </Link>
        }
      />

      {message ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="m-0 text-lg font-bold text-slate-950">기반지식 업로드</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                예: 23년 하반기 채용절차법 지도점검 결과 발표 PDF
              </p>
            </div>
            <button
              type="button"
              disabled={isSeeding}
              onClick={() => void handleSeed()}
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[#315fbc]/20 bg-[#edf4ff] px-4 text-sm font-semibold text-[#315fbc] disabled:opacity-60"
            >
              <FileSearch className="h-4 w-4" />
              {isSeeding ? "적재 중..." : "source_data 적재"}
            </button>
          </div>

          <div className="mt-5 grid gap-4">
            <Field label="문서 제목">
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className={inputClassName}
                placeholder="미입력 시 파일명 사용"
              />
            </Field>
            <Field label="버전/출처 메모">
              <input
                value={versionLabel}
                onChange={(event) => setVersionLabel(event.target.value)}
                className={inputClassName}
                placeholder="예: 2023 하반기 지도점검"
              />
            </Field>
            <label className="flex min-h-[150px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/70 px-5 py-8 text-center transition hover:border-[#315fbc] hover:bg-[#f5f8ff]">
              <Upload className="h-8 w-8 text-[#315fbc]" />
              <strong className="mt-3 text-sm text-slate-950">
                법률 PDF 또는 가이드 문서 선택
              </strong>
              <span className="mt-2 text-xs text-slate-500">
                업로드 후 인덱싱을 실행하면 chunk와 embedding이 생성됩니다.
              </span>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt,.hwp,.xlsx,.xls,.csv"
                className="sr-only"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
            {file ? (
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                선택 파일: <strong>{file.name}</strong>
              </div>
            ) : null}
            <button
              type="button"
              disabled={isUploading}
              onClick={() => void handleUpload()}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)] disabled:opacity-60"
            >
              <Upload className="h-4 w-4" />
              {isUploading ? "업로드 중..." : "기반지식 업로드"}
            </button>
          </div>
        </article>

        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <h2 className="m-0 text-lg font-bold text-slate-950">유사도 검색 테스트</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            분석 파이프라인에 들어가기 전, 법률 chunk가 실제로 검색되는지 확인합니다.
          </p>
          <div className="mt-5 grid gap-3">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-h-[96px] w-full resize-y rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-3 text-sm leading-6 outline-none focus:border-[var(--primary)]"
              placeholder="예: 혼인 여부와 가족관계를 입사지원서에 기재하도록 요구"
            />
            <div className="flex flex-col gap-3 sm:flex-row">
              <select
                value={searchMode}
                onChange={(event) =>
                  setSearchMode(event.target.value as "HYBRID" | "KEYWORD" | "VECTOR")
                }
                className={inputClassName}
              >
                <option value="HYBRID">HYBRID</option>
                <option value="KEYWORD">KEYWORD</option>
                <option value="VECTOR">VECTOR</option>
              </select>
              <button
                type="button"
                disabled={isSearching}
                onClick={() => void handleSearch()}
                className="inline-flex h-11 min-w-[150px] items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:opacity-60"
              >
                <Search className="h-4 w-4" />
                {isSearching ? "검색 중..." : "검색"}
              </button>
            </div>
            {searchResult ? (
              <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-xs text-slate-500">
                {searchResult.searchMode} · {searchResult.embeddingModel} ·{" "}
                {searchResult.resultCount}개 결과
              </div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="m-0 text-lg font-bold text-slate-950">기반지식 문서</h2>
            <form
              className="relative md:w-72"
              onSubmit={(event) => {
                event.preventDefault();
                setKeyword(keywordInput.trim());
              }}
            >
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={keywordInput}
                onChange={(event) => setKeywordInput(event.target.value)}
                className={`${inputClassName} pl-10`}
                placeholder="문서 검색"
              />
            </form>
          </div>

          <div className="mt-4 space-y-3">
            {sources.map((source) => (
              <div
                key={source.id}
                className={`rounded-2xl border bg-white p-4 transition ${
                  selectedSourceId === source.id
                    ? "border-[#315fbc]/50"
                    : "border-slate-200"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setSelectedSourceId(source.id)}
                  className="block w-full text-left"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-semibold text-slate-950">{source.title}</div>
                      <div className="mt-1 text-xs text-slate-500">
                        {source.sourceType} · {source.fileExt ?? "-"}
                      </div>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                      {source.chunkCount} chunks
                    </span>
                  </div>
                </button>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <StatusPill label={`extract ${source.extractStatus}`} />
                  <StatusPill label={`index ${source.indexStatus}`} />
                  <button
                    type="button"
                    disabled={isIndexing === source.id}
                    onClick={() => void handleIndex(source.id)}
                    className="rounded-full border border-[#315fbc]/20 bg-[#edf4ff] px-3 py-1 font-semibold text-[#315fbc] disabled:opacity-60"
                  >
                    {isIndexing === source.id ? "인덱싱 중" : "인덱싱"}
                  </button>
                </div>
              </div>
            ))}
            {!isLoading && sources.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
                기반지식 문서가 없습니다. PDF를 업로드하거나 source_data를 적재하세요.
              </div>
            ) : null}
          </div>
        </article>

        <div className="space-y-5">
          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <h2 className="m-0 text-lg font-bold text-slate-950">검색 결과</h2>
            <div className="mt-4 space-y-3">
              {searchResult?.results.map((result) => (
                <KnowledgeResultCard key={result.chunk.id} result={result} />
              ))}
              {searchResult && searchResult.results.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
                  검색 결과가 없습니다. 먼저 문서를 인덱싱해 주세요.
                </div>
              ) : null}
            </div>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
            <h2 className="m-0 text-lg font-bold text-slate-950">선택 문서 Chunk 미리보기</h2>
            <div className="mt-4 space-y-3">
              {chunks.slice(0, 6).map((chunk) => (
                <div key={chunk.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-bold text-slate-950">
                        {chunk.sectionTitle || chunk.articleNo || `Chunk #${chunk.chunkIndex}`}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {chunk.chunkType} · {chunk.embeddingModel ?? "embedding 없음"}
                      </div>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
                      {chunk.tokenCount ?? "-"} tok
                    </span>
                  </div>
                  <p className="mt-3 line-clamp-4 text-xs leading-5 text-slate-600">
                    {chunk.summary || chunk.content}
                  </p>
                </div>
              ))}
              {selectedSourceId && chunks.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
                  chunk가 없습니다. 인덱싱을 실행해 주세요.
                </div>
              ) : null}
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}

function StatusPill({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 font-semibold text-slate-600">
      {label}
    </span>
  );
}

function KnowledgeResultCard({
  result,
}: {
  result: KnowledgeSearchResponse["results"][number];
}) {
  const chunk = result.chunk;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold text-slate-950">
            {chunk.lawName || chunk.sectionTitle || "기반지식 chunk"}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {chunk.articleNo || chunk.issueCode || chunk.chunkType}
          </div>
        </div>
        <span className="rounded-full bg-[#edf4ff] px-3 py-1 text-xs font-bold text-[#315fbc]">
          {Math.round(result.hybridScore * 100)}점
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
        <span>keyword {Math.round(result.keywordScore * 100)}</span>
        <span>vector {Math.round(result.vectorScore * 100)}</span>
        <span>{result.matchedTerms.join(", ") || "matched term 없음"}</span>
      </div>
      <p className="mt-3 line-clamp-5 text-xs leading-5 text-slate-600">
        {chunk.content}
      </p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-semibold text-slate-700">
      {label}
      <div className="mt-2">{children}</div>
    </label>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <article className="rounded-[24px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <div className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </div>
      <div className={`mt-3 inline-flex rounded-full border px-3 py-1 text-lg font-bold ${tone ?? "border-transparent text-slate-950"}`}>
        {value}
      </div>
    </article>
  );
}
