import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { useThemeStore } from "../../store/useThemeStore";

interface AdminHeaderProps {
  toggleSidebar: () => void;
}

export function AdminHeader({ toggleSidebar }: AdminHeaderProps) {
  const navigate = useNavigate();
  const admin = useAuthStore((state) => state.admin);
  const logout = useAuthStore((state) => state.logout);
  const isDark = useThemeStore((state) => state.isDark);
  const toggleDark = useThemeStore((state) => state.toggleDark);

  const displayName = admin?.name || admin?.loginId || admin?.email || "관리자";

  const handleLogout = async () => {
    await logout();
    navigate("/admin/login");
  };

  return (
    <header className="admin-header">
      <div className="admin-header__left">
        <button
          type="button"
          className="sidebar-toggle"
          onClick={toggleSidebar}
          aria-label="사이드바 열기 또는 닫기"
        >
          <span />
          <span />
          <span />
        </button>
        <div>
          <p className="eyebrow">Admin Console</p>
          <h1>HR Copilot 관리자</h1>
        </div>
      </div>

      <div className="admin-header__right">
        <span className="admin-user-chip">{displayName}</span>
        <button type="button" className="ghost-button" onClick={toggleDark}>
          {isDark ? "라이트 모드" : "다크 모드"}
        </button>
        <button type="button" className="ghost-button">
          접근 로그 내보내기
        </button>
        <button type="button" className="ghost-button" onClick={handleLogout}>
          로그아웃
        </button>
        <button type="button" className="button-primary">
          신규 관리자 등록
        </button>
      </div>
    </header>
  );
}
