import { PageIntro } from "../../../common/components/PageIntro";
import { PromptProfileFormModal } from "../PromptProfile/components/PromptProfileFormModal";
import { CandidateBoard } from "./components/CandidateBoard";
import { CandidatePromptProfileActionModal } from "./components/CandidatePromptProfileActionModal";
import { useCandidateData } from "./hooks/useCandidateData";

export default function CandidatePage() {
  const {
    data,
    statistics,
    searchInput,
    statusFilter,
    jobFilter,
    pageSize,
    selectedIds,
    isLoading,
    errorMessage,
    successMessage,
    promptWizardOpen,
    promptCreateOpen,
    promptForm,
    promptFormError,
    promptSaving,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    handleSearchSubmit,
    handleJobFilterChange,
    handleOpenCreate,
    handleOpenDetail,
    handleDelete,
    toggleSelect,
    selectAllOnPage,
    openPromptWizard,
    closePromptWizard,
    openPromptCreateFromWizard,
    closePromptCreate,
    handlePromptFieldChange,
    handlePromptCreateSave,
    handlePickExistingProfile,
  } = useCandidateData();

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="candidate"
        title="지원자 관리"
        description="지원자 목록을 조회하고, 페이지 전환형 상세 화면에서 기본 정보와 문서를 함께 관리합니다."
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

      <CandidateBoard
        data={data}
        statistics={statistics}
        isLoading={isLoading}
        search={searchInput}
        statusFilter={statusFilter}
        jobFilter={jobFilter}
        pageSize={pageSize}
        selectedIds={selectedIds}
        onSearchChange={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onStatusFilterChange={(value) => {
          setPage(1);
          setStatusFilter(value);
        }}
        onJobFilterChange={handleJobFilterChange}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPage(1);
          setPageSize(size);
        }}
        onCreate={handleOpenCreate}
        onView={handleOpenDetail}
        onDelete={(row) => void handleDelete(row.id, row.name)}
        onToggleSelect={toggleSelect}
        onSelectAllOnPage={selectAllOnPage}
        onOpenPromptProfileWizard={openPromptWizard}
      />

      <CandidatePromptProfileActionModal
        open={promptWizardOpen}
        targetJob={jobFilter.trim()}
        onClose={closePromptWizard}
        onPickExisting={handlePickExistingProfile}
        onCreateNew={openPromptCreateFromWizard}
      />

      <PromptProfileFormModal
        mode={promptCreateOpen ? "create" : "closed"}
        form={promptForm}
        isSaving={promptSaving}
        formError={promptFormError}
        onClose={closePromptCreate}
        onFieldChange={handlePromptFieldChange}
        onSubmit={() => void handlePromptCreateSave()}
      />
    </div>
  );
}
