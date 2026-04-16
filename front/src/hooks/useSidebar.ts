import { useEffect, useState } from "react";

export function useSidebar() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth >= 1024 : false,
  );

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsSidebarOpen(true);
      }
    };

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return {
    isSidebarOpen,
    toggleSidebar: () => setIsSidebarOpen((current) => !current),
    closeSidebar: () => setIsSidebarOpen(false),
    openSidebar: () => setIsSidebarOpen(true),
  };
}
