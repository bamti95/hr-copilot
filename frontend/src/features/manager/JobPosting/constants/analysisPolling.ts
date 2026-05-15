/**
 * Max time to poll `GET .../analysis-jobs/{id}` while a compliance / Agentic RAG
 * analysis runs. Hybrid retrieval + per-issue evidence can exceed a few minutes;
 * a short cap caused false "polling stopped" UX while the server still succeeded.
 */
export const JOB_POSTING_ANALYSIS_POLLING_TIMEOUT_MS = 30 * 60 * 1000;
