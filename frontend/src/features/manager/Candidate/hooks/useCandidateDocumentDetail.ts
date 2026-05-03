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
  const [isExtractRefreshing, setIsExtractRefreshing] = useState(false);
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

  useEffect(() => {
    if (!candidateId || !documentId || document?.extractStatus !== "PENDING") {
      return;
    }

    let active = true;

    const intervalId = window.setInterval(() => {
      void (async () => {
        try {
          setIsExtractRefreshing(true);
          const [candidateResponse, documentResponse] = await Promise.all([
            fetchCandidateDetail(candidateId, { skipGlobalLoading: true }),
            fetchCandidateDocumentDetail(candidateId, documentId, {
              skipGlobalLoading: true,
            }),
          ]);

          if (!active) {
            return;
          }

          setCandidate(candidateResponse);
          setDocument(documentResponse);
        } catch (error) {
          // 401: 인증 만료. axios 인터셉터의 refresh도 실패한 경우 무한 폴링을
          // 막기 위해 인터벌을 즉시 정리한다.
          const status = (error as { response?: { status?: number } })?.response?.status;
          if (status === 401) {
            active = false;
            window.clearInterval(intervalId);
            return;
          }
          // Ignore transient polling failures and preserve the last known state.
        } finally {
          if (active) {
            setIsExtractRefreshing(false);
          }
        }
      })();
    }, 2500);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [candidateId, documentId, document?.extractStatus]);

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
    isExtractRefreshing,
    errorMessage,
    handleBack,
    handleDownload,
  };
}
