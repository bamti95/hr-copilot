import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA } from "../../PromptProfile/constants/defaultOutputSchema";
import { createPromptProfile } from "../../PromptProfile/services/promptProfileService";
import type { PromptProfileFormState, PromptProfileResponse } from "../../PromptProfile/types";
import { buildAgentSystemPrompt, validateAgentConfigForCreate } from "../../PromptProfile/utils/buildAgentSystemPrompt";
import { emptyPromptProfileForm } from "../../PromptProfile/utils/promptProfileFormDefaults";
import {
  deleteCandidate,
  fetchCandidateList,
  fetchCandidateStatistics,
} from "../services/candidateService";
import type {
  CandidateApplyStatus,
  CandidateListResponse,
  CandidateStatisticsResponse,
} from "../types";

export function useCandidateData() {
  const navigate = useNavigate();
  const [data, setData] = useState<CandidateListResponse>({
    items: [],
    paging: { page: 1, size: 10, totalCount: 0, totalPages: 0 },
  });
  const [statistics, setStatistics] = useState<CandidateStatisticsResponse | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<CandidateApplyStatus | "ALL">(
    "ALL",
  );
  const [jobFilter, setJobFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [promptWizardOpen, setPromptWizardOpen] = useState(false);
  const [promptCreateOpen, setPromptCreateOpen] = useState(false);
  const [promptForm, setPromptForm] = useState<PromptProfileFormState>(emptyPromptProfileForm());
  const [promptFormError, setPromptFormError] = useState("");
  const [promptSaving, setPromptSaving] = useState(false);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const stats = await fetchCandidateStatistics();
        if (active) {
          setStatistics(stats);
        }
      } catch {
        if (active) {
          setStatistics(null);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!successMessage) {
      return;
    }
    const t = window.setTimeout(() => setSuccessMessage(""), 4000);
    return () => window.clearTimeout(t);
  }, [successMessage]);

  const jobQuery = jobFilter.trim() || undefined;

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const response = await fetchCandidateList({
          page,
          limit: pageSize,
          search: searchKeyword || undefined,
          applyStatus: statusFilter === "ALL" ? undefined : statusFilter,
          targetJob: jobQuery,
        });

        if (!active) {
          return;
        }

        setData(response);
        setSelectedIds([]);
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(
          getErrorMessage(error, "지원자 목록을 불러오지 못했습니다."),
        );
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, [page, pageSize, searchKeyword, statusFilter, jobFilter]);

  const loadCandidates = useCallback(async () => {
    const response = await fetchCandidateList({
      page,
      limit: pageSize,
      search: searchKeyword || undefined,
      applyStatus: statusFilter === "ALL" ? undefined : statusFilter,
      targetJob: jobQuery,
    });
    setData(response);
  }, [page, pageSize, searchKeyword, statusFilter, jobQuery]);

  const handleSearchSubmit = () => {
    setPage(1);
    setSearchKeyword(searchInput.trim());
  };

  const handleJobFilterChange = (value: string) => {
    setPage(1);
    setJobFilter(value);
    setSelectedIds([]);
  };

  const handleOpenCreate = () => {
    navigate("/manager/candidates/new");
  };

  const handleOpenDetail = (candidateId: number) => {
    navigate(`/manager/candidates/${candidateId}`);
  };

  const handleDelete = async (candidateId: number, candidateName: string) => {
    const confirmed = window.confirm(
      `${candidateName} 지원자를 삭제하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");
      await deleteCandidate(candidateId);
      await loadCandidates();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 삭제에 실패했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const selectAllOnPage = () => {
    const ids = data.items.map((r) => r.id);
    if (ids.length === 0) {
      return;
    }
    const allSelected = ids.every((id) => selectedIds.includes(id));
    setSelectedIds(allSelected ? [] : ids);
  };

  const openPromptWizard = () => {
    if (!jobQuery || selectedIds.length === 0) {
      return;
    }
    setPromptWizardOpen(true);
  };

  const closePromptWizard = () => {
    setPromptWizardOpen(false);
  };

  const openPromptCreateFromWizard = () => {
    setPromptWizardOpen(false);
    setPromptForm(
      emptyPromptProfileForm({
        jobTitle: jobFilter.trim(),
      }),
    );
    setPromptFormError("");
    setPromptCreateOpen(true);
  };

  const closePromptCreate = () => {
    setPromptCreateOpen(false);
    setPromptForm(emptyPromptProfileForm());
    setPromptFormError("");
  };

  const handlePromptFieldChange = <K extends keyof PromptProfileFormState>(
    key: K,
    value: PromptProfileFormState[K],
  ) => {
    setPromptForm((prev) => ({ ...prev, [key]: value }));
  };

  const handlePromptCreateSave = async () => {
    setPromptFormError("");
    const err = validateAgentConfigForCreate(promptForm);
    if (err) {
      setPromptFormError(err);
      return;
    }
    try {
      setPromptSaving(true);
      await createPromptProfile({
        profileKey: promptForm.profileKey.trim(),
        systemPrompt: buildAgentSystemPrompt(promptForm),
        outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
        targetJob: jobFilter.trim() || promptForm.jobTitle.trim() || null,
      });
      closePromptCreate();
      setSuccessMessage("프롬프트 프로필이 등록되었습니다.");
    } catch (error) {
      setPromptFormError(getErrorMessage(error, "저장에 실패했습니다."));
    } finally {
      setPromptSaving(false);
    }
  };

  const handlePickExistingProfile = (row: PromptProfileResponse) => {
    setPromptWizardOpen(false);
    setSuccessMessage(
      `프로필「${row.profileKey}」을(를) 선택했습니다. (저장 연동 없음)`,
    );
  };

  return {
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
  };
}
