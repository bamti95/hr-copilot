import { PageIntro } from "../../../common/components/PageIntro";
import { InterviewSessionBoard } from "./components/InterviewSessionBoard";
import { useInterviewSessionData } from "./hooks/useInterviewSessionData";

export default function InterviewSessionPage() {
  const {
    data,
    candidateOptions,
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
    setPage,
    setPageSize,
    setCandidateFilterId,
    setTargetJobInput,
    handleSearchSubmit,
    handleCreate,
    handleEdit,
    handleDelete,
    handleCloseForm,
    handleSave,
    updateField,
  } = useInterviewSessionData();

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="interview session"
        title="인터뷰 세션 관리"
        description="인터뷰 세션 목록을 조회하고, 목표 직무와 난이도를 기준으로 세션을 생성하거나 수정할 수 있습니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      <InterviewSessionBoard
        data={data}
        candidateOptions={candidateOptions}
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
        onEdit={(sessionId) => void handleEdit(sessionId)}
        onDelete={(row) => void handleDelete(row.id, row.candidateName)}
        onCloseForm={handleCloseForm}
        onSave={() => void handleSave()}
        onFormChange={updateField}
      />
    </div>
  );
}
