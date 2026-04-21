import { Link, useRouteError } from "react-router-dom";

const ErrorPage = () => {
  const error = useRouteError();

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-xl rounded-[28px] border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">오류가 발생했습니다</h1>
        <p className="mt-3 text-sm text-slate-600">
          {error?.statusText || error?.message || "알 수 없는 오류입니다."}
        </p>
        <Link
          to="/admin/login"
          className="mt-6 inline-flex rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-white"
        >
          로그인 화면으로 이동
        </Link>
      </div>
    </div>
  );
};

export default ErrorPage;
