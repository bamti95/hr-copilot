// src/components/auth_prac/SignupPage.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await api.post("/auth/signup", { email, password });
      alert("회원가입 성공!");
      navigate("/auth/login");
    } catch (err) {
      setError(err.response?.data?.detail || "회원가입 실패");
    }
  };

  return (
<div className="flex items-center justify-center min-h-[85vh] px-4 py-12">
      {/* 카드 컨테이너 */}
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-[2.5rem] shadow-2xl border border-slate-100 dark:border-slate-800 p-10 transition-all">
        
        {/* 헤더 섹션 */}
        <div className="mb-10 text-left">
          <button 
            onClick={() => navigate(-1)} 
            className="mb-6 text-slate-400 hover:text-blue-600 transition-colors text-sm flex items-center gap-1"
          >
            ← 돌아가기
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 이메일 입력 섹션 */}
          <div className="group space-y-2">
            <label className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider ml-1">
              이메일 계정
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
              className="w-full px-6 py-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-300"
              required
            />
          </div>

          {/* 비밀번호 입력 섹션 */}
          <div className="group space-y-2">
            <label className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider ml-1">
              비밀번호 설정
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-6 py-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-300"
              required
            />
          </div>

          {/* 에러 메시지 알림 */}
          {error && (
            <div className="flex items-center gap-2 text-red-500 text-xs font-medium bg-red-50 dark:bg-red-900/10 p-4 rounded-xl border border-red-100 dark:border-red-900/20">
              <span className="shrink-0">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* 가입 완료 버튼 */}
          <button
            type="submit"
            className="w-full py-5 bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-2xl shadow-xl shadow-blue-200 dark:shadow-none transition-all active:scale-[0.97] mt-2 transform"
          >
            가입 완료하기
          </button>
        </form>

        {/* 하단 안내 */}
        <p className="mt-10 text-center text-sm text-slate-400">
          이미 계정이 있으신가요?{" "}
          <button 
            onClick={() => navigate("/auth/login")}
            className="text-blue-600 font-bold hover:text-blue-700 underline underline-offset-4 decoration-2"
          >
            로그인하기
          </button>
        </p>
      </div>
    </div>
  );
};

export default SignupPage;