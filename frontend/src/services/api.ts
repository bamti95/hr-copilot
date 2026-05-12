import axios, { type InternalAxiosRequestConfig } from "axios";
import { authStorage } from "./authStorage";
import { useGlobalLoadingStore } from "../store/useGlobalLoadingStore";

/** 로컬 기본값. 배포 시 Vite `VITE_API_URL` — origin만 주면 `/api/v1` 자동 추가 */
function resolveApiBaseUrl(): string {
  const raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
  const root = (raw || "http://127.0.0.1:8000").replace(/\/$/, "");
  return root.endsWith("/api/v1") ? root : `${root}/api/v1`;
}

const API_BASE_URL = resolveApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const nextConfig = config as InternalAxiosRequestConfig;
  const token = authStorage.getAccessToken();

  if (token) {
    nextConfig.headers.Authorization = `Bearer ${token}`;
  }

  if (!nextConfig.skipGlobalLoading) {
    useGlobalLoadingStore.getState().start();
    nextConfig.__globalLoadingTracked = true;
  }

  return nextConfig;
});

let refreshPromise: Promise<string | null> | null = null;

async function requestTokenRefresh() {
  const refreshToken = authStorage.getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refreshToken,
      refresh_token: refreshToken,
    });

    const nextAccessToken = response.data.accessToken as string;
    const nextRefreshToken = (response.data.refreshToken as string) ?? refreshToken;

    authStorage.setAccessToken(nextAccessToken);
    authStorage.setRefreshToken(nextRefreshToken);

    return nextAccessToken;
  } catch (error) {
    authStorage.clear();
    window.dispatchEvent(new Event("auth:unauthorized"));
    throw error;
  }
}

api.interceptors.response.use(
  (response) => {
    const responseConfig = response.config as InternalAxiosRequestConfig;

    if (responseConfig.__globalLoadingTracked) {
      useGlobalLoadingStore.getState().finish();
      responseConfig.__globalLoadingTracked = false;
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      skipAuthRefresh?: boolean;
      _retry?: boolean;
      headers?: Record<string, string>;
    };

    if (originalRequest?.__globalLoadingTracked) {
      useGlobalLoadingStore.getState().finish();
      originalRequest.__globalLoadingTracked = false;
    }

    if (
      error.response?.status !== 401 ||
      originalRequest?.skipAuthRefresh ||
      originalRequest?._retry
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!refreshPromise) {
      refreshPromise = requestTokenRefresh().finally(() => {
        refreshPromise = null;
      });
    }

    const nextAccessToken = await refreshPromise;

    if (!nextAccessToken) {
      return Promise.reject(error);
    }

    originalRequest.headers = originalRequest.headers ?? {};
    originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;

    return api(originalRequest);
  },
);

export default api;
