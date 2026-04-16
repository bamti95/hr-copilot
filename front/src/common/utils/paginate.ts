import type { PagedListResponse, PagingRequest } from "../types/pagination";

export function paginateItems<T>(
  items: T[],
  request: PagingRequest,
): PagedListResponse<T> {
  const { page, size, search } = request;
  const keyword = search?.trim().toLowerCase();

  const filteredItems = keyword
    ? items.filter((item) => JSON.stringify(item).toLowerCase().includes(keyword))
    : items;

  const totalCount = filteredItems.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / size));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * size;

  return {
    items: filteredItems.slice(start, start + size),
    paging: {
      page: safePage,
      size,
      totalCount,
      totalPages,
    },
  };
}
