import type { PagingMeta } from "../types/pagination";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

interface PaginationProps {
  paging: PagingMeta;
  onPageChange: (page: number) => void;
}

const buttonBaseClassName =
  "inline-flex h-10 min-w-10 items-center justify-center gap-1 rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 text-sm font-medium text-[var(--text)] shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--primary)]/30 hover:bg-[var(--panel)] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0";

const activeButtonClassName =
  "border-transparent bg-linear-to-br from-[var(--primary)] to-[var(--primary-strong)] text-white shadow-[0_10px_24px_color-mix(in_srgb,var(--primary)_28%,transparent)] hover:border-transparent hover:bg-linear-to-br";

function getVisiblePages(currentPage: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  if (currentPage <= 4) {
    return [1, 2, 3, 4, 5, "...", totalPages];
  }

  if (currentPage >= totalPages - 3) {
    return [1, "...", totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  }

  return [1, "...", currentPage - 1, currentPage, currentPage + 1, "...", totalPages];
}

export function Pagination({ paging, onPageChange }: PaginationProps) {
  const totalPages = Math.max(paging.totalPages, 1);
  const currentPage = Math.min(Math.max(paging.page, 1), totalPages);
  const pages = getVisiblePages(currentPage, totalPages);

  const startItem =
    paging.totalCount === 0 ? 0 : (currentPage - 1) * paging.size + 1;
  const endItem =
    paging.totalCount === 0
      ? 0
      : Math.min(currentPage * paging.size, paging.totalCount);

  return (
    <div className="mt-5 flex flex-col gap-4 rounded-[22px] border border-(--line) bg-(--panel) px-5 py-4 shadow-sm md:flex-row md:items-center md:justify-between">
      <div className="flex flex-1 flex-col gap-1">
        <span className="text-sm font-medium text-(--text)">
          Showing {startItem} to {endItem}
        </span>
        <span className="text-xs text-(--muted)">
          Total {paging.totalCount} items · Page {currentPage} of {totalPages}
        </span>
      </div>

      <div className="flex flex-2 flex-wrap items-center justify-center gap-2">        
        <button
          type="button"
          className={buttonBaseClassName}
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1 || paging.totalCount === 0}
          aria-label="Go to first page"
        >
          <ChevronsLeft className="h-4 w-4" />
          <span className="hidden sm:inline">First</span>
        </button>

        <button
          type="button"
          className={buttonBaseClassName}
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1 || paging.totalCount === 0}
          aria-label="Go to previous page"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Prev</span>
        </button>

        {pages.map((page, index) =>
          page === "..." ? (
            <span
              key={`ellipsis-${index}`}
              className="inline-flex h-10 min-w-10 items-center justify-center px-1 text-sm font-medium text-(--muted)"
            >
              ...
            </span>
          ) : (
            <button
              key={page}
              type="button"
              className={`${buttonBaseClassName} ${
                page === currentPage ? activeButtonClassName : ""
              }`}
              onClick={() => onPageChange(page as number)}
              aria-current={page === currentPage ? "page" : undefined}
            >
              {page}
            </button>
          ),
        )}

        <button
          type="button"
          className={buttonBaseClassName}
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages || paging.totalCount === 0}
          aria-label="Go to next page"
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="h-4 w-4" />
        </button>

        <button
          type="button"
          className={buttonBaseClassName}
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages || paging.totalCount === 0}
          aria-label="Go to last page"
        >
          <span className="hidden sm:inline">Last</span>
          <ChevronsRight className="h-4 w-4" />
        </button>
      </div>

      <div className="hidden flex-1 md:block" />

    </div>
  );
}