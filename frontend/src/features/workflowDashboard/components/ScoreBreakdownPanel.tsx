import { JsonViewer } from "./JsonViewer";
import { BottomPanel, EmptyState } from "./QuestionResultPanel";
import {
  getArray,
  getNestedRecord,
  type LlmCallLog,
} from "../types/workflowDashboard.types";

interface ScoreBreakdownPanelProps {
  logs: LlmCallLog[];
  finalResponse: Record<string, unknown> | null;
}

export function ScoreBreakdownPanel({
  logs,
  finalResponse,
}: ScoreBreakdownPanelProps) {
  const metadata = getNestedRecord(finalResponse, "generation_metadata");
  const reviewSummary = getNestedRecord(metadata, "review_summary");
  const scores = logs.flatMap((log) => getArray(log.outputJson, "scores"));

  return (
    <BottomPanel title="점수 평가">
      {reviewSummary ? (
        <JsonViewer value={reviewSummary} />
      ) : scores.length > 0 ? (
        <JsonViewer value={{ scores }} />
      ) : (
        <EmptyState text="현재 로그에는 점수 평가 데이터가 없습니다." />
      )}
    </BottomPanel>
  );
}

