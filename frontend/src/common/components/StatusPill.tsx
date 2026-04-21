interface StatusPillProps {
  status: string;
}

const toneByStatus: Record<string, string> = {
  ACTIVE: "positive",
  ENABLED: "positive",
  COMPLETED: "positive",
  SUCCESS: "positive",
  INACTIVE: "danger",
  FAILED: "danger",
  ERROR: "danger",
  PROCESSING: "warning",
  PENDING: "warning",
  REVIEW: "warning",
};

const toneClassNameByStatus: Record<string, string> = {
  positive: "bg-[rgba(20,184,111,0.14)] text-[var(--success)]",
  warning: "bg-[rgba(227,164,37,0.14)] text-[#8b6011]",
  danger: "bg-[rgba(255,93,93,0.14)] text-[#cb3b3b]",
  neutral: "bg-[rgba(100,118,150,0.12)] text-[#4f607d]",
};

export function StatusPill({ status }: StatusPillProps) {
  const tone = toneByStatus[status] ?? "neutral";

  return (
    <span
      className={`inline-flex min-w-[88px] items-center justify-center rounded-full px-3 py-2 text-[0.78rem] font-bold ${toneClassNameByStatus[tone]}`}
    >
      {status}
    </span>
  );
}
