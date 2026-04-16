import {
  adminAccessLogs,
  adminGroupMenuPermissions,
  adminGroups,
  adminMenus,
  adminUsers,
} from "../features/admin/data/adminMockData";

export const adminService = {
  getAdminGroups: () => adminGroups,
  getAdminUsers: () => adminUsers,
  getAdminMenus: () => adminMenus,
  getAdminGroupMenuPermissions: () => adminGroupMenuPermissions,
  getAdminAccessLogs: () => adminAccessLogs,
};
