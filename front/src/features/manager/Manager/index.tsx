import { PageIntro } from "../../../common/components/PageIntro";
import { ManagerBoard } from "./components/ManagerBoard";
import { useManagerData } from "./hooks/useManagerData";

export default function ManagerPage() {
  const { data, setPage, search, setSearch } = useManagerData();

  return (
    <>
      <PageIntro
        eyebrow="FR-01"
        title="Manager & Auth"
        description="관리자 계정 생성, 상태 제어, 목록/상세 조회를 위한 템플릿 영역입니다."
      />
      <ManagerBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
