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
    jobFilter,
    candidateNameInput,
    isLoading,
    isSaving,
    errorMessage,
    successMessage,
    detailModalOpen,
    detailModalLoading,
    selectedDetail,
    setPage,
    setPageSize,
    setJobFilter,
    setCandidateNameInput,
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
        description="현재 백엔드 세션 API 스펙에 맞춰 목록, 생성, 수정, 모달 상세 흐름을 제공합니다."
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
        jobFilter={jobFilter}
        candidateNameInput={candidateNameInput}
        onJobFilterChange={(value) => {
          setPage(1);
          setJobFilter(value);
        }}
        onCandidateNameInputChange={setCandidateNameInput}
        onSearchSubmit={handleSearchSubmit}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPage(1);
          setPageSize(size);
        }}
        onCreate={() => void handleCreate()}
        onView={(sessionId) => void handleViewDetail(sessionId)}
        onEdit={(sessionId) => void handleEdit(sessionId)}
        onDelete={(sessionId, candidateName) =>
          void handleDelete(sessionId, candidateName)
        }
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
