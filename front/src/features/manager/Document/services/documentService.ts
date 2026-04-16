import { documentList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type {
  DocumentListResponse,
  DocumentRequest,
  DocumentResponse,
} from "../types";

export function fetchDocumentList(request: DocumentRequest): DocumentListResponse {
  return paginateItems(documentList, request);
}

export function fetchDocumentDetail(id: number): DocumentResponse | undefined {
  return documentList.find((document) => document.id === id);
}
