import api from "./api";
import type {
  LoginRequest,
  LogoutRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  TokenPairResponse,
} from "../types/Auth";

function createRefreshPayload(refreshToken: string) {
  return {
    refreshToken,
    refresh_token: refreshToken,
  };
}

export async function loginAdmin(requestBody: LoginRequest) {
  const response = await api.post<TokenPairResponse>("/auth/login", requestBody, {
    skipAuthRefresh: true,
  } as never);

  return response.data;
}

export async function refreshAdminToken(requestBody: RefreshTokenRequest) {
  const response = await api.post<RefreshTokenResponse>(
    "/auth/refresh",
    createRefreshPayload(requestBody.refreshToken),
    {
      skipAuthRefresh: true,
    } as never,
  );

  return response.data;
}

export async function logoutAdmin(requestBody?: LogoutRequest) {
  await api.post(
    "/auth/logout",
    requestBody ? createRefreshPayload(requestBody.refreshToken) : undefined,
    {
      skipAuthRefresh: true,
    } as never,
  );
}
