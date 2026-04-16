export interface PagingRequest {
  page: number;
  size: number;
  search?: string;
}

export interface PagingMeta {
  page: number;
  size: number;
  totalCount: number;
  totalPages: number;
}

export interface PagedListResponse<T> {
  items: T[];
  paging: PagingMeta;
}
