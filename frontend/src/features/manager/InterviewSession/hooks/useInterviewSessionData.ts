import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { fetchPromptProfileList } from "../../PromptProfile/services/promptProfileService";
import {
  createInterviewSession,
  deleteInterviewSession,
  fetchInterviewSessionCandidateOptions,
  fetchInterviewSessionDetail,
  fetchInterviewSessionList,
  triggerInterviewQuestionGeneration,
  updateInterviewSession,
} from "../services/interviewSessionService";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionDetailResponse,
  InterviewSessionFormState,
  InterviewSessionListResponse,
  InterviewSessionPromptProfileOption,
  InterviewSessionResponse,
} from "../types";

type FormMode = "create" | "edit" | null;
type ValidationErrors = Partial<Record<keyof InterviewSessionFormState, string>>;

interface InterviewSessionPageState {
  candidateId?: number;
  candidateName?: string;
  targetJob?: string;
  promptProfileId?: number;
  openCreate?: boolean;
  openDetailSessionId?: number;
}

const emptyForm: InterviewSessionFormState = {
  candidateId: "",
  targetJob: "",
  difficultyLevel: "",
  promptProfileId: "",
  graphPipeline: "default",
};

export function useInterviewSessionData() {
  const navigate = useNavigate();
  const location = useLocation();
  const hasConsumedLocationState = useRef(false);

  const [data, setData] = useState<InterviewSessionListResponse>({
    items: [],
    paging: { page: 1, size: 10, totalCount: 0, totalPages: 0 },
  });
  const [candidateOptions, setCandidateOptions] = useState<
    InterviewSessionCandidateOption[]
  >([]);
  const [promptProfileOptions, setPromptProfileOptions] = useState<
    InterviewSessionPromptProfileOption[]
  >([]);
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
  const [form, setForm] = useState<InterviewSessionFormState>(emptyForm);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [jobFilter, setJobFilter] = useState("");
  const [candidateNameInput, setCandidateNameInput] = useState("");
  const [candidateNameKeyword, setCandidateNameKeyword] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailModalLoading, setDetailModalLoading] = useState(false);
  const [selectedDetail, setSelectedDetail] =
    useState<InterviewSessionDetailResponse | null>(null);

  const loadSessions = async () => {
    const response = await fetchInterviewSessionList({
      page,
      limit: pageSize,
      targetJob: jobFilter || undefined,
      candidateName: candidateNameKeyword || undefined,
    });
    setData(response);
  };

  const loadCandidateOptions = async () => {
    const response = await fetchInterviewSessionCandidateOptions();
    setCandidateOptions(response);
    return response;
  };

  const loadPromptProfileOptions = async () => {
    const response = await fetchPromptProfileList({
      page: 1,
      limit: 100,
    });
    const nextOptions = response.items.map((item) => ({
      id: item.id,
      profileKey: item.profileKey,
      targetJob: item.targetJob,
    }));
    setPromptProfileOptions(nextOptions);
    return nextOptions;
  };

  useEffect(() => {
    if (!successMessage) {
      return;
    }
    const timer = window.setTimeout(() => setSuccessMessage(""), 4000);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setErrorMessage("");
        const [candidateResponse, promptProfileResponse] = await Promise.all([
          fetchInterviewSessionCandidateOptions(),
          fetchPromptProfileList({ page: 1, limit: 100 }),
        ]);

        if (!active) {
          return;
        }

        setCandidateOptions(candidateResponse);
        setPromptProfileOptions(
          promptProfileResponse.items.map((item) => ({
            id: item.id,
            profileKey: item.profileKey,
            targetJob: item.targetJob,
          })),
        );
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(
          getErrorMessage(error, "세션 생성에 필요한 후보 데이터 로딩에 실패했습니다."),
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
          targetJob: jobFilter || undefined,
          candidateName: candidateNameKeyword || undefined,
        });

        if (!active) {
          return;
        }

        setData(response);
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(getErrorMessage(error, "면접 세션 목록을 불러오지 못했습니다."));
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
  }, [page, pageSize, jobFilter, candidateNameKeyword]);

  useEffect(() => {
    if (hasConsumedLocationState.current) {
      return;
    }

    const state = (location.state ?? {}) as InterviewSessionPageState;
    if (
      !state.openCreate &&
      !state.candidateId &&
      !state.targetJob &&
      !state.openDetailSessionId
    ) {
      return;
    }

    hasConsumedLocationState.current = true;

    if (state.candidateId) {
      setForm((current) => ({
        ...current,
        candidateId: String(state.candidateId),
      }));
    }

    if (state.targetJob) {
      setJobFilter(state.targetJob);
      setForm((current) => ({
        ...current,
        targetJob: state.targetJob ?? "",
      }));
    }

    if (state.promptProfileId) {
      setForm((current) => ({
        ...current,
        promptProfileId: String(state.promptProfileId),
      }));
    }

    if (state.openCreate) {
      setFormMode("create");
      setEditingSessionId(null);
    }

    if (state.openDetailSessionId) {
      const sessionId = state.openDetailSessionId;
      const openDetail = async () => {
        try {
          setDetailModalLoading(true);
          setErrorMessage("");
          const detail = await fetchInterviewSessionDetail(sessionId);
          setSelectedDetail(detail);
          setDetailModalOpen(true);
        } catch (error) {
          setErrorMessage(
            getErrorMessage(error, "세션 상세 정보를 불러오지 못했습니다."),
          );
        } finally {
          setDetailModalLoading(false);
        }
      };

      void openDetail();
    }

    void navigate(location.pathname, { replace: true, state: null });
  }, [location.pathname, location.state, navigate]);

  const validateForm = () => {
    const nextErrors: ValidationErrors = {};
    const candidateId = Number(form.candidateId);
    const targetJob = form.targetJob.trim();
    const difficultyLevel = form.difficultyLevel.trim();
    const promptProfileId = Number(form.promptProfileId);

    if (formMode === "create" && (!candidateId || Number.isNaN(candidateId))) {
      nextErrors.candidateId = "지원자를 선택해 주세요.";
    }

    if (!targetJob) {
      nextErrors.targetJob = "목표 직무를 입력해 주세요.";
    } else if (targetJob.length > 50) {
      nextErrors.targetJob = "목표 직무는 50자 이하로 입력해 주세요.";
    }

    if (difficultyLevel.length > 20) {
      nextErrors.difficultyLevel = "난이도는 20자 이하로 입력해 주세요.";
    }

    if (formMode === "create" && (!promptProfileId || Number.isNaN(promptProfileId))) {
      nextErrors.promptProfileId = "프롬프트 프로필을 선택해 주세요.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const syncForm = (session: InterviewSessionResponse) => {
    setForm({
      candidateId: String(session.candidateId),
      targetJob: session.targetJob,
      difficultyLevel: session.difficultyLevel ?? "",
      promptProfileId: session.promptProfileId ? String(session.promptProfileId) : "",
      graphPipeline: "default",
    });
  };

  const handleSearchSubmit = () => {
    setPage(1);
    setCandidateNameKeyword(candidateNameInput.trim());
  };

  const handleCreate = async () => {
    try {
      setErrorMessage("");
      if (candidateOptions.length === 0) {
        await loadCandidateOptions();
      }
      if (promptProfileOptions.length === 0) {
        await loadPromptProfileOptions();
      }
      setValidationErrors({});
      setEditingSessionId(null);
      setSelectedDetail(null);
      setDetailModalOpen(false);
      setForm((current) => ({
        ...emptyForm,
        candidateId: current.candidateId,
        targetJob: current.targetJob || jobFilter,
        promptProfileId: current.promptProfileId,
      }));
      setFormMode("create");
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "세션 생성에 필요한 데이터를 준비하지 못했습니다."),
      );
    }
  };

  const handleEdit = async (sessionId: number) => {
    try {
      setIsLoading(true);
      setErrorMessage("");
      setValidationErrors({});
      const detail = await fetchInterviewSessionDetail(sessionId);
      syncForm(detail);
      setSelectedDetail(detail);
      setDetailModalOpen(false);
      setEditingSessionId(sessionId);
      setFormMode("edit");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "세션 상세 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetail = async (sessionId: number) => {
    try {
      setDetailModalLoading(true);
      setErrorMessage("");
      const detail = await fetchInterviewSessionDetail(sessionId);
      setSelectedDetail(detail);
      setDetailModalOpen(true);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "세션 상세 정보를 불러오지 못했습니다."));
    } finally {
      setDetailModalLoading(false);
    }
  };

  const handleCloseDetailModal = () => {
    if (isSaving) {
      return;
    }
    setDetailModalOpen(false);
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

  const refreshSelectedDetailIfNeeded = async (sessionId: number) => {
    if (selectedDetail?.id !== sessionId) {
      return;
    }
    const detail = await fetchInterviewSessionDetail(sessionId);
    setSelectedDetail(detail);
  };

  const handleSave = async () => {
    if (!formMode || !validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      let savedSessionId: number | null = null;

      if (formMode === "create") {
        const created = await createInterviewSession({
          candidateId: Number(form.candidateId),
          targetJob: form.targetJob.trim(),
          difficultyLevel: form.difficultyLevel.trim() || null,
          promptProfileId: Number(form.promptProfileId),
          graphPipeline: form.graphPipeline,
        });
        savedSessionId = created.id;
      } else if (editingSessionId) {
        const updated = await updateInterviewSession(editingSessionId, {
          targetJob: form.targetJob.trim(),
          difficultyLevel: form.difficultyLevel.trim() || null,
        });
        savedSessionId = updated.id;
      }

      await loadSessions();

      if (savedSessionId) {
        await refreshSelectedDetailIfNeeded(savedSessionId);
      }

      handleCloseForm();
      setSuccessMessage(
        formMode === "create"
          ? "면접 세션이 생성되었습니다."
          : "면접 세션이 수정되었습니다.",
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "면접 세션 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (sessionId: number, candidateName: string) => {
    const confirmed = window.confirm(
      `${candidateName} 지원자의 면접 세션을 삭제하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await deleteInterviewSession(sessionId);
      await loadSessions();
      setSuccessMessage("면접 세션이 삭제되었습니다.");

      if (selectedDetail?.id === sessionId) {
        setDetailModalOpen(false);
        setSelectedDetail(null);
      }

      if (editingSessionId === sessionId) {
        handleCloseForm();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "면접 세션 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleTriggerQuestionGeneration = async (sessionId: number) => {
    try {
      setIsSaving(true);
      setErrorMessage("");
      await triggerInterviewQuestionGeneration(sessionId, {
        triggerType: "MANUAL",
      });
      setSuccessMessage("질문 생성 요청을 전송했습니다.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "질문 생성 요청에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  return {
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
  };
}
