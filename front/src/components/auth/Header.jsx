import { Link, useLocation } from "react-router-dom";
import useAuthStore from "../../store/useAuthStore";

const Header = () => {
  const { user, logout } = useAuthStore();
  const location = useLocation(); // 현재 경로 가져오기

  // 현재 경로와 일치하는지 확인하는 함수
  const isActive = (path) => location.pathname === path;

  // 메뉴 아이템 스타일 (재사용)
  const navItemStyle = (path) => `
    relative text-sm font-bold transition-all duration-300 px-1 py-2
    ${isActive(path) 
      ? "text-blue-600 dark:text-blue-400" 
      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"}
  `;

  return (
    <header className="sticky top-0 z-50 w-full bg-white/80 dark:bg-slate-600/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        
        {/* 왼쪽: 로고 및 네비게이션 */}
        <div className="flex items-center gap-10">
          <Link 
            to="/" 
            className="text-xl font-black bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent active:scale-95 transition-transform"
          >
            MyBoard
          </Link>
          
          <nav className="flex items-center gap-8">
            <Link to="/chat/stream" className={navItemStyle("/")}>
              챗 테스트
              {isActive("/chat/stream") && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full animate-in fade-in slide-in-from-bottom-1" />
              )}
            </Link>

            <Link to="/chat/stream-history" className={navItemStyle("/")}>
              챗 기록 테스트
              {isActive("/chat/stream-history") && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full animate-in fade-in slide-in-from-bottom-1" />
              )}
            </Link>

            <Link to="/chat/ai" className={navItemStyle("/")}>
              OpenAI 챗 테스트
              {isActive("/chat/ai") && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full animate-in fade-in slide-in-from-bottom-1" />
              )}
            </Link>
            
            <Link to="/mypage" className={navItemStyle("/auth/mypage")}>
              마이페이지
              {isActive("/mypage") && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full animate-in fade-in slide-in-from-bottom-1" />
              )}
            </Link>

            <Link to="/board/posts" className={navItemStyle("/auth/mypage")}>
              글목록
              {isActive("/board/posts") && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full animate-in fade-in slide-in-from-bottom-1" />
              )}
            </Link>
          </nav>
        </div>

        {/* 오른쪽: 사용자 정보 및 버튼 */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-5">
              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
                <span className="text-blue-500 mr-1">●</span> {user.email}님
              </span>
              <button 
                onClick={logout}
                className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-red-500 bg-slate-100 dark:bg-slate-800 hover:bg-red-50 rounded-xl transition-all"
              >
                로그아웃
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/auth/login" className={navItemStyle("/auth/login")}>
                로그인
              </Link>
              <Link 
                to="/auth/signup" 
                className="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-2xl shadow-lg shadow-blue-100 transition-all active:scale-95"
              >
                회원가입
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
