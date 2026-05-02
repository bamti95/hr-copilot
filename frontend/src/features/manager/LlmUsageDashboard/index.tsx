import { PageIntro } from "../../../common/components/PageIntro";
import WorkflowDashboardPage from "../../workflowDashboard/pages/WorkflowDashboardPage";

export default function LlmUsageDashboardPage() {
  return (
    <>
      <PageIntro
        eyebrow="관측성"
        title="워크플로우 대쉬보드"
        description="LangGraph 질문 생성 세션의 노드 흐름, 입력/출력, 토큰, 비용, 오류를 운영 관점에서 확인합니다."
      />
      <WorkflowDashboardPage />
    </>
  );
}
