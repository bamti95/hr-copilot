import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { KnowledgeSearchResponse } from "../types";

export function KnowledgeResultCard({
  result,
}: {
  result: KnowledgeSearchResponse["results"][number];
}) {
  const chunk = result.chunk;
  const [expanded, setExpanded] = useState(false);
  const content = chunk.content || "근거 내용이 없습니다.";
  const canToggle = content.length > 260;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-bold text-slate-950">
            {chunk.lawName || chunk.sectionTitle || "기반지식 chunk"}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {chunk.articleNo || chunk.issueCode || chunk.chunkType}
          </div>
        </div>
        <span className="rounded-full bg-[#edf4ff] px-3 py-1 text-xs font-bold text-[#315fbc]">
          {Math.round(result.hybridScore * 100)}점
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
        <span>keyword {Math.round(result.keywordScore * 100)}</span>
        <span>vector {Math.round(result.vectorScore * 100)}</span>
        <span>{result.matchedTerms.join(", ") || "matched term 없음"}</span>
      </div>
      <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-3">
        <p
          className={`whitespace-pre-wrap break-words text-xs leading-5 text-slate-600 ${
            expanded ? "" : "line-clamp-5"
          }`}
        >
          {content}
        </p>
        {canToggle ? (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="mt-3 inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 transition hover:border-[#315fbc] hover:text-[#315fbc]"
            aria-expanded={expanded}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" />
                접기
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" />
                전체 보기
              </>
            )}
          </button>
        ) : null}
      </div>
    </div>
  );
}
