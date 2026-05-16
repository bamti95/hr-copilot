import { Pagination } from "../../../../common/components/Pagination";
import { formatDateTime } from "../../common/formatDateTime"
import { StatusPill } from "../../../../common/components/StatusPill";
import type { ManagerListResponse, ManagerResponse } from "../types";
import { getRoleLabel } from "./managerLabels";

interface ManagerBoardProps {
  data: ManagerListResponse;
  isLoading: boolean;
  search: string;
  pageSize: number;
  canManage: boolean;
  editingManagerId: number | null;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onEdit: (managerId: number) => void;
  onToggleStatus: (row: ManagerResponse) => void;
  onDelete: (row: ManagerResponse) => void;
}

const inputClassName =
  "h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function getNextStatus(status: string) {
  return status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
}

function getToggleStatusLabel(status: string) {
  return getNextStatus(status) === "ACTIVE" ? "활성화" : "비활성화";
}

export function ManagerBoard({
  data,
  isLoading,
  search,
  pageSize,
  canManage,
  editingManagerId,
  onSearchChange,
  onSearchSubmit,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onEdit,
  onToggleStatus,
  onDelete,
}: ManagerBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-5">
        <h2 className="m-0 text-2xl font-bold text-[var(--text)]">관리자 관리</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          검색 조건과 페이지 크기를 설정한 뒤 관리자 목록을 조회하고, 권한이 있으면 생성/수정/상태변경/논리삭제를 처리할 수 있습니다.
        </p>
      </div>

      <div className="mb-4 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 xl:grid-cols-[minmax(0,1fr)_180px_100px_auto_auto] xl:items-end">
        <label className="text-sm font-medium text-[var(--text)]">
          키워드(이름/로그인 ID/이메일)
          <input
            className={`${inputClassName} mt-2`}
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearchSubmit();
              }
            }}
            placeholder="검색어를 입력하세요."
          />
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

        {canManage ? (
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] px-4 text-white hover:opacity-90`}
            onClick={onCreate}
          >
            신규 등록
          </button>
        ) : (
          <div />
        )}

        <div className="text-right text-sm text-[var(--muted)]">
          총 {data.paging.totalCount}건 / {Math.max(data.paging.totalPages, 1)} 페이지
        </div>
      </div>

      <div className="overflow-x-auto rounded-[24px] border border-white/70">
        <table className="w-full border-collapse">
          <thead className="bg-white/60">
            <tr>
              {["ID", "로그인 ID", "이름", "권한", "이메일", "상태", "최근 로그인", "생성일", "액션"].map(
                (label) => (
                  <th
                    key={label}
                    className="border-b border-[var(--line)] px-3 py-3 text-left text-[0.84rem] font-bold whitespace-nowrap text-[var(--muted)]"
                  >
                    {label}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => {
              const isEditing = editingManagerId === row.id;

              return (
                <tr
                  key={row.id}
                  className={isEditing ? "bg-emerald-50/60" : "transition hover:bg-slate-50/70"}
                >
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.id}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.loginId}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.name}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{getRoleLabel(row.roleType)}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.email}</td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    <StatusPill status={row.status} />
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    {formatDateTime(row.lastLoginAt)}
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    {formatDateTime(row.createdAt)}
                  </td>
                  <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                    <div className="flex flex-wrap gap-2">
                      {canManage ? (
                        <>
                          <button
                            type="button"
                            className={`${buttonClassName} border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                            onClick={() => onEdit(row.id)}
                            disabled={isLoading}
                          >
                            수정
                          </button>
                          <button
                            type="button"
                            className={`${buttonClassName} border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100`}
                            onClick={() => onToggleStatus(row)}
                            disabled={isLoading}
                          >
                            {getToggleStatusLabel(row.status)}
                          </button>
                          <button
                            type="button"
                            className={`${buttonClassName} border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100`}
                            onClick={() => onDelete(row)}
                            disabled={isLoading}
                          >
                            삭제
                          </button>
                        </>
                      ) : (
                        <span className="text-sm text-[var(--muted)]">조회 전용</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {data.items.length === 0 ? (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-10 text-center text-sm text-[var(--muted)]"
                >
                  조회된 관리자가 없습니다.
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
