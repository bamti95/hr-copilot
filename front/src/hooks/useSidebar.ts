import { useEffect, useState } from "react";

export function useSidebar() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(
    () => window.innerWidth >= 768,
  );

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
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
  };
}
