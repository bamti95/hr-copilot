import { Outlet } from "react-router-dom";
import { useSidebar } from "../../hooks/useSidebar.ts";
import { AdminHeader } from "./AdminHeader.tsx";
import { AdminSidebar } from "./AdminSidebar.tsx";

export function AdminLayout() {
  const { isSidebarOpen, toggleSidebar, closeSidebar } = useSidebar();

  return (
    <div className={`admin-shell ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <AdminSidebar
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
      />

      <div className="admin-shell__content">
        <AdminHeader toggleSidebar={toggleSidebar} />
        <main className="admin-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
