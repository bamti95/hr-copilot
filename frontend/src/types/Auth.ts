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

export interface ManagerProfile {
  id: number;
  loginId?: string;
  name: string;
  email: string;
  roleType?: string | null;
  status?: string;
  isDeleted: boolean;
}

export interface TokenPairResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  manager: ManagerProfile;
}

export interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}
