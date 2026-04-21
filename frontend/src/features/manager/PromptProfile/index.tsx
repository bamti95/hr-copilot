import { PageIntro } from "../../../common/components/PageIntro";
import { PromptProfileBoard } from "./components/PromptProfileBoard";
import { PromptProfileFormModal } from "./components/PromptProfileFormModal";
import { usePromptProfileData } from "./hooks/usePromptProfileData";

export default function PromptProfilePage() {
  const {
    data,
    searchInput,
    pageSize,
    isLoading,
    errorMessage,
    dialogMode,
    form,
    isSaving,
    formError,
    setSearchInput,
    setPage,
    setPageSize,
    handleSearchSubmit,
    openCreate,
    openEdit,
    closeDialog,
    handleFieldChange,
    handleSave,
    handleDelete,
  } = usePromptProfileData();

  return (
    <>
      <PageIntro
        eyebrow="FR-03"
        title="Prompt Profiles"
        description="시스템 프롬프트와 Output Schema(JSON)를 프로필 단위로 관리합니다."
      />
      <PromptProfileBoard
        data={data}
        isLoading={isLoading}
        errorMessage={errorMessage}
        search={searchInput}
        pageSize={pageSize}
        onSearchChange={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        onCreate={openCreate}
        onEdit={openEdit}
        onDelete={handleDelete}
      />
      <PromptProfileFormModal
        mode={dialogMode}
        form={form}
        isSaving={isSaving}
        formError={formError}
        onClose={closeDialog}
        onFieldChange={handleFieldChange}
        onSubmit={handleSave}
      />
    </>
  );
}
