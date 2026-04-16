import { create } from "zustand";
import type { Admin } from "../types/Admin/Admin";
import type { LoginRequest } from "../types/Auth";
import { authStorage } from "../services/authStorage";
import {
  fetchAdminMe,
  loginAdmin,
  logoutAdmin,
  refreshAdminToken,
} from "../services/authService";
import type { AdminGroupMenuPermissionResponse } from "../types/admin";

function toStringValue(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : undefined;
}

function toNumberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function normalizeAdmin(source: unknown): Admin | undefined {
  if (!source || typeof source !== "object") {
    return undefined;
  }

  const candidate = source as Record<string, unknown>;
  const id = toNumberValue(candidate.id ?? candidate.adminId);
  const groupId = toNumberValue(candidate.groupId ?? candidate.group_id);
  const loginId = toStringValue(candidate.loginId ?? candidate.login_id);
  const name = toStringValue(candidate.name) ?? loginId;
  const email = toStringValue(candidate.email) ?? "";

  if (!id || !groupId || !name) {
    return undefined;
  }

  return {
    id,
    loginId,
    name,
    email,
    groupId,
    isDeleted:
      candidate.isDeleted === true ||
      candidate.delTf === "Y" ||
      candidate.del_tf === "Y",
  };
}

function normalizePermissions(source: unknown): AdminGroupMenuPermissionResponse[] {
  if (!Array.isArray(source)) {
    return [];
  }

  return source
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      id: typeof item.id === "number" ? item.id : undefined,
      menuId: Number(item.menuId ?? item.menu_id ?? 0),
      menuName: toStringValue(item.menuName ?? item.menu_name),
      menuKey: toStringValue(item.menuKey ?? item.menu_key),
      menuPath: toStringValue(item.menuPath ?? item.menu_path) ?? null,
      parentId: typeof item.parentId === "number" ? item.parentId : null,
      depth: typeof item.depth === "number" ? item.depth : undefined,
      sortNo: typeof item.sortNo === "number" ? item.sortNo : undefined,
      icon: toStringValue(item.icon) ?? null,
      readTf: item.readTf === "Y" ? "Y" : "N",
      writeTf: item.writeTf === "Y" ? "Y" : "N",
      deleteTf: item.deleteTf === "Y" ? "Y" : "N",
      useTf: item.useTf === "N" ? "N" : "Y",
    }))
    .filter((item) => item.menuId > 0);
}

const persistedAccessToken = authStorage.getAccessToken() ?? undefined;
const persistedRefreshToken = authStorage.getRefreshToken() ?? undefined;
const persistedAdmin = normalizeAdmin(authStorage.getAdmin<unknown>()) ?? undefined;
const persistedPermissions = normalizePermissions(authStorage.getPermissions());

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken?: string;
  refreshToken?: string;
  admin?: Admin;
  permissions: AdminGroupMenuPermissionResponse[];
  login: (requestBody: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: Boolean(persistedAccessToken || persistedRefreshToken),
  isLoading: true,
  accessToken: persistedAccessToken,
  refreshToken: persistedRefreshToken,
  admin: persistedAdmin,
  permissions: persistedPermissions,

  login: async (requestBody) => {
    const response = await loginAdmin(requestBody);
    const admin = normalizeAdmin(response.admin);
    const permissions = normalizePermissions(response.permissions);

    authStorage.setAccessToken(response.accessToken);
    authStorage.setRefreshToken(response.refreshToken);
    if (admin) {
      authStorage.setAdmin(admin);
    }
    authStorage.setPermissions(permissions);

    set({
      isAuthenticated: true,
      isLoading: false,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      admin,
      permissions,
    });
  },

  logout: async () => {
    const refreshToken = authStorage.getRefreshToken();

    try {
      await logoutAdmin(refreshToken ? { refreshToken } : undefined);
    } catch (error) {
      console.error("서버 로그아웃 실패:", error);
    } finally {
      authStorage.clear();

      set({
        isAuthenticated: false,
        isLoading: false,
        accessToken: undefined,
        refreshToken: undefined,
        admin: undefined,
        permissions: [],
      });
    }
  },

  clearAuth: () => {
    authStorage.clear();

    set({
      isAuthenticated: false,
      isLoading: false,
      accessToken: undefined,
      refreshToken: undefined,
      admin: undefined,
      permissions: [],
    });
  },

  checkSession: async () => {
    const accessToken = authStorage.getAccessToken();
    const refreshToken = authStorage.getRefreshToken();

    if (!accessToken && !refreshToken) {
      set({
        isAuthenticated: false,
        isLoading: false,
        accessToken: undefined,
        refreshToken: undefined,
        admin: undefined,
        permissions: [],
      });
      return;
    }

    try {
      let currentAccessToken = accessToken;

      if (!currentAccessToken && refreshToken) {
        const refreshed = await refreshAdminToken({ refreshToken });
        authStorage.setAccessToken(refreshed.accessToken);
        authStorage.setRefreshToken(refreshed.refreshToken);
        currentAccessToken = refreshed.accessToken;
      }

      const me = await fetchAdminMe();
      const admin = normalizeAdmin(me.admin);
      const permissions = normalizePermissions(me.permissions);

      if (!admin) {
        throw new Error("관리자 세션 정보를 복원하지 못했습니다.");
      }

      authStorage.setAdmin(admin);
      authStorage.setPermissions(permissions);

      set({
        isAuthenticated: true,
        isLoading: false,
        accessToken: currentAccessToken ?? undefined,
        refreshToken: authStorage.getRefreshToken() ?? undefined,
        admin,
        permissions,
      });
    } catch (error) {
      console.error("세션 체크 실패:", error);
      authStorage.clear();

      set({
        isAuthenticated: false,
        isLoading: false,
        accessToken: undefined,
        refreshToken: undefined,
        admin: undefined,
        permissions: [],
      });
    }
  },
}));
