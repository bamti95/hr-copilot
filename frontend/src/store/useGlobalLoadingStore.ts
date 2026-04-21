import { create } from "zustand";

interface GlobalLoadingState {
  pendingCount: number;
  isVisible: boolean;
  start: () => void;
  finish: () => void;
  reset: () => void;
}

export const useGlobalLoadingStore = create<GlobalLoadingState>((set) => ({
  pendingCount: 0,
  isVisible: false,
  start: () =>
    set((state) => {
      const pendingCount = state.pendingCount + 1;

      return {
        pendingCount,
        isVisible: pendingCount > 0,
      };
    }),
  finish: () =>
    set((state) => {
      const pendingCount = Math.max(0, state.pendingCount - 1);

      return {
        pendingCount,
        isVisible: pendingCount > 0,
      };
    }),
  reset: () =>
    set({
      pendingCount: 0,
      isVisible: false,
    }),
}));
