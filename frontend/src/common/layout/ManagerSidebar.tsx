import { NavLink, useLocation } from "react-router-dom";
import { X, ChevronRight } from "lucide-react";
import { useAuthStore } from "../../store/useAuthStore";
import { managerNavItems } from "../data/managerConsoleData";

interface ManagerSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ManagerSidebar({ isOpen, onClose }: ManagerSidebarProps) {
  const manager = useAuthStore((state) => state.manager);
  const location = useLocation();

  return (
    <>
      <aside
        className={[
          "fixed left-0 top-0 z-40 flex h-screen flex-col overflow-hidden",
          "border-r border-white/10 bg-linear-to-b from-[#1f2633] via-[#1c2330] to-[#161d29] text-[#f5f7fb]",
          "shadow-[0_24px_60px_rgba(8,15,30,0.36)] transition-all duration-300 ease-out",
          "lg:sticky lg:top-0 lg:h-screen",
          isOpen
            ? "w-73 translate-x-0 opacity-100 lg:w-73 lg:min-w-73"
            : "-translate-x-full opacity-0 lg:w-0 lg:min-w-0 lg:translate-x-0 lg:opacity-0 lg:border-r-0 lg:shadow-none",
        ].join(" ")}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 pb-5 pt-5">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-linear-to-br from-white via-[#d9e7ff] to-[#8ab2ff] text-base font-extrabold text-[#192232] shadow-[0_8px_24px_rgba(137,173,255,0.24)]">
              HR
            </div>
            <div>
              <p className="m-0 text-[1.05rem] font-bold text-white">HR Copilot</p>
              <span className="text-[0.75rem] uppercase tracking-[0.14em] text-white/50">
                Manager Workspace
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/6 text-white/75 transition-all hover:bg-white/12 hover:text-white lg:hidden"
            aria-label="사이드바 닫기"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-5">
          <div>
            <p className="mb-3 px-2 text-[0.75rem] uppercase tracking-[0.14em] text-white/40">
              Manager Menu
            </p>

            <nav className="flex flex-col gap-2">
              {managerNavItems.map((item) => {
                const isActive = location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={[
                      "group flex items-center justify-between rounded-2xl border px-4 py-3.5 text-sm font-semibold transition-all duration-200",
                      isActive
                        ? "border-[#4f7fff66] bg-linear-to-r from-[#2f4fa8]/60 to-[#2a3f75]/60 text-white shadow-[0_10px_30px_rgba(47,79,168,0.24)]"
                        : "border-white/8 bg-white/4 text-white/82 hover:border-white/16 hover:bg-white/8 hover:text-white",
                    ].join(" ")}
                    onClick={() => {
                      if (window.innerWidth < 1024) {
                        onClose();
                      }
                    }}
                  >
                    <span>{item.label}</span>
                    <ChevronRight
                      className={`h-4 w-4 transition-transform ${
                        isActive
                          ? "translate-x-0 text-white/90"
                          : "text-white/30 group-hover:translate-x-0.5 group-hover:text-white/60"
                      }`}
                    />
                  </NavLink>
                );
              })}
              <NavLink
                to="/manager/llm-usage"
                className={[
                  "group flex items-center justify-between rounded-2xl border px-4 py-3.5 text-sm font-semibold transition-all duration-200",
                  location.pathname === "/manager/llm-usage"
                    ? "border-[#4f7fff66] bg-linear-to-r from-[#2f4fa8]/60 to-[#2a3f75]/60 text-white shadow-[0_10px_30px_rgba(47,79,168,0.24)]"
                    : "border-white/8 bg-white/4 text-white/82 hover:border-white/16 hover:bg-white/8 hover:text-white",
                ].join(" ")}
                onClick={() => {
                  if (window.innerWidth < 1024) {
                    onClose();
                  }
                }}
              >
                <span>LLM 사용량</span>
                <ChevronRight
                  className={`h-4 w-4 transition-transform ${
                    location.pathname === "/manager/llm-usage"
                      ? "translate-x-0 text-white/90"
                      : "text-white/30 group-hover:translate-x-0.5 group-hover:text-white/60"
                  }`}
                />
              </NavLink>
            </nav>
          </div>
        </div>

        <div className="border-t border-white/10 p-4">
          <p className="mb-3 px-1 text-[0.75rem] uppercase tracking-[0.14em] text-white/40">
            Manager Info
          </p>

          <div className="rounded-[20px] border border-white/10 bg-white/6 p-4 shadow-inner">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-linear-to-br from-[#3e6fff] to-[#6aa6ff] text-sm font-bold text-white">
                {(manager?.name ?? manager?.loginId ?? "M").slice(0, 1).toUpperCase()}
              </div>

              <div className="min-w-0">
                <strong className="block truncate text-sm text-white">
                  {manager?.name ?? "운영 매니저"}
                </strong>
                <span className="block truncate text-xs text-white/60">
                  {manager?.email ?? "manager@hrcopilot.ai"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {isOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-[#020817]/55 backdrop-blur-[2px] lg:hidden"
          onClick={onClose}
          aria-label="사이드바 배경 닫기"
        />
      ) : null}
    </>
  );
}
