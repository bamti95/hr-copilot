import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";

export function ProtectedRoute() {
  const location = useLocation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-[28px] border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-600">
            Auth
          </p>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">
            세션 상태를 확인하고 있습니다.
          </h1>
          <p className="mt-3 text-sm text-slate-500">
            잠시만 기다려 주세요.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
