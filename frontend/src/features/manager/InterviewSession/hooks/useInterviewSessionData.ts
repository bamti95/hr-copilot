import { useEffect, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import {
  createInterviewSession,
  deleteInterviewSession,
  fetchInterviewSessionCandidateOptions,
  fetchInterviewSessionDetail,
  fetchInterviewSessionList,
  updateInterviewSession,
} from "../services/interviewSessionService";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionFormState,
  InterviewSessionListResponse,
  InterviewSessionResponse,
} from "../types";

type FormMode = "create" | "edit" | null;
type ValidationErrors = Partial<Record<keyof InterviewSessionFormState, string>>;

const emptyForm: InterviewSessionFormState = {
  candidateId: "",
  targetJob: "",
  difficultyLevel: "",
};

export function useInterviewSessionData() {
  const [data, setData] = useState<InterviewSessionListResponse>({
    items: [],
    paging: { page: 1, size: 10, totalCount: 0, totalPages: 0 },
  });
  const [candidateOptions, setCandidateOptions] = useState<
    InterviewSessionCandidateOption[]
  >([]);
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
  const [form, setForm] = useState<InterviewSessionFormState>(emptyForm);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [candidateFilterId, setCandidateFilterId] = useState("");
  const [targetJobInput, setTargetJobInput] = useState("");
  const [targetJobKeyword, setTargetJobKeyword] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadSessions = async () => {
    const response = await fetchInterviewSessionList({
      page,
      limit: pageSize,
      candidateId: candidateFilterId ? Number(candidateFilterId) : undefined,
      targetJob: targetJobKeyword || undefined,
    });
    setData(response);
  };

  const loadCandidateOptions = async () => {
    const response = await fetchInterviewSessionCandidateOptions();
    setCandidateOptions(response);
  };

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setErrorMessage("");
        const response = await fetchInterviewSessionCandidateOptions();

        if (!active) {
          return;
        }

        setCandidateOptions(response);
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(
          getErrorMessage(error, "지원자 목록을 불러오지 못했습니다."),
        );
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const response = await fetchInterviewSessionList({
          page,
          limit: pageSize,
          candidateId: candidateFilterId ? Number(candidateFilterId) : undefined,
          targetJob: targetJobKeyword || undefined,
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
          getErrorMessage(error, "인터뷰 세션 목록을 불러오지 못했습니다."),
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
  }, [page, pageSize, candidateFilterId, targetJobKeyword]);

  const validateForm = () => {
    const nextErrors: ValidationErrors = {};
    const candidateId = Number(form.candidateId);
    const targetJob = form.targetJob.trim();
    const difficultyLevel = form.difficultyLevel.trim();

    if (formMode === "create" && (!candidateId || Number.isNaN(candidateId))) {
      nextErrors.candidateId = "지원자를 선택해주세요.";
    }

    if (!targetJob) {
      nextErrors.targetJob = "목표 직무를 입력해주세요.";
    } else if (targetJob.length > 50) {
      nextErrors.targetJob = "목표 직무는 50자 이하로 입력해주세요.";
    }

    if (difficultyLevel.length > 20) {
      nextErrors.difficultyLevel = "난이도는 20자 이하로 입력해주세요.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const syncForm = (session: InterviewSessionResponse) => {
    setForm({
      candidateId: String(session.candidateId),
      targetJob: session.targetJob,
      difficultyLevel: session.difficultyLevel ?? "",
    });
  };

  const handleSearchSubmit = () => {
    setPage(1);
    setTargetJobKeyword(targetJobInput.trim());
  };

  const handleCreate = async () => {
    try {
      setErrorMessage("");
      if (candidateOptions.length === 0) {
        await loadCandidateOptions();
      }
      setValidationErrors({});
      setEditingSessionId(null);
      setForm(emptyForm);
      setFormMode("create");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 목록을 불러오지 못했습니다."));
    }
  };

  const handleEdit = async (sessionId: number) => {
    try {
      setIsLoading(true);
      setErrorMessage("");
      setValidationErrors({});
      const detail = await fetchInterviewSessionDetail(sessionId);
      syncForm(detail);
      setEditingSessionId(sessionId);
      setFormMode("edit");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "인터뷰 세션 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseForm = () => {
    setFormMode(null);
    setEditingSessionId(null);
    setValidationErrors({});
    setForm(emptyForm);
  };

  const updateField = <K extends keyof InterviewSessionFormState>(
    key: K,
    value: InterviewSessionFormState[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setValidationErrors((current) => ({ ...current, [key]: undefined }));
  };

  const handleSave = async () => {
    if (!formMode || !validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      if (formMode === "create") {
        await createInterviewSession({
          candidateId: Number(form.candidateId),
          targetJob: form.targetJob.trim(),
          difficultyLevel: form.difficultyLevel.trim() || null,
        });
      } else if (editingSessionId) {
        await updateInterviewSession(editingSessionId, {
          targetJob: form.targetJob.trim(),
          difficultyLevel: form.difficultyLevel.trim() || null,
        });
      }

      await loadSessions();
      handleCloseForm();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "인터뷰 세션 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (sessionId: number, candidateName: string) => {
    const confirmed = window.confirm(
      `${candidateName} 인터뷰 세션을 삭제하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await deleteInterviewSession(sessionId);
      await loadSessions();

      if (editingSessionId === sessionId) {
        handleCloseForm();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "인터뷰 세션 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  return {
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
  };
}
