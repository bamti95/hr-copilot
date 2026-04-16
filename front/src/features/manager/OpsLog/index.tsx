import { PageIntro } from "../../../common/components/PageIntro";
import { OpsLogBoard } from "./components/OpsLogBoard";
import { useOpsLogData } from "./hooks/useOpsLogData";

export default function OpsLogPage() {
  const { data, setPage, search, setSearch } = useOpsLogData();

  return (
    <>
      <PageIntro
        eyebrow="FR-05"
        title="Ops & Logging"
        description="LLM 호출 로그와 비용/상태 추적을 위한 운영 템플릿입니다."
      />
      <OpsLogBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
