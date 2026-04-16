import type { ReactNode } from "react";

interface StatusBadgeProps {
  tone?: "neutral" | "positive" | "warning" | "danger";
  children: ReactNode;
}

export function StatusBadge({ tone = "neutral", children }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>;
}
