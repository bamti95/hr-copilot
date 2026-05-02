import type { ReactNode } from "react";
import { getArray, isRecord } from "../types/workflowDashboard.types";

interface QuestionResultPanelProps {
  finalResponse: Record<string, unknown> | null;
}

export function QuestionResultPanel({ finalResponse }: QuestionResultPanelProps) {
  const finalQuestions = getArray(finalResponse, "questions");

  return (
    <BottomPanel title="최종 질문 목록">
      {finalQuestions.length === 0 ? (
        <EmptyState text="final_formatter의 outputJson.final_response.questions가 있을 때 표시됩니다." />
      ) : (
        <div className="space-y-3">
          {finalQuestions.slice(0, 8).map((question, index) => {
            const item = isRecord(question) ? question : {};
            return (
              <article
                key={`${String(item.id ?? index)}`}
                className="rounded-lg border border-slate-200 bg-white p-3"
              >
                <div className="font-semibold text-slate-950">
                  Q{index + 1}. {String(item.question_text ?? item.questionText ?? "")}
                </div>
                <div className="mt-2 grid gap-1 text-xs text-slate-500 md:grid-cols-2">
                  <span>유형: {String(item.category ?? "-")}</span>
                  <span>점수: {String(item.score ?? "-")}</span>
                  <span className="md:col-span-2">
                    근거: {String(item.generation_basis ?? item.score_reason ?? "-")}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </BottomPanel>
  );
}

export function BottomPanel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="min-w-0 rounded-lg border border-slate-200 bg-slate-50 p-4 shadow-sm">
      <h2 className="m-0 mb-3 text-lg font-bold text-slate-950">{title}</h2>
      <div className="max-h-[360px] overflow-auto">{children}</div>
    </section>
  );
}

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
