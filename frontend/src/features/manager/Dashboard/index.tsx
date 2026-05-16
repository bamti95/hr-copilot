import { PageIntro } from "../../../common/components/PageIntro";
import { DashboardOverview } from "./components/DashboardOverview";
import { useDashboardData } from "./hooks/useDashboardData";

export default function DashboardPage() {
  const { data, isLoading, error, reload } = useDashboardData();

  return (
    <>
      <PageIntro
        eyebrow="HR Workspace"
        title="대시보드"
        description="오늘 확인해야 할 지원자, 문서 분석, 면접 질문 생성, 채용공고 RAG 분석과 비용을 한 화면에서 확인합니다."
      />
      <DashboardOverview
        data={data}
        isLoading={isLoading}
        error={error}
        onRefresh={() => {
          void reload();
        }}
      />
    </>
  );
}
