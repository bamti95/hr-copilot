import { FileSearch, FileText, RefreshCw, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { fetchJobPostings } from "../services/jobPostingService";
import type { JobPostingResponse } from "../types";
import { formatDateTime, inputClassName } from "../utils/display";

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
        description="Rule-RAG 기반으로 채용공고 문구의 컴플라이언스 리스크를 점검하고 법률 근거를 함께 확인합니다."
        actions={
          <>
            <Link
              to="/manager/job-posting-experiments"
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
            >
              <FileSearch className="h-4 w-4" />
              실험실
            </Link>
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
                    등록된 채용공고가 없습니다. 새 분석으로 첫 공고를 추가해 보세요.
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

