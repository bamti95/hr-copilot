import { useMemo, useState } from "react";
import { fetchManagerList } from "../services/managerService";

export function useManagerData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchManagerList({ page, size: 5, keyword: search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
