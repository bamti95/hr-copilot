import { interviewSessionList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type {
  InterviewSessionListResponse,
  InterviewSessionRequest,
  InterviewSessionResponse,
} from "../types";

export function fetchInterviewSessionList(
  request: InterviewSessionRequest,
): InterviewSessionListResponse {
  return paginateItems(interviewSessionList, request);
}

export function fetchInterviewSessionDetail(
  id: number,
): InterviewSessionResponse | undefined {
  return interviewSessionList.find((session) => session.id === id);
}
