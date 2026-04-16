import { useMemo, useState } from "react";
import { fetchCandidateList } from "../services/candidateService";

export function useCandidateData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchCandidateList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
