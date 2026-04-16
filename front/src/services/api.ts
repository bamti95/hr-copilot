import axios from "axios";
import { authStorage } from "./authStorage";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = authStorage.getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
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
  (response) => response,
  async (error) => {
    const originalRequest = error.config as any;

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
