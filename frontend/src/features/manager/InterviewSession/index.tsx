import { PageIntro } from "../../../common/components/PageIntro";
import { InterviewSessionDetailModal } from "./components/InterviewSessionDetailModal";
import { InterviewSessionBoard } from "./components/InterviewSessionBoard";
import { useInterviewSessionData } from "./hooks/useInterviewSessionData";

export default function InterviewSessionPage() {
  const {
    data,
    candidateOptions,
    promptProfileOptions,
    formMode,
    editingSessionId,
    form,
    validationErrors,
    pageSize,
    candidateFilterId,
    targetJobInput,
    isLoading,
    isSaving,
    errorMessage,
    successMessage,
    detailModalOpen,
    detailModalLoading,
    selectedDetail,
    setPage,
    setPageSize,
    setCandidateFilterId,
    setTargetJobInput,
    handleSearchSubmit,
    handleCreate,
    handleViewDetail,
    handleCloseDetailModal,
    handleEdit,
    handleDelete,
    handleTriggerQuestionGeneration,
    handleCloseForm,
    handleSave,
    updateField,
  } = useInterviewSessionData();

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="interview session"
        title="면접 세션 관리"
        description="면접 세션을 조회하고, 세션 생성 및 질문 분석 트리거를 실행할 수 있습니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      {successMessage ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {successMessage}
        </div>
      ) : null}

      <InterviewSessionBoard
        data={data}
        candidateOptions={candidateOptions}
        promptProfileOptions={promptProfileOptions}
        formMode={formMode}
        editingSessionId={editingSessionId}
        form={form}
        validationErrors={validationErrors}
        isLoading={isLoading}
        isSaving={isSaving}
        pageSize={pageSize}
        candidateFilterId={candidateFilterId}
        targetJobInput={targetJobInput}
        onCandidateFilterChange={(value) => {
          setPage(1);
          setCandidateFilterId(value);
        }}
        onTargetJobInputChange={setTargetJobInput}
        onSearchSubmit={handleSearchSubmit}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPage(1);
          setPageSize(size);
        }}
        onCreate={() => void handleCreate()}
        onView={handleViewDetail}
        onCloseForm={handleCloseForm}
        onSave={() => void handleSave()}
        onFormChange={updateField}
      />

      <InterviewSessionDetailModal
        open={detailModalOpen}
        detail={selectedDetail}
        isLoading={detailModalLoading}
        isSaving={isSaving}
        onClose={handleCloseDetailModal}
        onEdit={(sessionId) => void handleEdit(sessionId)}
        onDelete={(sessionId, candidateName) =>
          void handleDelete(sessionId, candidateName)
        }
        onTriggerQuestionGeneration={(sessionId) =>
          void handleTriggerQuestionGeneration(sessionId)
        }
      />
    </div>
  );
}
