import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { useThemeStore } from "../../store/useThemeStore";

interface ManagerHeaderProps {
  onToggleSidebar: () => void;
}

const ghostButtonClassName =
  "rounded-2xl border border-[var(--line)] bg-white px-4 py-3 text-sm font-medium text-[var(--text)] transition-colors hover:bg-slate-50 dark:bg-[rgba(14,21,33,0.92)] dark:text-white";

export function ManagerHeader({ onToggleSidebar }: ManagerHeaderProps) {
  const navigate = useNavigate();
  const manager = useAuthStore((state) => state.manager);
  const logout = useAuthStore((state) => state.logout);
  const isDark = useThemeStore((state) => state.isDark);
  const toggleDark = useThemeStore((state) => state.toggleDark);

  const displayName = manager?.name || manager?.loginId || manager?.email || "Manager";

  const handleLogout = async () => {
    await logout();
    navigate("/auth/login");
  };

  return (
    <header className="mb-5 flex flex-col gap-4 rounded-3xl border border-white/55 px-[18px] py-4 backdrop-blur-[18px] md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="flex h-12 w-12 flex-col justify-center gap-1 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-0 text-slate-700 shadow-sm transition-colors hover:bg-slate-100 dark:bg-[rgba(14,21,33,0.92)] dark:text-white dark:hover:bg-[rgba(20,29,45,0.96)]"
          onClick={onToggleSidebar}
          aria-label="사이드바 열기 또는 닫기"
        >
          <span className="mx-auto h-0.5 w-[18px] rounded-full bg-slate-700 dark:bg-white" />
          <span className="mx-auto h-0.5 w-[18px] rounded-full bg-slate-700 dark:bg-white" />
          <span className="mx-auto h-0.5 w-[18px] rounded-full bg-slate-700 dark:bg-white" />
        </button>
        <div>
          <p className="m-0 text-[0.78rem] uppercase tracking-[0.12em] text-[var(--muted)]">
            Manager Console
          </p>
          <h1 className="m-0 text-[clamp(1.5rem,2.4vw,2rem)] font-bold text-[var(--text)]">
            HR Copilot Manager
          </h1>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex min-h-12 min-w-[88px] items-center justify-center rounded-full bg-[#246bff1f] px-3.5 py-3 text-sm font-bold text-[var(--text)]">
          {manager?.roleType}
        </span>
        <span className="inline-flex min-h-12 min-w-[88px] items-center justify-center rounded-full bg-[#246bff1f] px-3.5 py-3 text-sm font-bold text-[var(--text)]">
          {displayName}
        </span>
        <button type="button" className={ghostButtonClassName} onClick={toggleDark}>
          {isDark ? "라이트 모드" : "다크 모드"}
        </button>
        <button type="button" className={ghostButtonClassName} onClick={handleLogout}>
          로그아웃
        </button>
      </div>
    </header>
  );
}
