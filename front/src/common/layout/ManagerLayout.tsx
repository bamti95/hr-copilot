import { Outlet } from "react-router-dom";
import { useSidebar } from "../../hooks/useSidebar";
import { ManagerHeader } from "./ManagerHeader";
import { ManagerSidebar } from "./ManagerSidebar";

export function ManagerLayout() {
  const { isSidebarOpen, toggleSidebar, closeSidebar } = useSidebar();

  return (
    <div className={`admin-shell ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <ManagerSidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      <div className="admin-shell__content">
        <ManagerHeader onToggleSidebar={toggleSidebar} />
        <main className="admin-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
