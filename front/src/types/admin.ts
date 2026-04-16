export interface AdminGroupMenuPermissionRequest {
  menuId: number;
  readTf: "Y" | "N";
  writeTf: "Y" | "N";
  deleteTf: "Y" | "N";
  useTf: "Y" | "N";
}

export interface AdminGroupMenuPermissionResponse {
  id?: number;
  menuId: number;
  menuName?: string;
  menuKey?: string;
  menuPath?: string | null;
  parentId?: number | null;
  depth?: number;
  sortNo?: number;
  icon?: string | null;
  readTf: "Y" | "N";
  writeTf: "Y" | "N";
  deleteTf: "Y" | "N";
  useTf: "Y" | "N";
}

export interface AdminGroupRequest {
  groupName: string;
  groupDesc?: string | null;
  useTf: "Y" | "N";
  menuPermissions: AdminGroupMenuPermissionRequest[];
}

export interface AdminGroupResponse {
  id: number;
  groupName: string;
  groupDesc?: string | null;
  useTf: "Y" | "N";
  delTf?: "Y" | "N";
  regAdm?: string | null;
  regDate: string;
  upAdm?: string | null;
  upDate?: string | null;
  delAdm?: string | null;
  delDate?: string | null;
  menuPermissions: AdminGroupMenuPermissionResponse[];
}

export interface AdminGroupListResponse {
  items: AdminGroupResponse[];
  totalCount: number;
  totalPages: number;
}

export interface AdminRequest {
  groupId: number;
  loginId: string;
  password?: string;
  name: string;
  email?: string | null;
  status?: "ACTIVE" | "LOCKED" | "INACTIVE";
  useTf?: "Y" | "N";
  delTf?: "Y" | "N";
}

export interface AdminResponse {
  id: number;
  groupId: number;
  loginId: string;
  name: string;
  email?: string | null;
  status: "ACTIVE" | "LOCKED" | "INACTIVE";
  lastLoginAt?: string | null;
  useTf?: "Y" | "N";
  delTf?: "Y" | "N";
  regAdm?: string | null;
  regDate: string;
  upAdm?: string | null;
  upDate?: string | null;
  delAdm?: string | null;
  delDate?: string | null;
}

export interface AdminListResponse {
  items: AdminResponse[];
  totalCount: number;
  totalPages: number;
}

export interface AdminMenuRequest {
  parentId?: number | null;
  menuName: string;
  menuKey: string;
  menuPath?: string | null;
  depth?: number;
  sortNo: number;
  icon?: string | null;
  useTf?: "Y" | "N";
  delTf?: "Y" | "N";
}

export interface AdminMenu {
  id: number;
  parentId: number | null;
  menuName: string;
  menuKey: string;
  menuPath: string | null;
  depth: number;
  sortNo: number;
  icon: string | null;
  useTf: "Y" | "N";
  delTf?: "Y" | "N";
  regAdm?: string | null;
  regDate?: string;
  upAdm?: string | null;
  upDate?: string | null;
  delAdm?: string | null;
  delDate?: string | null;
}

export interface AdminMenuListResponse {
  items: AdminMenu[];
  totalCount: number;
  totalPages: number;
}

export interface AdminMenuTreeResponse extends AdminMenu {
  children: AdminMenuTreeResponse[];
}

export interface AdminAccessLog {
  id: number;
  adminId: number;
  adminName: string;
  actionType: "LOGIN" | "LOGOUT" | "CREATE" | "UPDATE" | "DELETE" | "EXPORT";
  actionTarget: string;
  targetId: string;
  ipAddress: string;
  resultTf: "Y" | "N";
  createdAt: string;
  message: string;
}
