import { PageIntro } from "../../../common/components/PageIntro";
import { CandidateAnalysisSessionCreateModal } from "./components/CandidateAnalysisSessionCreateModal";
import { CandidateBoard } from "./components/CandidateBoard";
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
    isAnalysisSessionCreateModalOpen,
    isCreatingAnalysisSessions,
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
    openAnalysisSessionCreateModal,
    closeAnalysisSessionCreateModal,
    createAnalysisSessions,
  } = useCandidateData();

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="candidate"
        title="지원자 관리"
        description="지원자 목록을 조회하고, 필터와 선택 상태를 기준으로 분석 세션 생성을 준비할 수 있습니다."
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
        onOpenAnalysisSessionCreateModal={openAnalysisSessionCreateModal}
      />

      <CandidateAnalysisSessionCreateModal
        open={isAnalysisSessionCreateModalOpen}
        selectedCount={selectedIds.length}
        targetJob={jobFilter.trim()}
        isSubmitting={isCreatingAnalysisSessions}
        onClose={closeAnalysisSessionCreateModal}
        onConfirm={(payload) => void createAnalysisSessions(payload)}
      />
    </div>
  );
}
