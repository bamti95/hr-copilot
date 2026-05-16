export const ROLE_LABELS: Record<string, string> = {
  SUPER_ADMIN: "최고 관리자",
  "SYSTEM-MANAGER": "시스템 관리자",
  SYSTEM_MANAGER: "시스템 관리자",
  OPS_MANAGER: "운영 관리자",
  RECRUIT_MANAGER: "채용 관리자",
  DOC_REVIEWER: "문서 검토자",
  QUALITY_MANAGER: "품질 관리자",
  PROMPT_MANAGER: "프롬프트 관리자",
  ADMIN: "관리자",
  HR_MANAGER: "인사 담당자",
  HR: "인사 담당자",
  INTERVIEWER: "면접관",
  VIEWER: "조회 전용",
};

export const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "활성",
  INACTIVE: "비활성",
  PENDING: "대기",
  SUSPENDED: "정지",
  LOCKED: "잠김",
};

export function getRoleLabel(role: string | null | undefined) {
  if (!role) return "-";
  return ROLE_LABELS[role] ?? role;
}

export function getStatusLabel(status: string | null | undefined) {
  if (!status) return "-";
  return STATUS_LABELS[status] ?? status;
}
