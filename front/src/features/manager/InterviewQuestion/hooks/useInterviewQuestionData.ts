import { useMemo, useState } from "react";
import { fetchInterviewQuestionList } from "../services/interviewQuestionService";

export function useInterviewQuestionData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchInterviewQuestionList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
