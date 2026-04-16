import { PageIntro } from "../../../common/components/PageIntro";
import { InterviewSessionBoard } from "./components/InterviewSessionBoard";
import { useInterviewSessionData } from "./hooks/useInterviewSessionData";

export default function InterviewSessionPage() {
  const { data, setPage, search, setSearch } = useInterviewSessionData();

  return (
    <>
      <PageIntro
        eyebrow="FR-03"
        title="Interview Sessions"
        description="후보자와 채용 기준을 조합해 인터뷰 세션을 생성하고 확인합니다."
      />
      <InterviewSessionBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
