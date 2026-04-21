import { PageIntro } from "../../../../common/components/PageIntro";
import { CandidateDetailModal } from "../components/CandidateDetailModal";
import { useCandidateDetail } from "../hooks/useCandidateDetail";

const statusOptions = [
  "APPLIED",
  "SCREENING",
  "INTERVIEW",
  "ACCEPTED",
  "REJECTED",
] as const;

const documentTypeOptions = [
  "RESUME",
  "PORTFOLIO",
  "COVER_LETTER",
  "CAREER_DESCRIPTION",
  "ROLE_PROFILE",
] as const;

interface CandidateDetailPageProps {
  mode: "create" | "detail";
  candidateId?: number;
}

export default function CandidateDetailPage({
  mode,
  candidateId,
}: CandidateDetailPageProps) {
  const {
    detail,
    form,
    validationErrors,
    pendingDocuments,
    activeDocumentActionId,
    isSaving,
    isDetailLoading,
    isExtractRefreshing,
    errorMessage,
    handleBack,
    handleSave,
    handleDelete,
    handleDownloadDocument,
    handleOpenDocument,
    updateField,
    addPendingFiles,
    updatePendingDocumentType,
    removePendingDocument,
    handleDeleteExistingDocument,
    handleReplaceExistingDocument,
  } = useCandidateDetail({
    mode,
    candidateId,
  });

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="candidate"
        title={mode === "create" ? "지원자 등록" : "지원자 상세"}
        description="지원자 기본 정보, 진행 상태, 문서 업로드와 기존 문서 관리를 페이지 전환형으로 제공합니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      <CandidateDetailModal
        mode={mode}
        detail={detail}
        form={form}
        validationErrors={validationErrors}
        pendingDocuments={pendingDocuments}
        activeDocumentActionId={activeDocumentActionId}
        isSaving={isSaving}
        isDetailLoading={isDetailLoading}
        isExtractRefreshing={isExtractRefreshing}
        statusOptions={statusOptions}
        documentTypeOptions={documentTypeOptions}
        onFieldChange={updateField}
        onSave={() => void handleSave()}
        onBack={handleBack}
        onDelete={() => void handleDelete()}
        onAddFiles={addPendingFiles}
        onPendingDocumentTypeChange={updatePendingDocumentType}
        onPendingDocumentRemove={removePendingDocument}
        onDocumentDownload={(document) => void handleDownloadDocument(document)}
        onExistingDocumentDelete={(document) =>
          void handleDeleteExistingDocument(document.id, document.originalFileName)
        }
        onExistingDocumentReplace={(document, file) =>
          void handleReplaceExistingDocument(document.id, document.documentType, file)
        }
        onOpenDocument={(document) => handleOpenDocument(document.id)}
      />
    </div>
  );
}
