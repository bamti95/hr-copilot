import type {
  AdminAccessLog,
  AdminGroup,
  AdminGroupMenuPermission,
  AdminMenu,
  AdminUser,
} from "../../../types/admin";

export const adminGroups: AdminGroup[] = [
  { id: 1, groupName: "SUPER_ADMIN", groupDesc: "시스템 전 영역 운영 권한", useTf: "Y", adminCount: 2, updatedAt: "2026-04-11 09:00" },
  { id: 2, groupName: "HR_MANAGER", groupDesc: "채용 운영 및 평가 관리", useTf: "Y", adminCount: 4, updatedAt: "2026-04-10 16:40" },
  { id: 3, groupName: "CONTENT_EDITOR", groupDesc: "문서 및 프롬프트 관리", useTf: "Y", adminCount: 3, updatedAt: "2026-04-09 14:15" },
  { id: 4, groupName: "AUDITOR", groupDesc: "조회 전용 및 접근 로그 감사", useTf: "N", adminCount: 1, updatedAt: "2026-04-08 11:20" },
];

export const adminUsers: AdminUser[] = [
  { id: 101, loginId: "root.admin", name: "김도윤", email: "root@hrcopilot.ai", groupId: 1, groupName: "SUPER_ADMIN", status: "ACTIVE", lastLoginAt: "2026-04-11 08:55", useTf: "Y" },
  { id: 102, loginId: "hr.lead", name: "박서연", email: "syeon@hrcopilot.ai", groupId: 2, groupName: "HR_MANAGER", status: "ACTIVE", lastLoginAt: "2026-04-11 08:41", useTf: "Y" },
  { id: 103, loginId: "ops.audit", name: "최현우", email: "audit@hrcopilot.ai", groupId: 4, groupName: "AUDITOR", status: "LOCKED", lastLoginAt: "2026-04-09 18:20", useTf: "N" },
  { id: 104, loginId: "cms.editor", name: "이민지", email: "editor@hrcopilot.ai", groupId: 3, groupName: "CONTENT_EDITOR", status: "ACTIVE", lastLoginAt: "2026-04-10 12:11", useTf: "Y" },
];

export const adminMenus: AdminMenu[] = [
  { id: 1, parentId: null, menuName: "대시보드", menuKey: "dashboard", menuPath: "/admin/dashboard", depth: 1, sortNo: 1, icon: "DB", useTf: "Y" },
  { id: 2, parentId: null, menuName: "관리자 그룹", menuKey: "admin_group", menuPath: "/admin/groups", depth: 1, sortNo: 2, icon: "GR", useTf: "Y" },
  { id: 3, parentId: null, menuName: "관리자 계정", menuKey: "admin", menuPath: "/admin/accounts", depth: 1, sortNo: 3, icon: "AD", useTf: "Y" },
  { id: 4, parentId: null, menuName: "메뉴 관리", menuKey: "adm_menu", menuPath: "/admin/menus", depth: 1, sortNo: 4, icon: "MN", useTf: "Y" },
  { id: 5, parentId: null, menuName: "권한 매핑", menuKey: "admin_group_menu", menuPath: "/admin/permissions", depth: 1, sortNo: 5, icon: "RB", useTf: "Y" },
  { id: 6, parentId: null, menuName: "접근 로그", menuKey: "admin_access_log", menuPath: "/admin/access-logs", depth: 1, sortNo: 6, icon: "LG", useTf: "Y" },
  { id: 7, parentId: 2, menuName: "그룹 상세", menuKey: "admin_group_detail", menuPath: "/admin/groups/detail", depth: 2, sortNo: 1, icon: "DT", useTf: "Y" },
  { id: 8, parentId: 3, menuName: "계정 상세", menuKey: "admin_detail", menuPath: "/admin/accounts/detail", depth: 2, sortNo: 1, icon: "DT", useTf: "Y" },
];

export const adminGroupMenuPermissions: AdminGroupMenuPermission[] = [
  { id: 1, groupId: 1, menuId: 1, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 2, groupId: 1, menuId: 2, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 3, groupId: 1, menuId: 3, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 4, groupId: 1, menuId: 4, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 5, groupId: 1, menuId: 5, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 6, groupId: 1, menuId: 6, readTf: "Y", writeTf: "Y", deleteTf: "Y", useTf: "Y" },
  { id: 7, groupId: 2, menuId: 1, readTf: "Y", writeTf: "N", deleteTf: "N", useTf: "Y" },
  { id: 8, groupId: 2, menuId: 2, readTf: "Y", writeTf: "Y", deleteTf: "N", useTf: "Y" },
  { id: 9, groupId: 2, menuId: 3, readTf: "Y", writeTf: "Y", deleteTf: "N", useTf: "Y" },
  { id: 10, groupId: 2, menuId: 6, readTf: "Y", writeTf: "N", deleteTf: "N", useTf: "Y" },
  { id: 11, groupId: 3, menuId: 1, readTf: "Y", writeTf: "N", deleteTf: "N", useTf: "Y" },
  { id: 12, groupId: 3, menuId: 4, readTf: "Y", writeTf: "Y", deleteTf: "N", useTf: "Y" },
  { id: 13, groupId: 4, menuId: 1, readTf: "Y", writeTf: "N", deleteTf: "N", useTf: "Y" },
  { id: 14, groupId: 4, menuId: 6, readTf: "Y", writeTf: "N", deleteTf: "N", useTf: "Y" },
];

export const adminAccessLogs: AdminAccessLog[] = [
  { id: 1001, adminId: 101, adminName: "김도윤", actionType: "LOGIN", actionTarget: "admin", targetId: "101", ipAddress: "10.0.0.12", resultTf: "Y", createdAt: "2026-04-11 08:55", message: "관리자 로그인 성공" },
  { id: 1002, adminId: 102, adminName: "박서연", actionType: "UPDATE", actionTarget: "admin_group", targetId: "2", ipAddress: "10.0.0.24", resultTf: "Y", createdAt: "2026-04-11 09:14", message: "HR_MANAGER 그룹 설명 수정" },
  { id: 1003, adminId: 104, adminName: "이민지", actionType: "CREATE", actionTarget: "adm_menu", targetId: "8", ipAddress: "10.0.0.36", resultTf: "Y", createdAt: "2026-04-11 09:42", message: "신규 하위 메뉴 생성" },
  { id: 1004, adminId: 103, adminName: "최현우", actionType: "LOGIN", actionTarget: "admin", targetId: "103", ipAddress: "10.0.0.48", resultTf: "N", createdAt: "2026-04-10 18:20", message: "잠금 계정 로그인 실패" },
  { id: 1005, adminId: 101, adminName: "김도윤", actionType: "EXPORT", actionTarget: "admin_access_log", targetId: "2026-04-10", ipAddress: "10.0.0.12", resultTf: "Y", createdAt: "2026-04-10 17:05", message: "감사 로그 CSV 내보내기" },
  { id: 1006, adminId: 102, adminName: "박서연", actionType: "DELETE", actionTarget: "admin_group_menu", targetId: "14", ipAddress: "10.0.0.24", resultTf: "Y", createdAt: "2026-04-10 13:10", message: "AUDITOR 쓰기 권한 제거" },
];
