import { useGlobalLoadingStore } from "../../store/useGlobalLoadingStore";

export function GlobalLoadingOverlay() {
  const isVisible = useGlobalLoadingStore((state) => state.isVisible);

  if (!isVisible) {
    return null;
  }

  return (
    <div className="pointer-events-auto fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/18 backdrop-blur-[3px]">
      <div className="flex min-w-[220px] flex-col items-center gap-4 rounded-[28px] border border-white/70 bg-[var(--panel)] px-8 py-7 text-center shadow-[var(--shadow)]">
        <div className="global-loading-spinner" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--primary)]">
            Loading
          </p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            데이터를 불러오는 중입니다.
          </p>
        </div>
      </div>
    </div>
  );
}
