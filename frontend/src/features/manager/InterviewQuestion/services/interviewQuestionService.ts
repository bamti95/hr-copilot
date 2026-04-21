import { interviewQuestionList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type {
  InterviewQuestionListResponse,
  InterviewQuestionRequest,
  InterviewQuestionResponse,
} from "../types";

export function fetchInterviewQuestionList(
  request: InterviewQuestionRequest,
): InterviewQuestionListResponse {
  return paginateItems(interviewQuestionList, request);
}

export function fetchInterviewQuestionDetail(
  id: number,
): InterviewQuestionResponse | undefined {
  return interviewQuestionList.find((question) => question.id === id);
}
