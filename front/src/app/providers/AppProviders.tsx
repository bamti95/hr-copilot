import { useEffect, type PropsWithChildren } from "react";
import { useAuthStore } from "../../store/useAuthStore";
import { useThemeStore } from "../../store/useThemeStore";

export function AppProviders({ children }: PropsWithChildren) {
  const checkSession = useAuthStore((state) => state.checkSession);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const isDark = useThemeStore((state) => state.isDark);
  const initializeTheme = useThemeStore((state) => state.initializeTheme);

  useEffect(() => {
    initializeTheme();
    void checkSession();
  }, [checkSession, initializeTheme]);

  useEffect(() => {
    document.documentElement.classList.toggle("theme-dark", isDark);
    document.body.classList.toggle("theme-dark", isDark);
  }, [isDark]);

  useEffect(() => {
    const handleUnauthorized = () => clearAuth();

    window.addEventListener("auth:unauthorized", handleUnauthorized);

    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, [clearAuth]);

  return children;
}
