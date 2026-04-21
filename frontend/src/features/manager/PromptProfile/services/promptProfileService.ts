import api from "../../../../services/api";
import type { PagingMeta } from "../../../../common/types/pagination";
import type {
  PromptProfileCreateRequest,
  PromptProfileListRequest,
  PromptProfileListResponse,
  PromptProfileResponse,
  PromptProfileUpdateRequest,
} from "../types";

interface PromptProfileApiResponse {
  id: number;
  profile_key: string;
  system_prompt: string;
  output_schema: string | null;
  target_job?: string | null;
  created_at: string;
  created_by: number | null;
  updated_at: string;
  deleted_at: string | null;
  deleted_by: number | null;
}

interface PromptProfileListApiResponse {
  prompt_profiles: PromptProfileApiResponse[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    items_per_page: number;
  };
}

function mapPromptProfile(response: PromptProfileApiResponse): PromptProfileResponse {
  return {
    id: response.id,
    profileKey: response.profile_key,
    systemPrompt: response.system_prompt,
    outputSchema: response.output_schema,
    targetJob: response.target_job ?? null,
    createdAt: response.created_at,
    createdBy: response.created_by,
    updatedAt: response.updated_at,
    deletedAt: response.deleted_at,
    deletedBy: response.deleted_by,
  };
}

function toPagingMeta(response: PromptProfileListApiResponse): PagingMeta {
  return {
    page: response.pagination.current_page,
    size: response.pagination.items_per_page,
    totalCount: response.pagination.total_items,
    totalPages: response.pagination.total_pages,
  };
}

export async function fetchPromptProfileList(
  request: PromptProfileListRequest,
): Promise<PromptProfileListResponse> {
  const response = await api.get<PromptProfileListApiResponse>("/prompt-profiles", {
    params: {
      page: request.page,
      limit: request.limit,
      search: request.search?.trim() || undefined,
      target_job: request.targetJob?.trim() || undefined,
    },
  });

  return {
    items: response.data.prompt_profiles.map(mapPromptProfile),
    paging: toPagingMeta(response.data),
  };
}

export async function fetchPromptProfileDetail(id: number): Promise<PromptProfileResponse> {
  const response = await api.get<PromptProfileApiResponse>(`/prompt-profiles/${id}`);
  return mapPromptProfile(response.data);
}

function toCreatePayload(body: PromptProfileCreateRequest) {
  return {
    profile_key: body.profileKey.trim(),
    system_prompt: body.systemPrompt.trim(),
    output_schema:
      body.outputSchema === undefined || body.outputSchema === null
        ? null
        : body.outputSchema.trim() || null,
    target_job:
      body.targetJob === undefined || body.targetJob === null
        ? null
        : body.targetJob.trim() || null,
  };
}

function toUpdatePayload(body: PromptProfileUpdateRequest) {
  const trimmed = body.outputSchema.trim();
  return {
    system_prompt: body.systemPrompt.trim(),
    output_schema: trimmed === "" ? null : trimmed,
  };
}

export async function createPromptProfile(
  requestBody: PromptProfileCreateRequest,
): Promise<PromptProfileResponse> {
  const response = await api.post<PromptProfileApiResponse>(
    "/prompt-profiles",
    toCreatePayload(requestBody),
  );
  return mapPromptProfile(response.data);
}

export async function updatePromptProfile(
  profileId: number,
  requestBody: PromptProfileUpdateRequest,
): Promise<PromptProfileResponse> {
  const response = await api.put<PromptProfileApiResponse>(
    `/prompt-profiles/${profileId}`,
    toUpdatePayload(requestBody),
  );
  return mapPromptProfile(response.data);
}

export async function deletePromptProfile(profileId: number): Promise<void> {
  await api.delete(`/prompt-profiles/${profileId}`);
}
