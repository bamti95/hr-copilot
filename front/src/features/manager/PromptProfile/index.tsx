import { PageIntro } from "../../../common/components/PageIntro";
import { PromptProfileBoard } from "./components/PromptProfileBoard";
import { usePromptProfileData } from "./hooks/usePromptProfileData";

export default function PromptProfilePage() {
  const { data, setPage, search, setSearch } = usePromptProfileData();

  return (
    <>
      <PageIntro
        eyebrow="FR-03"
        title="Prompt Profiles"
        description="Persona와 Output Schema를 프로파일 단위로 관리하는 템플릿입니다."
      />
      <PromptProfileBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
