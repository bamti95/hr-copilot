import { DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA } from "../constants/defaultOutputSchema";
import type { DepartmentRealityFormState, PromptProfileFormState } from "../types";

export function emptyDepartmentReality(): DepartmentRealityFormState {
  return {
    q1: { selectedIds: [], customItems: [] },
    q2: { selectedIds: [], customItems: [] },
    q3: { selectedIds: [], customItems: [] },
    q4: { selectedIds: [], customItems: [] },
  };
}

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
    departmentReality: emptyDepartmentReality(),
    ...partial,
  };
}
