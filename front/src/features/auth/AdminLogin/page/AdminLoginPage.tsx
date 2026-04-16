import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuthStore } from "../../../../store/useAuthStore";

export function AdminLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;

  if (isAuthenticated) {
    return <Navigate to={from ?? "/admin/dashboard"} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");

    try {
      await login({
        login_id: loginId,
        password,
      });

      navigate(from ?? "/admin/dashboard", { replace: true });
    } catch (error: any) {
      setErrorMessage(
        error?.response?.data?.detail ??
          "로그인에 실패했습니다. 입력한 정보를 확인해 주세요.",
      );
    }
  };

  return (
    <div className="login-page">
      <div className="login-page__panel">
        <div className="login-page__intro">
          <p className="eyebrow">Authentication</p>
          <h1>HR Copilot 관리자 로그인</h1>
          <p>
            관리자 계정으로 로그인하면 그룹 권한에 맞는 메뉴와 기능만 접근할 수 있습니다.
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            로그인 ID
            <input
              value={loginId}
              onChange={(event) => setLoginId(event.target.value)}
              placeholder="admin01"
              autoComplete="username"
            />
          </label>

          <label>
            비밀번호
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="비밀번호를 입력하세요"
              autoComplete="current-password"
            />
          </label>

          {errorMessage ? (
            <div className="login-form__error">{errorMessage}</div>
          ) : null}

          <button
            type="submit"
            className="button-primary login-form__submit"
            disabled={isLoading}
          >
            {isLoading ? "로그인 중..." : "로그인"}
          </button>
        </form>
      </div>
    </div>
  );
}
