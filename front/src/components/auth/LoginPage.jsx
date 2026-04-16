// src/components/auth_prac/LoginPage.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../../store/useAuthStore";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/board/posts");
    } catch (err) {
      setError(err.response?.data?.detail || "로그인 실패");
    }
  };

   return (
    <div className="flex items-center justify-center min-h-[80vh] px-4">
      {/* 카드 컨테이너 */}
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl shadow-xl border border-slate-100 dark:border-slate-800 p-8 transition-all">

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 이메일 입력창 */}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 ml-1">
              이메일 주소
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
              className="w-full px-5 py-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-400"
              required
            />
          </div>

          {/* 비밀번호 입력창 */}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 ml-1">
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-5 py-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-400"
              required
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-500 text-xs py-2 px-4 rounded-lg border border-red-100 dark:border-red-900/30 animate-pulse">
              ⚠️ {error}
            </div>
          )}

          {/* 로그인 버튼 */}
          <button
            type="submit"
            className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-2xl shadow-lg shadow-blue-200 dark:shadow-none transition-all active:scale-[0.98] mt-4"
          >
            로그인하기
          </button>
        </form>

        {/* 푸터 링크 */}
        <div className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
          계정이 없으신가요?{" "}
          <button
            onClick={() => navigate('/auth/signup')} 
            className="text-blue-600 font-semibold hover:underline decoration-2 underline-offset-4">
            회원가입
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;