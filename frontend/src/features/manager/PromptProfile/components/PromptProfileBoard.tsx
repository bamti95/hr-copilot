import { Pagination } from "../../../../common/components/Pagination";
import type { PromptProfileListResponse, PromptProfileResponse } from "../types";
import { formatDateTime } from "../../common/formatDateTime";

interface PromptProfileBoardProps {
  data: PromptProfileListResponse;
  isLoading: boolean;
  errorMessage: string;
  search: string;
  pageSize: number;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onEdit: (row: PromptProfileResponse) => void;
  onDelete: (row: PromptProfileResponse) => void;
}

const inputClassName =
  "mt-2 h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function truncate(text: string, max: number) {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) {
    return t;
  }
  return `${t.slice(0, max)}…`;
}

export function PromptProfileBoard({
  data,
  isLoading,
  errorMessage,
  search,
  pageSize,
  onSearchChange,
  onSearchSubmit,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onEdit,
  onDelete,
}: PromptProfileBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-[var(--text)]">프롬프트 프로필 관리</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          시스템 프롬프트와 출력 JSON 스키마를 프로필 단위로 등록·수정합니다. API:{" "}
          <code className="rounded bg-[var(--panel-strong)] px-1.5 py-0.5 text-xs">
            /api/v1/prompt-profiles
          </code>
        </p>
      </div>

      {errorMessage ? (
        <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {errorMessage}
        </div>
      ) : null}

      <div className="mb-4 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 xl:grid-cols-[minmax(0,1fr)_140px_100px_auto] xl:items-end">
        <label className="text-sm font-medium text-[var(--text)]">
          검색
          <input
            className={inputClassName}
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearchSubmit();
              }
            }}
            placeholder="프로필 키 (부분 일치)"
          />
        </label>

        <label className="text-sm font-medium text-[var(--text)]">
          페이지 크기
          <select
            className={inputClassName}
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {[10, 20, 50].map((size) => (
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
              {["ID", "프로필 키", "시스템 프롬프트", "스키마", "생성자", "수정일", "액션"].map((label) => (
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
            {data.items.map((row) => (
              <tr key={row.id} className="transition hover:bg-slate-50/70">
                <td className="border-b border-[var(--line)] px-3 py-3 align-top whitespace-nowrap">
                  {row.id}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 align-top font-semibold whitespace-nowrap text-[var(--text)]">
                  {row.profileKey}
                </td>
                <td
                  className="border-b border-[var(--line)] px-3 py-3 align-top text-sm text-[var(--text)] max-w-[min(420px,40vw)]"
                  title={row.systemPrompt}
                >
                  {truncate(row.systemPrompt, 120)}
                </td>
                <td
                  className="border-b border-[var(--line)] px-3 py-3 align-top font-mono text-xs text-[var(--muted)] max-w-[200px]"
                  title={row.outputSchema ?? ""}
                >
                  {row.outputSchema ? truncate(row.outputSchema, 40) : "—"}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 align-top whitespace-nowrap text-sm text-[var(--text)]">
                  {row.createdName ?? "-"}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 align-top whitespace-nowrap text-sm">
                  {formatDateTime(row.updatedAt)}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 align-top whitespace-nowrap">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className={`${buttonClassName} border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                      onClick={() => onEdit(row)}
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
            ))}
            {data.items.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-3 py-10 text-center text-sm text-[var(--muted)]"
                >
                  {isLoading ? "불러오는 중…" : "등록된 프롬프트 프로필이 없습니다."}
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
