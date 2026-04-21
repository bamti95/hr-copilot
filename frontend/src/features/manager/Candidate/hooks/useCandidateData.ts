import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { deleteCandidate, fetchCandidateList } from "../services/candidateService";
import type {
  CandidateApplyStatus,
  CandidateListResponse,
} from "../types";

export function useCandidateData() {
  const navigate = useNavigate();
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
  const [errorMessage, setErrorMessage] = useState("");

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

  const handleSearchSubmit = () => {
    setPage(1);
    setSearchKeyword(searchInput.trim());
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

  return {
    data,
    searchInput,
    statusFilter,
    pageSize,
    isLoading,
    errorMessage,
    setSearchInput,
    setStatusFilter,
    setPage,
    setPageSize,
    handleSearchSubmit,
    handleOpenCreate,
    handleOpenDetail,
    handleDelete,
  };
}
