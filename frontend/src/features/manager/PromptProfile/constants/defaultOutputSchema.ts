/** 서버 JSON 검증을 통과하는 고정 Output schema (UI 비표시). */
export const DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA = JSON.stringify(
  {
    questions: [{ question_text: "string", competency: "string", rationale: "string" }],
  },
  null,
  0,
);
