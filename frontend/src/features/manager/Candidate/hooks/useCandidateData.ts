import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { createAnalysisSessions } from "../services/analysisSessionService";
import {
  bulkImportCandidates,
  deleteCandidate,
  fetchCandidateList,
  fetchCandidateSampleFolders,
  fetchCandidateStatistics,
} from "../services/candidateService";
import type {
  AnalysisSessionCreateRequest,
  AnalysisSessionGraphPipeline,
  CandidateApplyStatus,
  CandidateSampleFolder,
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
  const [isAnalysisSessionCreateModalOpen, setIsAnalysisSessionCreateModalOpen] =
    useState(false);
  const [isCreatingAnalysisSessions, setIsCreatingAnalysisSessions] = useState(false);
  const [sampleFolders, setSampleFolders] = useState<CandidateSampleFolder[]>([]);
  const [selectedSampleFolderName, setSelectedSampleFolderName] = useState("");
  const [isBulkImportModalOpen, setIsBulkImportModalOpen] = useState(false);
  const [isLoadingSampleFolders, setIsLoadingSampleFolders] = useState(false);
  const [isBulkImporting, setIsBulkImporting] = useState(false);

  const loadStatistics = useCallback(async () => {
    try {
      const stats = await fetchCandidateStatistics();
      setStatistics(stats);
    } catch {
      setStatistics(null);
    }
  }, []);

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
    const timer = window.setTimeout(() => setSuccessMessage(""), 4000);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  const jobQuery = jobFilter.trim() || undefined;

  const loadSampleFolders = useCallback(async () => {
    try {
      setIsLoadingSampleFolders(true);
      const folders = await fetchCandidateSampleFolders();
      setSampleFolders(folders);
      setSelectedSampleFolderName((current) => {
        if (current && folders.some((folder) => folder.folderName === current)) {
          return current;
        }
        return folders[0]?.folderName ?? "";
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "샘플 폴더 목록을 불러오지 못했습니다."));
    } finally {
      setIsLoadingSampleFolders(false);
    }
  }, []);

  const loadCandidates = useCallback(async () => {
    const response = await fetchCandidateList({
      page,
      limit: pageSize,
      search: searchKeyword || undefined,
      applyStatus: statusFilter === "ALL" ? undefined : statusFilter,
      targetJob: jobQuery,
    });
    setData(response);
  }, [jobQuery, page, pageSize, searchKeyword, statusFilter]);

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
  }, [jobQuery, page, pageSize, searchKeyword, statusFilter]);

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

  const handleOpenBulkImport = async () => {
    setErrorMessage("");
    setIsBulkImportModalOpen(true);
    await loadSampleFolders();
  };

  const handleCloseBulkImport = () => {
    if (isBulkImporting) {
      return;
    }
    setIsBulkImportModalOpen(false);
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
      setSuccessMessage("지원자를 삭제했습니다.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "지원자 삭제에 실패했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id],
    );
  };

  const selectAllOnPage = () => {
    const ids = data.items.map((row) => row.id);
    if (ids.length === 0) {
      return;
    }
    const allSelected = ids.every((id) => selectedIds.includes(id));
    setSelectedIds(allSelected ? [] : ids);
  };

  const openAnalysisSessionCreateModal = () => {
    if (!jobQuery || selectedIds.length === 0 || isLoading) {
      return;
    }
    setIsAnalysisSessionCreateModalOpen(true);
  };

  const closeAnalysisSessionCreateModal = () => {
    if (isCreatingAnalysisSessions) {
      return;
    }
    setIsAnalysisSessionCreateModalOpen(false);
  };

  const handleCreateAnalysisSessions = async (
    payload: Omit<AnalysisSessionCreateRequest, "candidateIds" | "targetJob">,
  ) => {
    if (!jobQuery || selectedIds.length === 0) {
      return;
    }
    if (payload.promptProfileId === null || payload.promptProfileId === undefined) {
      setErrorMessage("프롬프트 프로필을 선택한 뒤 분석 세션을 생성해 주세요.");
      return;
    }

    try {
      setIsCreatingAnalysisSessions(true);
      setErrorMessage("");

      const response = await createAnalysisSessions({
        candidateIds: selectedIds,
        targetJob: jobQuery,
        difficultyLevel: payload.difficultyLevel ?? null,
        promptProfileId: payload.promptProfileId,
        promptProfileSnapshot: payload.promptProfileSnapshot ?? null,
        graphPipeline: payload.graphPipeline,
      });

      setIsAnalysisSessionCreateModalOpen(false);
      setSelectedIds([]);
      const pipelineLabel: Record<AnalysisSessionGraphPipeline, string> = {
        default: "기본",
        jh: "JH",
        hy: "HY",
        jy: "JY",
      };
      setSuccessMessage(
        `${response.items.length}개의 분석 세션을 생성했습니다. (그래프: ${pipelineLabel[payload.graphPipeline]}) 실제 분석은 이후 단계에서 시작할 수 있습니다.`,
      );
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "분석 세션 생성에 실패했습니다."),
      );
    } finally {
      setIsCreatingAnalysisSessions(false);
    }
  };

  const handleBulkImport = async () => {
    if (!selectedSampleFolderName) {
      setErrorMessage("등록할 샘플 폴더를 먼저 선택해 주세요.");
      return;
    }

    try {
      setIsBulkImporting(true);
      setErrorMessage("");
      const response = await bulkImportCandidates({
        folderName: selectedSampleFolderName,
      });
      await loadCandidates();
      await loadStatistics();

      const skippedMessage =
        response.skippedCount > 0 ? `, ${response.skippedCount}명 건너뜀` : "";
      setSuccessMessage(
        `${response.folderName} 폴더에서 ${response.createdCount}명 등록 완료${skippedMessage}`,
      );

      if (response.errors.length > 0) {
        const preview = response.errors
          .slice(0, 3)
          .map((error) => `${error.candidateKey}: ${error.reason}`)
          .join(" / ");
        setErrorMessage(`일부 항목은 등록되지 않았습니다. ${preview}`);
      } else {
        setErrorMessage("");
      }

      setIsBulkImportModalOpen(false);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "단체 지원자 등록에 실패했습니다."));
    } finally {
      setIsBulkImporting(false);
    }
  };

  return {
    data,
    statistics,
    searchInput,
    statusFilter,
    jobFilter,
    page,
    pageSize,
    selectedIds,
    isLoading,
    errorMessage,
    successMessage,
    sampleFolders,
    selectedSampleFolderName,
    isBulkImportModalOpen,
    isLoadingSampleFolders,
    isBulkImporting,
    isAnalysisSessionCreateModalOpen,
    isCreatingAnalysisSessions,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    setSelectedSampleFolderName,
    handleSearchSubmit,
    handleJobFilterChange,
    handleOpenCreate,
    handleOpenBulkImport,
    handleCloseBulkImport,
    handleOpenDetail,
    handleDelete,
    toggleSelect,
    selectAllOnPage,
    loadSampleFolders,
    handleBulkImport,
    openAnalysisSessionCreateModal,
    closeAnalysisSessionCreateModal,
    createAnalysisSessions: handleCreateAnalysisSessions,
  };
}
