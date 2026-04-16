import { useMemo, useState } from "react";
import { fetchInterviewSessionList } from "../services/interviewSessionService";

export function useInterviewSessionData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchInterviewSessionList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
