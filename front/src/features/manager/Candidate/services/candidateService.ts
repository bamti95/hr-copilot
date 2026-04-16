import { candidateList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type {
  CandidateListResponse,
  CandidateRequest,
  CandidateResponse,
} from "../types";

export function fetchCandidateList(
  request: CandidateRequest,
): CandidateListResponse {
  return paginateItems(candidateList, request);
}

export function fetchCandidateDetail(id: number): CandidateResponse | undefined {
  return candidateList.find((candidate) => candidate.id === id);
}
