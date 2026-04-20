import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type {
  CandidateApplyStatus,
  CandidateListResponse,
  CandidateResponse,
} from "../types";

interface CandidateBoardProps {
  data: CandidateListResponse;
  isLoading: boolean;
  search: string;
  statusFilter: CandidateApplyStatus | "ALL";
  pageSize: number;
  selectedCandidateId: number | null;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onStatusFilterChange: (value: CandidateApplyStatus | "ALL") => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onView: (candidateId: number) => void;
  onDelete: (row: CandidateResponse) => void;
}

const inputClassName =
  "h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}

function formatDateTime(value: string) {
  return value.replace("T", " ").slice(0, 16);
}

export function CandidateBoard({
  data,
  isLoading,
  search,
  statusFilter,
  pageSize,
  selectedCandidateId,
  onSearchChange,
  onSearchSubmit,
  onStatusFilterChange,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onView,
  onDelete,
}: CandidateBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-5">
        <h2 className="m-0 text-2xl font-bold text-[var(--text)]">지원자 관리</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          후보자 목록을 조회하고, 상세 모달에서 기본 정보 수정과 지원 상태 변경,
          문서 등록 및 다운로드를 함께 처리합니다.
        </p>
      </div>

      <div className="mb-4 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 xl:grid-cols-[minmax(0,1fr)_180px_150px_100px_auto] xl:items-end">
        <label className="text-sm font-medium text-[var(--text)]">
          검색어
          <input
            className={`${inputClassName} mt-2`}
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearchSubmit();
              }
            }}
            placeholder="이름, 이메일로 검색"
          />
        </label>

        <label className="text-sm font-medium text-[var(--text)]">
          지원 상태
          <select
            className={`${inputClassName} mt-2`}
            value={statusFilter}
            onChange={(event) =>
              onStatusFilterChange(event.target.value as CandidateApplyStatus | "ALL")
            }
          >
            <option value="ALL">전체</option>
            <option value="APPLIED">APPLIED</option>
            <option value="SCREENING">SCREENING</option>
            <option value="INTERVIEW">INTERVIEW</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </label>

        <label className="text-sm font-medium text-[var(--text)]">
          페이지 크기
          <select
            className={`${inputClassName} mt-2`}
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className={`${buttonClassName} border-slate-900 bg-slate-900 px-4 text-white hover:bg-slate-800`}
          onClick={onSearchSubmit}
        >
          검색
        </button>

        <button
          type="button"
          className={`${buttonClassName} border-transparent bg-[var(--primary)] px-4 text-white hover:opacity-90`}
          onClick={onCreate}
        >
          신규 등록
        </button>
      </div>

      <div className="mb-4 text-right text-sm text-[var(--muted)]">
        총 {data.paging.totalCount}건 / {Math.max(data.paging.totalPages, 1)} 페이지
      </div>

      <div className="overflow-x-auto rounded-[24px] border border-white/70">
        <table className="w-full border-collapse">
          <thead className="bg-white/60">
            <tr>
              {[
                "ID",
                "이름",
                "이메일",
                "전화번호",
                "생년월일",
                "지원 상태",
                "등록일",
                "액션",
              ].map((label) => (
                <th
                  key={label}
                  className="border-b border-[var(--line)] px-3 py-3 text-left text-[0.84rem] font-bold whitespace-nowrap text-[var(--muted)]"
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => {
              const isSelected = selectedCandidateId === row.id;

              return (
                <tr
                  key={row.id}
                  className={isSelected ? "bg-emerald-50/60" : "transition hover:bg-slate-50/70"}
                >
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.id}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap font-semibold text-[var(--text)]">
                    {row.name}
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.email}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.phone}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{formatDate(row.birthDate)}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    <StatusPill status={row.applyStatus} />
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    {formatDateTime(row.createdAt)}
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className={`${buttonClassName} border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                        onClick={() => onView(row.id)}
                        disabled={isLoading}
                      >
                        수정
                      </button>
                      <button
                        type="button"
                        className={`${buttonClassName} border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100`}
                        onClick={() => onDelete(row)}
                        disabled={isLoading}
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {data.items.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="px-3 py-10 text-center text-sm text-[var(--muted)]"
                >
                  조회된 지원자가 없습니다.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
