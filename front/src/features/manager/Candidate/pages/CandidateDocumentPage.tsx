import { PageIntro } from "../../../../common/components/PageIntro";
import { CandidateDocumentDetail } from "../components/CandidateDocumentDetail";
import { useCandidateDocumentDetail } from "../hooks/useCandidateDocumentDetail";

interface CandidateDocumentPageProps {
  candidateId?: number;
  documentId?: number;
}

export default function CandidateDocumentPage({
  candidateId,
  documentId,
}: CandidateDocumentPageProps) {
  const {
    candidate,
    document,
    isLoading,
    errorMessage,
    handleBack,
    handleDownload,
  } = useCandidateDocumentDetail({
    candidateId,
    documentId,
  });

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="document"
        title="지원 문서 상세"
        description="문서 메타 정보와 추출 텍스트를 분리된 화면에서 확인하고 다운로드할 수 있습니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      <CandidateDocumentDetail
        candidate={candidate}
        document={document}
        isLoading={isLoading}
        onBack={handleBack}
        onDownload={() => void handleDownload()}
      />
    </div>
  );
}
