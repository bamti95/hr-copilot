import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import {
  createCandidate,
  deleteCandidate,
  deleteCandidateDocument,
  downloadCandidateDocument,
  fetchCandidateDetail,
  replaceCandidateDocument,
  updateCandidate,
  updateCandidateStatus,
  uploadCandidateDocuments,
} from "../services/candidateService";
import type {
  CandidateApplyStatus,
  CandidateCreateRequest,
  CandidateDetailResponse,
  CandidateDocumentResponse,
  CandidateFormState,
  CandidatePendingDocument,
  CandidateUpdateRequest,
} from "../types";

type ValidationErrors = Partial<Record<keyof CandidateFormState, string>>;
const MAX_PENDING_DOCUMENT_COUNT = 3;

const emptyForm: CandidateFormState = {
  name: "",
  email: "",
  phone: "",
  birthDate: "",
  applyStatus: "APPLIED",
};

function normalizeValue(value: string) {
  return value.trim();
}

function toRequestPayload(
  form: CandidateFormState,
): CandidateCreateRequest | CandidateUpdateRequest {
  return {
    name: normalizeValue(form.name),
    email: normalizeValue(form.email),
    phone: normalizeValue(form.phone),
    birthDate: normalizeValue(form.birthDate) || null,
  };
}

function toFormState(detail: CandidateDetailResponse): CandidateFormState {
  return {
    name: detail.name,
    email: detail.email,
    phone: detail.phone,
    birthDate: detail.birthDate ?? "",
    applyStatus: detail.applyStatus,
  };
}

function createPendingDocuments(files: File[]): CandidatePendingDocument[] {
  return files.map((file, index) => ({
    id: `${file.name}-${file.lastModified}-${index}`,
    file,
    documentType: "RESUME",
  }));
}

interface UseCandidateDetailOptions {
  mode: "create" | "detail";
  candidateId?: number;
}

export function useCandidateDetail({
  mode,
  candidateId,
}: UseCandidateDetailOptions) {
  const navigate = useNavigate();
  const isCreateMode = mode === "create";
  const [detail, setDetail] = useState<CandidateDetailResponse | null>(null);
  const [form, setForm] = useState<CandidateFormState>(emptyForm);
  const [initialForm, setInitialForm] = useState<CandidateFormState | null>(
    isCreateMode ? emptyForm : null,
  );
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [pendingDocuments, setPendingDocuments] = useState<CandidatePendingDocument[]>([]);
  const [activeDocumentActionId, setActiveDocumentActionId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(!isCreateMode);
  const [isExtractRefreshing, setIsExtractRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const refreshCandidateDetail = async (
    targetCandidateId: number,
    options?: { syncForm?: boolean },
  ) => {
    const shouldSyncForm = options?.syncForm ?? true;
    const refreshedDetail = await fetchCandidateDetail(targetCandidateId);
    setDetail(refreshedDetail);
    if (shouldSyncForm) {
      setForm(toFormState(refreshedDetail));
      setInitialForm(toFormState(refreshedDetail));
    }
  };

  useEffect(() => {
    if (isCreateMode) {
      setDetail(null);
      setForm(emptyForm);
      setInitialForm(emptyForm);
      setPendingDocuments([]);
      setValidationErrors({});
      setIsDetailLoading(false);
      return;
    }

    if (!candidateId) {
      setErrorMessage("지원자 정보를 찾을 수 없습니다.");
      setIsDetailLoading(false);
      return;
    }

    let active = true;

    const run = async () => {
      try {
        setIsDetailLoading(true);
        setErrorMessage("");
        const response = await fetchCandidateDetail(candidateId);

        if (!active) {
          return;
        }

        setDetail(response);
        setForm(toFormState(response));
        setInitialForm(toFormState(response));
        setPendingDocuments([]);
        setValidationErrors({});
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(
          getErrorMessage(error, "지원자 상세 정보를 불러오지 못했습니다."),
        );
      } finally {
        if (active) {
          setIsDetailLoading(false);
        }
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, [candidateId, isCreateMode]);

  useEffect(() => {
    if (
      isCreateMode ||
      !candidateId ||
      !detail?.documents.some((document) => document.extractStatus === "PENDING")
    ) {
      return;
    }

    let active = true;

    const intervalId = window.setInterval(() => {
      if (isSaving) {
        return;
      }

      void (async () => {
        try {
          setIsExtractRefreshing(true);
          const refreshedDetail = await fetchCandidateDetail(candidateId, {
            skipGlobalLoading: true,
          });

          if (!active) {
            return;
          }

          setDetail(refreshedDetail);
        } catch {
          // Keep the current editing state stable if polling fails.
        } finally {
          if (active) {
            setIsExtractRefreshing(false);
          }
        }
      })();
    }, 3000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [candidateId, detail, isCreateMode, isSaving]);

  const validateForm = () => {
    const nextErrors: ValidationErrors = {};
    const name = normalizeValue(form.name);
    const email = normalizeValue(form.email);
    const phone = normalizeValue(form.phone);

    if (!name) {
      nextErrors.name = "지원자 이름을 입력해주세요.";
    } else if (name.length > 100) {
      nextErrors.name = "지원자 이름은 100자 이하로 입력해주세요.";
    }

    if (!email) {
      nextErrors.email = "이메일을 입력해주세요.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "올바른 이메일 형식을 입력해주세요.";
    }

    if (!phone) {
      nextErrors.phone = "전화번호를 입력해주세요.";
    } else if (phone.replace(/\D/g, "").length < 10) {
      nextErrors.phone = "전화번호는 10자리 이상 입력해주세요.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const updateField = <K extends keyof CandidateFormState>(
    key: K,
    value: CandidateFormState[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setValidationErrors((current) => ({ ...current, [key]: undefined }));
  };

  const addPendingFiles = (files: FileList | File[] | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const nextFiles = Array.from(files);

    setPendingDocuments((current) => {
      const remainingSlots = MAX_PENDING_DOCUMENT_COUNT - current.length;

      if (remainingSlots <= 0) {
        setErrorMessage("문서는 최대 3개까지 업로드할 수 있습니다.");
        return current;
      }

      if (nextFiles.length > remainingSlots) {
        setErrorMessage("문서는 최대 3개까지 업로드할 수 있습니다.");
      } else {
        setErrorMessage("");
      }

      const acceptedFiles = nextFiles.slice(0, remainingSlots);
      return [...current, ...createPendingDocuments(acceptedFiles)];
    });
  };

  const updatePendingDocumentType = (
    pendingId: string,
    documentType: CandidatePendingDocument["documentType"],
  ) => {
    setPendingDocuments((current) =>
      current.map((document) =>
        document.id === pendingId ? { ...document, documentType } : document,
      ),
    );
  };

  const removePendingDocument = (pendingId: string) => {
    setPendingDocuments((current) =>
      current.filter((document) => document.id !== pendingId),
    );
    setErrorMessage("");
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      const payload = toRequestPayload(form);

      if (isCreateMode) {
        const created = await createCandidate(payload);

        if (pendingDocuments.length > 0) {
          await uploadCandidateDocuments(created.id, {
            documentTypes: pendingDocuments.map((document) => document.documentType),
            files: pendingDocuments.map((document) => document.file),
          });
        }

        navigate(`/manager/candidates/${created.id}`, { replace: true });
        return;
      }

      if (!candidateId || !initialForm) {
        return;
      }

      const hasInfoChange =
        payload.name !== normalizeValue(initialForm.name) ||
        payload.email !== normalizeValue(initialForm.email) ||
        payload.phone !== normalizeValue(initialForm.phone) ||
        (payload.birthDate || null) !== (normalizeValue(initialForm.birthDate) || null);

      const hasStatusChange = form.applyStatus !== initialForm.applyStatus;

      if (hasInfoChange) {
        await updateCandidate(candidateId, payload);
      }

      if (hasStatusChange) {
        await updateCandidateStatus(candidateId, {
          applyStatus: form.applyStatus,
        });
      }

      if (pendingDocuments.length > 0) {
        await uploadCandidateDocuments(candidateId, {
          documentTypes: pendingDocuments.map((document) => document.documentType),
          files: pendingDocuments.map((document) => document.file),
        });
      }

      await refreshCandidateDetail(candidateId);
      setPendingDocuments([]);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!candidateId || !detail) {
      return;
    }

    const confirmed = window.confirm(`${detail.name} 지원자를 삭제하시겠습니까?`);

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await deleteCandidate(candidateId);
      navigate("/manager/candidates");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadDocument = async (document: CandidateDocumentResponse) => {
    if (!candidateId) {
      return;
    }

    try {
      await downloadCandidateDocument(
        candidateId,
        document.id,
        document.originalFileName,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "문서 다운로드에 실패했습니다."));
    }
  };

  const handleDeleteExistingDocument = async (
    documentId: number,
    fileName: string,
  ) => {
    if (!candidateId) {
      return;
    }

    const confirmed = window.confirm(`${fileName} 파일을 삭제하시겠습니까?`);

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setActiveDocumentActionId(documentId);
      setErrorMessage("");
      await deleteCandidateDocument(candidateId, documentId);
      await refreshCandidateDetail(candidateId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "기존 문서 삭제에 실패했습니다."));
    } finally {
      setActiveDocumentActionId(null);
      setIsSaving(false);
    }
  };

  const handleReplaceExistingDocument = async (
    documentId: number,
    documentType: CandidateDocumentResponse["documentType"],
    file: File | null,
  ) => {
    if (!candidateId || !file) {
      return;
    }

    try {
      setIsSaving(true);
      setActiveDocumentActionId(documentId);
      setErrorMessage("");
      await replaceCandidateDocument(candidateId, documentId, {
        documentType,
        file,
      });
      await refreshCandidateDetail(candidateId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "기존 문서 교체에 실패했습니다."));
    } finally {
      setActiveDocumentActionId(null);
      setIsSaving(false);
    }
  };

  const handleBack = () => {
    navigate("/manager/candidates");
  };

  const handleOpenDocument = (documentId: number) => {
    if (!candidateId) {
      return;
    }

    navigate(`/manager/candidates/${candidateId}/documents/${documentId}`);
  };

  return {
    detail,
    form,
    validationErrors,
    pendingDocuments,
    activeDocumentActionId,
    isSaving,
    isDetailLoading,
    isExtractRefreshing,
    errorMessage,
    isCreateMode,
    handleBack,
    handleSave,
    handleDelete,
    handleDownloadDocument,
    handleOpenDocument,
    updateField,
    addPendingFiles,
    updatePendingDocumentType,
    removePendingDocument,
    handleDeleteExistingDocument,
    handleReplaceExistingDocument,
  };
}
