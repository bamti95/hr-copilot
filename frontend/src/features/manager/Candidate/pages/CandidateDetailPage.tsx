import { useEffect, useState } from "react";
import { PageIntro } from "../../../../common/components/PageIntro";
import { CandidateDetailModal } from "../components/CandidateDetailModal";
import { useCandidateDetail } from "../hooks/useCandidateDetail";
import {
  confirmDocumentBulkImport,
  fetchDocumentBulkPreviewJob,
  fetchDocumentBulkPreviewJobs,
  previewDocumentBulkImport,
} from "../services/candidateService";
import type {
  DocumentBulkImportPreviewRequest,
  DocumentBulkImportPreviewJobResponse,
} from "../types";

const statusOptions = [
  "APPLIED",
  "SCREENING",
  "INTERVIEW",
  "ACCEPTED",
  "REJECTED",
] as const;

const jobPositionOptions = [
  "STRATEGY_PLANNING",
  "HR",
  "MARKETING",
  "AI_DEV_DATA",
  "SALES",
] as const;

const documentTypeOptions = [
  "RESUME",
  "PORTFOLIO",
  "COVER_LETTER",
  "CAREER_DESCRIPTION",
  "ROLE_PROFILE",
] as const;

interface CandidateDetailPageProps {
  mode: "create" | "detail";
  candidateId?: number;
}

export default function CandidateDetailPage({
  mode,
  candidateId,
}: CandidateDetailPageProps) {
  const [registrationMode, setRegistrationMode] = useState<"single" | "bulk">(
    "single",
  );
  const [documentBulkPreview, setDocumentBulkPreview] =
    useState<DocumentBulkImportPreviewJobResponse | null>(null);
  const [documentBulkJobId, setDocumentBulkJobId] = useState<number | null>(null);
  const [isDocumentBulkPreviewing, setIsDocumentBulkPreviewing] = useState(false);
  const [isDocumentBulkImporting, setIsDocumentBulkImporting] = useState(false);
  const [documentBulkErrorMessage, setDocumentBulkErrorMessage] = useState("");
  const {
    detail,
    form,
    validationErrors,
    pendingDocuments,
    activeDocumentActionId,
    isSaving,
    isDetailLoading,
    isExtractRefreshing,
    errorMessage,
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
  } = useCandidateDetail({
    mode,
    candidateId,
  });

  useEffect(() => {
    if (mode !== "create") {
      return;
    }

    let active = true;

    const hydrateActiveDocumentBulkJob = async () => {
      try {
        const response = await fetchDocumentBulkPreviewJobs({
          activeOnly: true,
          limit: 1,
        });
        if (!active) {
          return;
        }
        const latestJob = response.jobs[0] ?? null;
        if (latestJob) {
          setRegistrationMode("bulk");
          setDocumentBulkPreview(latestJob);
          setDocumentBulkJobId(latestJob.jobId);
        }
      } catch {
        if (active) {
          setDocumentBulkJobId(null);
        }
      }
    };

    void hydrateActiveDocumentBulkJob();

    return () => {
      active = false;
    };
  }, [mode]);

  useEffect(() => {
    if (!documentBulkJobId) {
      return;
    }

    let active = true;
    const terminalStatuses = new Set([
      "SUCCESS",
      "PARTIAL_SUCCESS",
      "FAILED",
      "CANCELLED",
    ]);

    const poll = async () => {
      try {
        const job = await fetchDocumentBulkPreviewJob(documentBulkJobId);
        if (!active) {
          return;
        }
        setDocumentBulkPreview(job);
        if (terminalStatuses.has(job.status)) {
          setDocumentBulkJobId(null);
          if (job.status === "FAILED") {
            setDocumentBulkErrorMessage(
              job.errorMessage || "문서 일괄등록 미리보기 작업이 실패했습니다.",
            );
          }
        }
      } catch (error) {
        if (!active) {
          return;
        }
        setDocumentBulkJobId(null);
        const message =
          error instanceof Error
            ? error.message
            : "문서 일괄등록 미리보기 작업 상태를 불러오지 못했습니다.";
        setDocumentBulkErrorMessage(message);
      }
    };

    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 2000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [documentBulkJobId]);

  const handleDocumentBulkPreview = async (
    request: DocumentBulkImportPreviewRequest,
  ) => {
    try {
      setIsDocumentBulkPreviewing(true);
      setDocumentBulkErrorMessage("");
      const response = await previewDocumentBulkImport(request);
      setDocumentBulkPreview({
        jobId: response.jobId,
        status: response.status,
        progress: response.progress,
        currentStep: response.currentStep,
        errorMessage: null,
        uploadMode: request.mode,
        summary: null,
        rows: [],
      });
      setDocumentBulkJobId(response.jobId);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "문서 일괄등록 미리보기 생성에 실패했습니다.";
      setDocumentBulkErrorMessage(message);
    } finally {
      setIsDocumentBulkPreviewing(false);
    }
  };

  const handleConfirmDocumentBulkImport = async (selectedRowIds: string[]) => {
    if (!documentBulkPreview) {
      return;
    }
    try {
      setIsDocumentBulkImporting(true);
      setDocumentBulkErrorMessage("");
      const response = await confirmDocumentBulkImport({
        jobId: documentBulkPreview.jobId,
        selectedRowIds,
      });
      setDocumentBulkJobId(null);
      setDocumentBulkErrorMessage(
        response.errors.length > 0
          ? response.errors
              .slice(0, 3)
              .map((error) => `${error.groupKey ?? error.rowId ?? "-"}: ${error.reason}`)
              .join(" / ")
          : "",
      );
      handleBack();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "문서 일괄등록 확정 저장에 실패했습니다.";
      setDocumentBulkErrorMessage(message);
    } finally {
      setIsDocumentBulkImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="candidate"
        title={mode === "create" ? "지원자 등록" : "지원자 상세"}
        description="지원자 기본 정보, 진행 상태, 문서 업로드와 기존 문서 관리를 페이지 전환형으로 제공합니다."
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      {documentBulkErrorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {documentBulkErrorMessage}
        </div>
      ) : null}

      <CandidateDetailModal
        mode={mode}
        registrationMode={registrationMode}
        onRegistrationModeChange={(nextMode) => {
          setRegistrationMode(nextMode);
          setDocumentBulkErrorMessage("");
        }}
        documentBulkPreview={documentBulkPreview}
        isDocumentBulkPreviewing={isDocumentBulkPreviewing}
        isDocumentBulkImporting={isDocumentBulkImporting}
        detail={detail}
        form={form}
        validationErrors={validationErrors}
        pendingDocuments={pendingDocuments}
        activeDocumentActionId={activeDocumentActionId}
        isSaving={isSaving}
        isDetailLoading={isDetailLoading}
        isExtractRefreshing={isExtractRefreshing}
        statusOptions={statusOptions}
        jobPositionOptions={jobPositionOptions}
        documentTypeOptions={documentTypeOptions}
        onFieldChange={updateField}
        onSave={() => void handleSave()}
        onBack={handleBack}
        onDelete={() => void handleDelete()}
        onAddFiles={addPendingFiles}
        onPendingDocumentTypeChange={updatePendingDocumentType}
        onPendingDocumentRemove={removePendingDocument}
        onDocumentDownload={(document) => void handleDownloadDocument(document)}
        onExistingDocumentDelete={(document) =>
          void handleDeleteExistingDocument(document.id, document.originalFileName)
        }
        onExistingDocumentReplace={(document, file) =>
          void handleReplaceExistingDocument(document.id, document.documentType, file)
        }
        onOpenDocument={(document) => handleOpenDocument(document.id)}
        onDocumentBulkPreview={(request) => void handleDocumentBulkPreview(request)}
        onDocumentBulkConfirmImport={(selectedRowIds) =>
          void handleConfirmDocumentBulkImport(selectedRowIds)
        }
      />
    </div>
  );
}
