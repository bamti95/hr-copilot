import { PageIntro } from "../../../common/components/PageIntro";
import { DashboardOverview } from "./components/DashboardOverview";
import { useDashboardData } from "./hooks/useDashboardData";

export default function DashboardPage() {
  const { metrics, activities } = useDashboardData();

  return (
    <>
      <PageIntro
        eyebrow="Manager Workspace"
        title="HR Copilot Dashboard"
        description="요구사항 정의서를 기준으로 통합 계정, 지원자, 문서, 프롬프트, 인터뷰 운영을 한 화면에서 시작하는 템플릿입니다."
      />
      <DashboardOverview metrics={metrics} activities={activities} />
    </>
  );
}
