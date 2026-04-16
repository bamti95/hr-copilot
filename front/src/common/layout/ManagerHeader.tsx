import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { useThemeStore } from "../../store/useThemeStore";

interface ManagerHeaderProps {
  onToggleSidebar: () => void;
}

export function ManagerHeader({ onToggleSidebar }: ManagerHeaderProps) {
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
          onClick={onToggleSidebar}
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
        <button type="button" className="ghost-button" onClick={handleLogout}>
          로그아웃
        </button>
      </div>
    </header>
  );
}
