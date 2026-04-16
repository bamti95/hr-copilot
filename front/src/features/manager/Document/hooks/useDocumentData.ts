import { useMemo, useState } from "react";
import { fetchDocumentList } from "../services/documentService";

export function useDocumentData() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const data = useMemo(
    () => fetchDocumentList({ page, size: 5, search }),
    [page, search],
  );

  return { data, page, setPage, search, setSearch };
}
