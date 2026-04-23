import { createInterviewSession } from "../../InterviewSession/services/interviewSessionService";
import { fetchPromptProfileDetail } from "../../PromptProfile/services/promptProfileService";
import type {
  AnalysisSessionCreateItem,
  AnalysisSessionCreateRequest,
  AnalysisSessionCreateResponse,
} from "../types";

export async function buildPromptProfileSnapshot(
  promptProfileId: number,
): Promise<Record<string, unknown>> {
  const detail = await fetchPromptProfileDetail(promptProfileId);
  return {
    id: detail.id,
    profileKey: detail.profileKey,
    targetJob: detail.targetJob,
    systemPrompt: detail.systemPrompt,
    outputSchema: detail.outputSchema,
    createdAt: detail.createdAt,
    updatedAt: detail.updatedAt,
  };
}

export async function createAnalysisSessions(
  request: AnalysisSessionCreateRequest,
): Promise<AnalysisSessionCreateResponse> {
  const candidateIds = request.candidateIds.filter((id) => Number.isFinite(id));
  if (candidateIds.length === 0) {
    return { items: [] };
  }

  const promptProfileSnapshot =
    request.promptProfileSnapshot ??
    (await buildPromptProfileSnapshot(request.promptProfileId));

  const created = await Promise.all<AnalysisSessionCreateItem>(
    candidateIds.map(async (candidateId) => {
      const session = await createInterviewSession({
        candidateId,
        targetJob: request.targetJob,
        difficultyLevel: request.difficultyLevel ?? null,
        promptProfileId: request.promptProfileId,
      });

      return {
        sessionId: session.id,
        candidateId: session.candidateId,
        targetJob: session.targetJob,
        difficultyLevel: session.difficultyLevel as AnalysisSessionCreateItem["difficultyLevel"],
        promptProfileId: request.promptProfileId,
        status: "READY" as const,
        createdAt: session.createdAt,
      };
    }),
  );

  void promptProfileSnapshot;

  return {
    items: created,
  };
}
