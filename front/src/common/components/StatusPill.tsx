interface StatusPillProps {
  status: string;
}

const toneByStatus: Record<string, string> = {
  ACTIVE: "is-positive",
  ENABLED: "is-positive",
  COMPLETED: "is-positive",
  SUCCESS: "is-positive",
  INACTIVE: "is-danger",
  FAILED: "is-danger",
  ERROR: "is-danger",
  PROCESSING: "is-warning",
  PENDING: "is-warning",
  REVIEW: "is-warning",
};

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span className={`status-pill ${toneByStatus[status] ?? "is-neutral"}`}>
      {status}
    </span>
  );
}
