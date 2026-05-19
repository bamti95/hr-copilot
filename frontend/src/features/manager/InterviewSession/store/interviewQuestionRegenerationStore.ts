import { create } from "zustand";

export interface InterviewQuestionRegenerationJob {
  sessionId: number;
  targetQuestionIds: string[];
  completedAtBaseline: string | null;
  requestedAtBaseline: string | null;
  hasObservedRunning: boolean;
  baselineCaptured: boolean;
  candidateName?: string;
}

interface InterviewQuestionRegenerationState {
  jobs: Record<number, InterviewQuestionRegenerationJob>;
  startJob: (
    job: Omit<InterviewQuestionRegenerationJob, "hasObservedRunning"> & {
      hasObservedRunning?: boolean;
    },
  ) => void;
  updateJob: (
    sessionId: number,
    patch: Partial<InterviewQuestionRegenerationJob>,
  ) => void;
  completeJob: (sessionId: number) => void;
  getJob: (sessionId: number) => InterviewQuestionRegenerationJob | undefined;
  isSessionRegenerating: (sessionId: number) => boolean;
}

export const useInterviewQuestionRegenerationStore =
  create<InterviewQuestionRegenerationState>((set, get) => ({
    jobs: {},

    startJob: (job) => {
      set((state) => ({
        jobs: {
          ...state.jobs,
          [job.sessionId]: {
            ...job,
            hasObservedRunning: job.hasObservedRunning ?? false,
            baselineCaptured: job.baselineCaptured ?? false,
          },
        },
      }));
    },

    updateJob: (sessionId, patch) => {
      set((state) => {
        const current = state.jobs[sessionId];
        if (!current) {
          return state;
        }
        const next = { ...current, ...patch };
        const isUnchanged = (Object.keys(patch) as (keyof typeof patch)[]).every(
          (key) => current[key] === next[key],
        );
        if (isUnchanged) {
          return state;
        }
        return {
          jobs: {
            ...state.jobs,
            [sessionId]: next,
          },
        };
      });
    },

    completeJob: (sessionId) => {
      set((state) => {
        if (!state.jobs[sessionId]) {
          return state;
        }
        const nextJobs = { ...state.jobs };
        delete nextJobs[sessionId];
        return { jobs: nextJobs };
      });
    },

    getJob: (sessionId) => get().jobs[sessionId],

    isSessionRegenerating: (sessionId) => Boolean(get().jobs[sessionId]),
  }));
