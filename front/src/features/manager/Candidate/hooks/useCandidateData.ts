import { useEffect, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import {
  createCandidate,
  deleteCandidate,
  deleteCandidateDocument,
  downloadCandidateDocument,
  fetchCandidateDetail,
  fetchCandidateList,
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
  CandidateListResponse,
  CandidatePendingDocument,
  CandidateUpdateRequest,
} from "../types";

type CandidateModalMode = "create" | "detail" | null;
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

export function useCandidateData() {
  const [data, setData] = useState<CandidateListResponse>({
    items: [],
    paging: { page: 1, size: 10, totalCount: 0, totalPages: 0 },
  });
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<CandidateApplyStatus | "ALL">(
    "ALL",
  );
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [modalMode, setModalMode] = useState<CandidateModalMode>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [detail, setDetail] = useState<CandidateDetailResponse | null>(null);
  const [form, setForm] = useState<CandidateFormState>(emptyForm);
  const [initialForm, setInitialForm] = useState<CandidateFormState | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [pendingDocuments, setPendingDocuments] = useState<CandidatePendingDocument[]>([]);
  const [activeDocumentActionId, setActiveDocumentActionId] = useState<number | null>(null);

  const loadCandidates = async () => {
    const response = await fetchCandidateList({
      page,
      limit: pageSize,
      search: searchKeyword || undefined,
      applyStatus: statusFilter === "ALL" ? undefined : statusFilter,
    });
    setData(response);
  };

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
  }, [page, pageSize, searchKeyword, statusFilter]);

  const validateForm = () => {
    const nextErrors: ValidationErrors = {};
    const name = normalizeValue(form.name);
    const email = normalizeValue(form.email);
    const phone = normalizeValue(form.phone);

    if (!name) {
      nextErrors.name = "지원자 이름을 입력해 주세요.";
    } else if (name.length > 100) {
      nextErrors.name = "지원자 이름은 100자 이하로 입력해 주세요.";
    }

    if (!email) {
      nextErrors.email = "이메일을 입력해 주세요.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "올바른 이메일 형식을 입력해 주세요.";
    }

    if (!phone) {
      nextErrors.phone = "전화번호를 입력해 주세요.";
    } else if (phone.replace(/\D/g, "").length < 10) {
      nextErrors.phone = "전화번호는 10자리 이상 입력해 주세요.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const resetModalState = () => {
    setModalMode(null);
    setSelectedCandidateId(null);
    setDetail(null);
    setForm(emptyForm);
    setInitialForm(null);
    setValidationErrors({});
    setPendingDocuments([]);
  };

  const handleSearchSubmit = () => {
    setPage(1);
    setSearchKeyword(normalizeValue(searchInput));
  };

  const handleOpenCreate = () => {
    setErrorMessage("");
    setValidationErrors({});
    setDetail(null);
    setInitialForm(emptyForm);
    setForm(emptyForm);
    setPendingDocuments([]);
    setSelectedCandidateId(null);
    setModalMode("create");
  };

  const handleOpenDetail = async (candidateId: number) => {
    try {
      setIsDetailLoading(true);
      setErrorMessage("");
      const response = await fetchCandidateDetail(candidateId);
      setDetail(response);
      setSelectedCandidateId(candidateId);
      setForm(toFormState(response));
      setInitialForm(toFormState(response));
      setPendingDocuments([]);
      setValidationErrors({});
      setModalMode("detail");
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "지원자 상세 정보를 불러오지 못했습니다."),
      );
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleCloseModal = () => {
    if (isSaving) {
      return;
    }
    resetModalState();
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      const payload = toRequestPayload(form);
      let targetCandidateId = selectedCandidateId;

      if (modalMode === "create") {
        const created = await createCandidate(payload);
        targetCandidateId = created.id;
      } else if (modalMode === "detail" && selectedCandidateId && initialForm) {
        const hasInfoChange =
          payload.name !== normalizeValue(initialForm.name) ||
          payload.email !== normalizeValue(initialForm.email) ||
          payload.phone !== normalizeValue(initialForm.phone) ||
          (payload.birthDate || null) !==
            (normalizeValue(initialForm.birthDate) || null);

        const hasStatusChange = form.applyStatus !== initialForm.applyStatus;

        if (hasInfoChange) {
          await updateCandidate(selectedCandidateId, payload);
        }

        if (hasStatusChange) {
          await updateCandidateStatus(selectedCandidateId, {
            applyStatus: form.applyStatus,
          });
        }
      }

      if (targetCandidateId && pendingDocuments.length > 0) {
        await uploadCandidateDocuments(targetCandidateId, {
          documentTypes: pendingDocuments.map((document) => document.documentType),
          files: pendingDocuments.map((document) => document.file),
        });
      }

      await loadCandidates();

      if (targetCandidateId && modalMode === "detail") {
        const refreshedDetail = await fetchCandidateDetail(targetCandidateId);
        setDetail(refreshedDetail);
        setForm(toFormState(refreshedDetail));
        setInitialForm(toFormState(refreshedDetail));
        setPendingDocuments([]);
      } else {
        resetModalState();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (candidateId: number, candidateName: string) => {
    const confirmed = window.confirm(
      `${candidateName} 지원자를 삭제하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await deleteCandidate(candidateId);
      await loadCandidates();

      if (selectedCandidateId === candidateId) {
        resetModalState();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadDocument = async (document: CandidateDocumentResponse) => {
    if (!selectedCandidateId) {
      return;
    }

    try {
      await downloadCandidateDocument(
        selectedCandidateId,
        document.id,
        document.originalFileName,
      );
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "문서 다운로드에 실패했습니다."),
      );
    }
  };

  const refreshCandidateDetail = async (candidateId: number) => {
    const refreshedDetail = await fetchCandidateDetail(candidateId);
    setDetail(refreshedDetail);
    setForm(toFormState(refreshedDetail));
    setInitialForm(toFormState(refreshedDetail));
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
        setErrorMessage("문서 업로드는 최대 3개까지 가능합니다.");
        return current;
      }

      if (nextFiles.length > remainingSlots) {
        setErrorMessage("문서 업로드는 최대 3개까지 가능합니다.");
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

  const handleDeleteExistingDocument = async (
    documentId: number,
    fileName: string,
  ) => {
    if (!selectedCandidateId) {
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
      await deleteCandidateDocument(selectedCandidateId, documentId);
      await refreshCandidateDetail(selectedCandidateId);
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
    if (!selectedCandidateId || !file) {
      return;
    }

    try {
      setIsSaving(true);
      setActiveDocumentActionId(documentId);
      setErrorMessage("");
      await replaceCandidateDocument(selectedCandidateId, documentId, {
        documentType,
        file,
      });
      await refreshCandidateDetail(selectedCandidateId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "기존 문서 교체에 실패했습니다."));
    } finally {
      setActiveDocumentActionId(null);
      setIsSaving(false);
    }
  };

  return {
    data,
    searchInput,
    statusFilter,
    pageSize,
    isLoading,
    isSaving,
    isDetailLoading,
    errorMessage,
    modalMode,
    detail,
    form,
    validationErrors,
    pendingDocuments,
    activeDocumentActionId,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    handleSearchSubmit,
    handleOpenCreate,
    handleOpenDetail,
    handleCloseModal,
    handleSave,
    handleDelete,
    handleDownloadDocument,
    updateField,
    addPendingFiles,
    updatePendingDocumentType,
    removePendingDocument,
    handleDeleteExistingDocument,
    handleReplaceExistingDocument,
  };
}
