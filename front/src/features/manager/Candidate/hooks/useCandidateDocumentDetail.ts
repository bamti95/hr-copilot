import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import {
  downloadCandidateDocument,
  fetchCandidateDetail,
  fetchCandidateDocumentDetail,
} from "../services/candidateService";
import type {
  CandidateDetailResponse,
  CandidateDocumentDetailResponse,
} from "../types";

interface UseCandidateDocumentDetailOptions {
  candidateId?: number;
  documentId?: number;
}

export function useCandidateDocumentDetail({
  candidateId,
  documentId,
}: UseCandidateDocumentDetailOptions) {
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<CandidateDetailResponse | null>(null);
  const [document, setDocument] = useState<CandidateDocumentDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!candidateId || !documentId) {
      setErrorMessage("문서 정보를 찾을 수 없습니다.");
      setIsLoading(false);
      return;
    }

    let active = true;

    const run = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const [candidateResponse, documentResponse] = await Promise.all([
          fetchCandidateDetail(candidateId),
          fetchCandidateDocumentDetail(candidateId, documentId),
        ]);

        if (!active) {
          return;
        }

        setCandidate(candidateResponse);
        setDocument(documentResponse);
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(
          getErrorMessage(error, "문서 상세 정보를 불러오지 못했습니다."),
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
  }, [candidateId, documentId]);

  const handleBack = () => {
    if (candidateId) {
      navigate(`/manager/candidates/${candidateId}`);
      return;
    }

    navigate("/manager/candidates");
  };

  const handleDownload = async () => {
    if (!candidateId || !documentId || !document) {
      return;
    }

    try {
      await downloadCandidateDocument(
        candidateId,
        documentId,
        document.originalFileName,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "문서 다운로드에 실패했습니다."));
    }
  };

  return {
    candidate,
    document,
    isLoading,
    errorMessage,
    handleBack,
    handleDownload,
  };
}
