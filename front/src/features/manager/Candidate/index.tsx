import { PageIntro } from "../../../common/components/PageIntro";
import { CandidateBoard } from "./components/CandidateBoard";
import { useCandidateData } from "./hooks/useCandidateData";

export default function CandidatePage() {
  const {
    data,
    searchInput,
    statusFilter,
    pageSize,
    isLoading,
    errorMessage,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    handleSearchSubmit,
    handleOpenCreate,
    handleOpenDetail,
    handleDelete,
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

      <CandidateBoard
        data={data}
        isLoading={isLoading}
        search={searchInput}
        statusFilter={statusFilter}
        pageSize={pageSize}
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
        onView={handleOpenDetail}
        onDelete={(row) => void handleDelete(row.id, row.name)}
      />
    </div>
  );
}
