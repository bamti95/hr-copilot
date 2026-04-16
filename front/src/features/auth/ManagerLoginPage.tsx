import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ShieldCheck, Sparkles, LockKeyhole, User2 } from "lucide-react";
import { useAuthStore } from "../../store/useAuthStore";

const inputClassName =
  "h-12 w-full rounded-2xl border border-slate-200/80 bg-white/80 pl-11 pr-4 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10";

export default function ManagerLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const from = (location.state as { from?: { pathname?: string } } | null)?.from
    ?.pathname;

  if (isAuthenticated) {
    return <Navigate to={from ?? "/manager/managers"} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");

    try {
      await login({
        login_id: loginId,
        password,
      });

      navigate(from ?? "/manager/managers", { replace: true });
    } catch (error: any) {
      setErrorMessage(
        error?.response?.data?.detail ??
          "로그인에 실패했습니다. 입력한 아이디와 비밀번호를 다시 확인해 주세요.",
      );
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-10">
      {/* background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(20,184,166,0.18),transparent_24%),linear-gradient(135deg,#020617_0%,#0f172a_42%,#052e2b_100%)]" />
      <div className="absolute -left-16 top-10 h-72 w-72 rounded-full bg-emerald-400/20 blur-3xl" />
      <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-cyan-400/10 blur-3xl" />

      <div className="relative grid w-full max-w-6xl overflow-hidden rounded-[32px] border border-white/10 bg-white/8 shadow-[0_30px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl lg:grid-cols-[1.1fr_0.9fr]">
        {/* left branding */}
        <section className="hidden lg:flex flex-col justify-between border-r border-white/10 bg-white/6 p-10 text-white">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm font-medium text-emerald-100 backdrop-blur">
              <Sparkles className="h-4 w-4" />
              AI-Powered Interview Design Platform
            </div>

            <h1 className="mt-8 text-4xl font-semibold leading-tight">
              HR Copilot
              <br />
              <span className="bg-gradient-to-r from-emerald-300 to-teal-200 bg-clip-text text-transparent">
                Manager Console
              </span>
            </h1>

            <p className="mt-5 max-w-md text-sm leading-7 text-slate-200/80">
              채용 문서, 지원자 정보, AI 분석 결과를 기반으로 면접 질문 생성과
              관리자 운영을 한 곳에서 관리하는 콘솔입니다.
            </p>

            <div className="mt-10 space-y-4">
              <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/8 p-4">
                <div className="rounded-xl bg-emerald-400/15 p-2 text-emerald-300">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">Secure Authentication</p>
                  <p className="mt-1 text-xs leading-6 text-slate-300/75">
                    관리자 인증 후 권한 기반 메뉴와 API에 안전하게 접근합니다.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/8 p-4">
                <div className="rounded-xl bg-teal-400/15 p-2 text-teal-300">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">AI Workflow Ready</p>
                  <p className="mt-1 text-xs leading-6 text-slate-300/75">
                    문서 처리, 프롬프트 실행, 질문 생성 결과까지 통합 운영할 수
                    있습니다.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-xs leading-6 text-slate-300/80">
            Internal access only · HR Copilot Administration
          </div>
        </section>

        {/* right form */}
        <section className="flex items-center justify-center bg-white/80 px-6 py-10 backdrop-blur-xl sm:px-10">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center lg:text-left">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-[0_14px_30px_rgba(16,185,129,0.35)] lg:mx-0">
                <ShieldCheck className="h-7 w-7" />
              </div>

              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-600">
                Manager Login
              </p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                관리자 로그인
              </h2>
              <p className="mt-3 text-sm leading-6 text-slate-500">
                계정 정보를 입력하고 관리자 콘솔에 접속하세요.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Login ID
                </label>
                <div className="relative">
                  <User2 className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    className={inputClassName}
                    value={loginId}
                    onChange={(event) => setLoginId(event.target.value)}
                    placeholder="master.manager"
                    autoComplete="username"
                  />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Password
                </label>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    className={inputClassName}
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="비밀번호를 입력해 주세요"
                    autoComplete="current-password"
                  />
                </div>
              </div>

              {errorMessage ? (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-600">
                  {errorMessage}
                </div>
              ) : null}

              <button
                type="submit"
                className="group h-12 w-full rounded-2xl bg-gradient-to-r from-emerald-500 via-emerald-500 to-teal-500 text-sm font-semibold text-white shadow-[0_18px_35px_rgba(16,185,129,0.28)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_22px_40px_rgba(16,185,129,0.36)] disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isLoading}
              >
                <span className="inline-flex items-center gap-2">
                  {isLoading ? "로그인 중..." : "로그인"}
                </span>
              </button>
            </form>

            <p className="mt-6 text-center text-xs leading-6 text-slate-400 lg:text-left">
              Authorized managers only. Access is logged and monitored.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}