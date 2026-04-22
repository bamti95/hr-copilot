import { DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA } from "../constants/defaultOutputSchema";
import type { PromptProfileFormState } from "../types";

export function emptyPromptProfileForm(partial?: Partial<PromptProfileFormState>): PromptProfileFormState {
  return {
    profileKey: "",
    systemPrompt: "",
    outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
    agentName: "",
    department: "",
    targetJob: "",
    mustHaveStack: [],
    niceToHaveStack: [],
    requiredCertificates: [],
    requiredEducation: [],
    ...partial,
  };
}
