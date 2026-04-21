import { useCallback, useEffect, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA } from "../constants/defaultOutputSchema";
import {
  createPromptProfile,
  deletePromptProfile,
  fetchPromptProfileList,
  updatePromptProfile,
} from "../services/promptProfileService";
import type {
  PromptProfileFormState,
  PromptProfileListResponse,
  PromptProfileResponse,
} from "../types";
import { buildAgentSystemPrompt, validateAgentConfigForCreate } from "../utils/buildAgentSystemPrompt";
import { emptyPromptProfileForm } from "../utils/promptProfileFormDefaults";

export function usePromptProfileData() {
  const [data, setData] = useState<PromptProfileListResponse>({
    items: [],
    paging: { page: 1, size: 20, totalCount: 0, totalPages: 0 },
  });
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [dialogMode, setDialogMode] = useState<"closed" | "create" | "edit">("closed");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<PromptProfileFormState>(emptyPromptProfileForm());
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const loadList = useCallback(async () => {
    const response = await fetchPromptProfileList({
      page,
      limit: pageSize,
      search: searchKeyword.trim() || undefined,
    });
    setData(response);
  }, [page, pageSize, searchKeyword]);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const response = await fetchPromptProfileList({
          page,
          limit: pageSize,
          search: searchKeyword.trim() || undefined,
        });
        if (!active) {
          return;
        }
        setData(response);
      } catch (error) {
        if (!active) {
          return;
        }
        setErrorMessage(
          getErrorMessage(error, "프롬프트 프로필 목록을 불러오지 못했습니다."),
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
  }, [page, pageSize, searchKeyword]);

  const handleSearchSubmit = () => {
    setPage(1);
    setSearchKeyword(searchInput.trim());
  };

  const openCreate = () => {
    setForm(emptyPromptProfileForm());
    setEditingId(null);
    setFormError("");
    setDialogMode("create");
  };

  const openEdit = (row: PromptProfileResponse) => {
    setForm({
      ...emptyPromptProfileForm(),
      profileKey: row.profileKey,
      systemPrompt: row.systemPrompt,
      outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
    });
    setEditingId(row.id);
    setFormError("");
    setDialogMode("edit");
  };

  const closeDialog = () => {
    setDialogMode("closed");
    setEditingId(null);
    setForm(emptyPromptProfileForm());
    setFormError("");
  };

  const handleFieldChange = <K extends keyof PromptProfileFormState>(
    key: K,
    value: PromptProfileFormState[K],
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setFormError("");
    if (dialogMode === "create") {
      const agentErr = validateAgentConfigForCreate(form);
      if (agentErr) {
        setFormError(agentErr);
        return;
      }
    } else if (!form.systemPrompt.trim()) {
      setFormError("시스템 프롬프트는 필수입니다.");
      return;
    }

    try {
      setIsSaving(true);
      if (dialogMode === "create") {
        const systemPrompt = buildAgentSystemPrompt(form);
        await createPromptProfile({
          profileKey: form.profileKey.trim(),
          systemPrompt,
          outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
          targetJob: form.jobTitle.trim() || null,
        });
      } else if (dialogMode === "edit" && editingId !== null) {
        await updatePromptProfile(editingId, {
          systemPrompt: form.systemPrompt.trim(),
          outputSchema: DEFAULT_PROMPT_PROFILE_OUTPUT_SCHEMA,
        });
      }
      closeDialog();
      await loadList();
    } catch (error) {
      setFormError(getErrorMessage(error, "저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (row: PromptProfileResponse) => {
    const confirmed = window.confirm(
      `프로필 "${row.profileKey}" 을(를) 삭제하시겠습니까? (논리 삭제)`,
    );
    if (!confirmed) {
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");
      await deletePromptProfile(row.id);
      await loadList();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "삭제에 실패했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  return {
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
  };
}
