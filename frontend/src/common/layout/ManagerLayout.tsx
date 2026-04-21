import { Outlet } from "react-router-dom";
import { useSidebar } from "../../hooks/useSidebar";
import { ManagerHeader } from "./ManagerHeader";
import { ManagerSidebar } from "./ManagerSidebar";

export function ManagerLayout() {
  const { isSidebarOpen, toggleSidebar, closeSidebar } = useSidebar();

  return (
    <div className="flex min-h-screen">
      <ManagerSidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      <div className="min-w-0 flex-1 p-3 md:p-6">
        <ManagerHeader onToggleSidebar={toggleSidebar} />
        <main className="flex flex-col gap-3 md:gap-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
