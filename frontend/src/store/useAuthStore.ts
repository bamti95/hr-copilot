import { create } from "zustand";
import type { LoginRequest, ManagerProfile } from "../types/Auth";
import { authStorage } from "../services/authStorage";
import {
  loginAdmin,
  logoutAdmin,
  refreshAdminToken,
} from "../services/authService";

function toStringValue(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : undefined;
}

function toNumberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function normalizeManager(source: unknown): ManagerProfile | undefined {
  if (!source || typeof source !== "object") {
    return undefined;
  }

  const candidate = source as Record<string, unknown>;
  const id = toNumberValue(candidate.id);
  const loginId = toStringValue(candidate.loginId ?? candidate.login_id);
  const name = toStringValue(candidate.name) ?? loginId;
  const email = toStringValue(candidate.email) ?? "";
  const roleType = toStringValue(candidate.roleType ?? candidate.role_type) ?? null;
  const status = toStringValue(candidate.status);

  if (!id || !name) {
    return undefined;
  }

  return {
    id,
    loginId,
    name,
    email,
    roleType,
    status,
    isDeleted:
      candidate.isDeleted === true ||
      candidate.delTf === "Y" ||
      candidate.del_tf === "Y",
  };
}

const persistedAccessToken = authStorage.getAccessToken() ?? undefined;
const persistedRefreshToken = authStorage.getRefreshToken() ?? undefined;
const persistedManager = normalizeManager(authStorage.getManager<unknown>()) ?? undefined;

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken?: string;
  refreshToken?: string;
  manager?: ManagerProfile;
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
  manager: persistedManager,

  login: async (requestBody) => {
    const response = await loginAdmin(requestBody);
    const manager = normalizeManager(response.manager);

    authStorage.setAccessToken(response.accessToken);
    authStorage.setRefreshToken(response.refreshToken);
    if (manager) {
      authStorage.setManager(manager);
    }

    set({
      isAuthenticated: true,
      isLoading: false,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      manager,
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
        manager: undefined,
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
      manager: undefined,
    });
  },

  checkSession: async () => {
    const accessToken = authStorage.getAccessToken();
    const refreshToken = authStorage.getRefreshToken();
    const storedManager = normalizeManager(authStorage.getManager<unknown>());

    if (!accessToken && !refreshToken) {
      set({
        isAuthenticated: false,
        isLoading: false,
        accessToken: undefined,
        refreshToken: undefined,
        manager: undefined,
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

      if (!storedManager) {
        throw new Error("저장된 매니저 정보가 없습니다.");
      }

      set({
        isAuthenticated: true,
        isLoading: false,
        accessToken: currentAccessToken ?? undefined,
        refreshToken: authStorage.getRefreshToken() ?? undefined,
        manager: storedManager,
      });
    } catch (error) {
      console.error("세션 체크 실패:", error);
      authStorage.clear();

      set({
        isAuthenticated: false,
        isLoading: false,
        accessToken: undefined,
        refreshToken: undefined,
        manager: undefined,
      });
    }
  },
}));
