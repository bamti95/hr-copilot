import { PageIntro } from "../../../common/components/PageIntro";
import { CandidateBoard } from "./components/CandidateBoard";
import { CandidateDetailModal } from "./components/CandidateDetailModal";
import { useCandidateData } from "./hooks/useCandidateData";

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

export default function CandidatePage() {
  const {
    data,
    searchInput,
    statusFilter,
    pageSize,
    isLoading,
    isSaving,
    isDetailLoading,
    errorMessage,
    modalMode,
    detail,
    form,
    validationErrors,
    pendingDocuments,
    activeDocumentActionId,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    handleSearchSubmit,
    handleOpenCreate,
    handleOpenDetail,
    handleCloseModal,
    handleSave,
    handleDelete,
    handleDownloadDocument,
    updateField,
    addPendingFiles,
    updatePendingDocumentType,
    removePendingDocument,
    handleDeleteExistingDocument,
    handleReplaceExistingDocument,
  } = useCandidateData();

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="candidate"
        title="지원자 관리"
        description="지원자 목록을 조회하고, 상세 모달에서 기본 정보 수정, 지원 상태 변경, 문서 다중 등록 및 다운로드를 함께 처리합니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      <CandidateBoard
        data={data}
        isLoading={isLoading || isSaving}
        search={searchInput}
        statusFilter={statusFilter}
        pageSize={pageSize}
        selectedCandidateId={detail?.id ?? null}
        onSearchChange={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onStatusFilterChange={(value) => {
          setPage(1);
          setStatusFilter(value);
        }}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPage(1);
          setPageSize(size);
        }}
        onCreate={handleOpenCreate}
        onView={(candidateId) => void handleOpenDetail(candidateId)}
        onDelete={(row) => void handleDelete(row.id, row.name)}
      />

      <CandidateDetailModal
        isOpen={modalMode !== null}
        modalMode={modalMode}
        detail={detail}
        form={form}
        validationErrors={validationErrors}
        pendingDocuments={pendingDocuments}
        activeDocumentActionId={activeDocumentActionId}
        isSaving={isSaving}
        isDetailLoading={isDetailLoading}
        statusOptions={statusOptions}
        documentTypeOptions={documentTypeOptions}
        onFieldChange={updateField}
        onSave={() => void handleSave()}
        onClose={handleCloseModal}
        onDelete={() => {
          if (detail) {
            void handleDelete(detail.id, detail.name);
          }
        }}
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
      />
    </div>
  );
}
