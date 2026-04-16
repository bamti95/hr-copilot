import type { PagingMeta } from "../types/pagination";

interface PaginationProps {
  paging: PagingMeta;
  onPageChange: (page: number) => void;
}

export function Pagination({ paging, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: paging.totalPages }, (_, index) => index + 1);

  return (
    <div className="pagination">
      <span className="pagination__meta">
        Showing {(paging.page - 1) * paging.size + 1} to{" "}
        {Math.min(paging.page * paging.size, paging.totalCount)} of{" "}
        {paging.totalCount}
      </span>
      <div className="pagination__actions">
        <button
          type="button"
          className="pagination__button"
          onClick={() => onPageChange(Math.max(1, paging.page - 1))}
          disabled={paging.page === 1}
        >
          Prev
        </button>
        {pages.map((page) => (
          <button
            key={page}
            type="button"
            className={`pagination__button ${page === paging.page ? "is-active" : ""}`}
            onClick={() => onPageChange(page)}
          >
            {page}
          </button>
        ))}
        <button
          type="button"
          className="pagination__button"
          onClick={() => onPageChange(Math.min(paging.totalPages, paging.page + 1))}
          disabled={paging.page === paging.totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
