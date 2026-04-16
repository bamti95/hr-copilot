import { PageIntro } from "../../../common/components/PageIntro";
import { CandidateBoard } from "./components/CandidateBoard";
import { useCandidateData } from "./hooks/useCandidateData";

export default function CandidatePage() {
  const { data, setPage, search, setSearch } = useCandidateData();

  return (
    <>
      <PageIntro
        eyebrow="FR-02"
        title="Candidate Management"
        description="지원자 통합 정보와 지원 상태를 관리하는 영역입니다."
      />
      <CandidateBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
