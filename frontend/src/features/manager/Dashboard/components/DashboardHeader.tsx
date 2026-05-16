import { RefreshCw } from "lucide-react";

export function DashboardHeader({
  onRefresh,
  isLoading,
}: {
  onRefresh: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
      <div>
        <h2 className="m-0 text-lg font-bold text-slate-950">
          오늘의 채용 준비 현황
        </h2>
        <p className="m-0 mt-1 text-sm leading-5 text-slate-500">
          지원자 처리, 면접 질문 준비, 채용공고 RAG 분석과 AI 비용을 한 화면에서 확인합니다.
        </p>
      </div>
      <button
        type="button"
        onClick={onRefresh}
        disabled={isLoading}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 transition hover:border-[#315fbc] hover:text-[#315fbc] disabled:cursor-wait disabled:opacity-60"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
        새로고침
      </button>
    </div>
  );
}
