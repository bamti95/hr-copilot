import { useMemo, useState } from "react";
import { fetchPromptProfileList } from "../services/promptProfileService";

export function usePromptProfileData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchPromptProfileList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
