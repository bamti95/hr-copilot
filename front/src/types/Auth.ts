import type { Admin } from "./Admin/Admin";
import type { AdminGroupMenuPermissionResponse } from "./admin";

export interface LoginRequest {
  login_id: string;
  password: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface LogoutRequest {
  refreshToken: string;
}

export interface AuthMeResponse {
  admin: {
    id: number;
    groupId?: number;
    group_id?: number;
    loginId?: string;
    login_id?: string;
    name: string;
    email?: string | null;
    delTf?: "Y" | "N";
    del_tf?: "Y" | "N";
  };
  permissions: AdminGroupMenuPermissionResponse[];
}

export interface TokenPairResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  admin: Admin;
  permissions: AdminGroupMenuPermissionResponse[];
}

export interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}
