import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { managerNavItems } from "../data/managerConsoleData";

interface ManagerSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ManagerSidebar({ isOpen, onClose }: ManagerSidebarProps) {
  const admin = useAuthStore((state) => state.admin);

  return (
    <>
      <aside className={`admin-sidebar ${isOpen ? "is-open" : ""}`}>
        <div className="admin-sidebar__brand">
          <div className="brand-mark">HR</div>
          <div>
            <p>HR Copilot</p>
            <span>Admin Workspace</span>
          </div>
        </div>

        <div className="admin-sidebar__section">
          <p className="admin-sidebar__label">관리 메뉴</p>
          <nav className="admin-sidebar__nav">
            {managerNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `admin-sidebar__parent ${isActive ? "is-active" : ""}`
                }
                onClick={() => {
                  if (window.innerWidth < 768) {
                    onClose();
                  }
                }}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="admin-sidebar__footer">
          <p className="admin-sidebar__label">관리자 정보</p>
          <div className="sidebar-note">
            <strong>{admin?.name ?? "운영 관리자"}</strong>
            <span>{admin?.email ?? "admin@hrcopilot.ai"}</span>
          </div>
        </div>
      </aside>

      {isOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={onClose}
          aria-label="사이드바 닫기"
        />
      ) : null}
    </>
  );
}
