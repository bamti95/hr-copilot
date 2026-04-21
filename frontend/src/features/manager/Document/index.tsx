import { PageIntro } from "../../../common/components/PageIntro";
import { DocumentBoard } from "./components/DocumentBoard";
import { useDocumentData } from "./hooks/useDocumentData";

export default function DocumentPage() {
  const { data, setPage, search, setSearch } = useDocumentData();

  return (
    <>
      <PageIntro
        eyebrow="FR-02"
        title="Document & OCR"
        description="이력서/포트폴리오 업로드와 텍스트 추출 상태를 관리하는 영역입니다."
      />
      <DocumentBoard
        data={data}
        search={search}
        onSearchChange={setSearch}
        onPageChange={setPage}
      />
    </>
  );
}
