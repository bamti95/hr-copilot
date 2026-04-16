import { PageIntro } from "../../../common/components/PageIntro";
import { InterviewQuestionBoard } from "./components/InterviewQuestionBoard";
import { useInterviewQuestionData } from "./hooks/useInterviewQuestionData";

export default function InterviewQuestionPage() {
  const { data, setPage, search, setSearch } = useInterviewQuestionData();

  return (
    <>
      <PageIntro
        eyebrow="FR-04"
        title="Interview Questions"
        description="질문 생성 근거와 기대 답변을 함께 검토할 수 있는 템플릿입니다."
      />
      <InterviewQuestionBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
