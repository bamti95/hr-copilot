import { promptProfileList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type {
  PromptProfileListResponse,
  PromptProfileRequest,
  PromptProfileResponse,
} from "../types";

export function fetchPromptProfileList(
  request: PromptProfileRequest,
): PromptProfileListResponse {
  return paginateItems(promptProfileList, request);
}

export function fetchPromptProfileDetail(
  id: number,
): PromptProfileResponse | undefined {
  return promptProfileList.find((profile) => profile.id === id);
}
