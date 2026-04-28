import { PageIntro } from "../../../common/components/PageIntro";
import { LlmUsageOverview } from "./components/LlmUsageOverview";
import { useLlmUsageData } from "./hooks/useLlmUsageData";
import type { LlmUsageSummaryResponse } from "./types";

const emptyData: LlmUsageSummaryResponse = {
  metrics: {
    totalCalls: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    totalTokens: 0,
    estimatedCost: 0,
    avgElapsedMs: 0,
    failedCalls: 0,
  },
  byNode: [],
  bySession: [],
  recentCalls: [],
};

export default function LlmUsageDashboardPage() {
  const { data, isLoading, error, reload } = useLlmUsageData();
  const usageData = data ?? emptyData;

  return (
    <>
      <PageIntro
        eyebrow="Observability"
        title="LLM 사용량 대시보드"
        description="LangGraph 면접 질문 생성 파이프라인의 노드별 입력 토큰, 출력 토큰, 예상 비용, 호출 시간을 한눈에 확인합니다."
      />
      <LlmUsageOverview
        metrics={usageData.metrics}
        byNode={usageData.byNode}
        bySession={usageData.bySession}
        recentCalls={usageData.recentCalls}
        isLoading={isLoading}
        error={error}
        onRefresh={() => {
          void reload();
        }}
      />
    </>
  );
}
