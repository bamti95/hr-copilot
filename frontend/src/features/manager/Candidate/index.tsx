import { useCallback, useEffect, useState } from "react";
import { PageIntro } from "../../../common/components/PageIntro";
import { getErrorMessage } from "../../../utils/getErrorMessage";
import { DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA } from "../PromptProfile/constants/defaultOutputSchema";
import { PromptProfileFormModal } from "../PromptProfile/components/PromptProfileFormModal";
import { createPromptProfile } from "../PromptProfile/services/promptProfileService";
import type { PromptProfileFormState } from "../PromptProfile/types";
import {
  buildAgentSystemPrompt,
  validateAgentConfigForCreate,
} from "../PromptProfile/utils/buildAgentSystemPrompt";
import { emptyPromptProfileForm } from "../PromptProfile/utils/promptProfileFormDefaults";
import { CandidateAnalysisSessionCreateModal } from "./components/CandidateAnalysisSessionCreateModal";
import { CandidateBoard } from "./components/CandidateBoard";
import { useCandidateData } from "./hooks/useCandidateData";
import type { CandidateJobPosition } from "./types";

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

  const [profileListVersion, setProfileListVersion] = useState(0);
  const [promptProfileDialogMode, setPromptProfileDialogMode] = useState<"closed" | "create">(
    "closed",
  );
  const [promptForm, setPromptForm] = useState<PromptProfileFormState>(() =>
    emptyPromptProfileForm(),
  );
  const [promptFormError, setPromptFormError] = useState("");
  const [isPromptProfileSaving, setIsPromptProfileSaving] = useState(false);
  const [profileInlineSuccess, setProfileInlineSuccess] = useState("");

  useEffect(() => {
    if (!profileInlineSuccess) {
      return;
    }
    const timer = window.setTimeout(() => setProfileInlineSuccess(""), 4000);
    return () => window.clearTimeout(timer);
  }, [profileInlineSuccess]);

  const handlePromptFieldChange = useCallback(
    <K extends keyof PromptProfileFormState>(key: K, value: PromptProfileFormState[K]) => {
      setPromptForm((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const closePromptProfileDialog = useCallback(() => {
    if (isPromptProfileSaving) {
      return;
    }
    setPromptProfileDialogMode("closed");
    setPromptForm(emptyPromptProfileForm());
    setPromptFormError("");
  }, [isPromptProfileSaving]);

  const openCreatePromptProfileForJob = useCallback((presetTargetJob: string) => {
    setPromptForm(
      emptyPromptProfileForm({
        targetJob: presetTargetJob as CandidateJobPosition,
      }),
    );
    setPromptFormError("");
    setPromptProfileDialogMode("create");
  }, []);

  const handlePromptProfileSave = async () => {
    setPromptFormError("");
    const agentErr = validateAgentConfigForCreate(promptForm);
    if (agentErr) {
      setPromptFormError(agentErr);
      return;
    }

    try {
      setIsPromptProfileSaving(true);
      const systemPrompt = buildAgentSystemPrompt(promptForm);
      await createPromptProfile({
        profileKey: promptForm.profileKey.trim(),
        systemPrompt,
        outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
        targetJob: promptForm.targetJob || null,
      });
      setPromptProfileDialogMode("closed");
      setPromptForm(emptyPromptProfileForm());
      setPromptFormError("");
      setProfileListVersion((v) => v + 1);
      setProfileInlineSuccess(
        "프롬프트 프로필을 등록했습니다. 아래 목록에서 선택한 뒤 세션을 생성할 수 있습니다.",
      );
    } catch (error) {
      setPromptFormError(getErrorMessage(error, "저장에 실패했습니다."));
    } finally {
      setIsPromptProfileSaving(false);
    }
  };

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

      {profileInlineSuccess ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {profileInlineSuccess}
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
        profileListVersion={profileListVersion}
        isSubmitting={isCreatingAnalysisSessions}
        onClose={closeAnalysisSessionCreateModal}
        onConfirm={(payload) => void createAnalysisSessions(payload)}
        onOpenCreatePromptProfile={openCreatePromptProfileForJob}
      />

      <PromptProfileFormModal
        mode={promptProfileDialogMode}
        form={promptForm}
        isSaving={isPromptProfileSaving}
        formError={promptFormError}
        onClose={closePromptProfileDialog}
        onFieldChange={handlePromptFieldChange}
        onSubmit={() => void handlePromptProfileSave()}
      />
    </div>
  );
}
