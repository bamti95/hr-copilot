import { useMemo, useState } from "react";
import { fetchOpsLogList } from "../services/opsLogService";

export function useOpsLogData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchOpsLogList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
