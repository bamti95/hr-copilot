import { FileSearch, Search, Upload } from "lucide-react";
import type {
  ChangeEvent,
  Dispatch,
  FormEvent,
  SetStateAction,
} from "react";
import type {
  KnowledgeChunk,
  KnowledgeSearchResponse,
  KnowledgeSource,
} from "../types";
import { inputClassName } from "../utils/display";
import { Field, StatusPill } from "./JobPostingFields";
import { KnowledgeResultCard } from "./KnowledgeResultCard";

interface KnowledgeUploadPanelProps {
  title: string;
  versionLabel: string;
  file: File | null;
  isUploading: boolean;
  isSeeding: boolean;
  onTitleChange: Dispatch<SetStateAction<string>>;
  onVersionLabelChange: Dispatch<SetStateAction<string>>;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
  onSeed: () => void;
}

export function KnowledgeUploadPanel({
  title,
  versionLabel,
  file,
  isUploading,
  isSeeding,
  onTitleChange,
  onVersionLabelChange,
  onFileChange,
  onUpload,
  onSeed,
}: KnowledgeUploadPanelProps) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="m-0 text-lg font-bold text-slate-950">기반지식 업로드</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            법률 PDF나 가이드 문서를 업로드하고 chunk와 embedding을 생성합니다.
          </p>
        </div>
        <button
          type="button"
          disabled={isSeeding}
          onClick={onSeed}
          className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[#315fbc]/20 bg-[#edf4ff] px-4 text-sm font-semibold text-[#315fbc] disabled:opacity-60"
        >
          <FileSearch className="h-4 w-4" />
          {isSeeding ? "적재 중..." : "source_data 적재"}
        </button>
      </div>

      <div className="mt-5 grid gap-4">
        <Field label="문서 제목">
          <input
            value={title}
            onChange={(event) => onTitleChange(event.target.value)}
            className={inputClassName}
            placeholder="미입력 시 파일명 사용"
          />
        </Field>
        <Field label="버전/출처 메모">
          <input
            value={versionLabel}
            onChange={(event) => onVersionLabelChange(event.target.value)}
            className={inputClassName}
            placeholder="예: 2023 하반기 지침"
          />
        </Field>
        <label className="flex min-h-[150px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/70 px-5 py-8 text-center transition hover:border-[#315fbc] hover:bg-[#f5f8ff]">
          <Upload className="h-8 w-8 text-[#315fbc]" />
          <strong className="mt-3 text-sm text-slate-950">
            법률 PDF 또는 가이드 문서 선택
          </strong>
          <span className="mt-2 text-xs text-slate-500">
            업로드 후 인덱싱을 실행하면 chunk와 embedding이 생성됩니다.
          </span>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt,.hwp,.xlsx,.xls,.csv"
            className="sr-only"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          />
        </label>
        {file ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
            선택 파일: <strong>{file.name}</strong>
          </div>
        ) : null}
        <button
          type="button"
          disabled={isUploading}
          onClick={onUpload}
          className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-[#315fbc] to-[#4f7fff] px-4 text-sm font-semibold text-white shadow-[0_18px_32px_rgba(49,95,188,0.22)] disabled:opacity-60"
        >
          <Upload className="h-4 w-4" />
          {isUploading ? "업로드 중..." : "기반지식 업로드"}
        </button>
      </div>
    </article>
  );
}

interface KnowledgeSearchPanelProps {
  query: string;
  searchMode: "HYBRID" | "KEYWORD" | "VECTOR";
  searchResult: KnowledgeSearchResponse | null;
  isSearching: boolean;
  onQueryChange: Dispatch<SetStateAction<string>>;
  onSearchModeChange: Dispatch<SetStateAction<"HYBRID" | "KEYWORD" | "VECTOR">>;
  onSearch: () => void;
}

export function KnowledgeSearchPanel({
  query,
  searchMode,
  searchResult,
  isSearching,
  onQueryChange,
  onSearchModeChange,
  onSearch,
}: KnowledgeSearchPanelProps) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <h2 className="m-0 text-lg font-bold text-slate-950">유사도 검색 테스트</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        분석 파이프라인에 들어가기 전 법률 chunk가 실제로 검색되는지 확인합니다.
      </p>
      <div className="mt-5 grid gap-3">
        <textarea
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          className="min-h-[96px] w-full resize-y rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-3 text-sm leading-6 outline-none focus:border-[var(--primary)]"
          placeholder="예: 개인 정보를 가족관계나 입사지원서에 기재하도록 요구"
        />
        <div className="flex flex-col gap-3 sm:flex-row">
          <select
            value={searchMode}
            onChange={(event) =>
              onSearchModeChange(event.target.value as "HYBRID" | "KEYWORD" | "VECTOR")
            }
            className={inputClassName}
          >
            <option value="HYBRID">HYBRID</option>
            <option value="KEYWORD">KEYWORD</option>
            <option value="VECTOR">VECTOR</option>
          </select>
          <button
            type="button"
            disabled={isSearching}
            onClick={onSearch}
            className="inline-flex h-11 min-w-[150px] items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:opacity-60"
          >
            <Search className="h-4 w-4" />
            {isSearching ? "검색 중..." : "검색"}
          </button>
        </div>
        {searchResult ? (
          <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-xs text-slate-500">
            {searchResult.searchMode} · {searchResult.embeddingModel} ·{" "}
            {searchResult.resultCount}개 결과
          </div>
        ) : null}
      </div>
    </article>
  );
}

interface KnowledgeSourceListProps {
  sources: KnowledgeSource[];
  selectedSourceId: number | null;
  keywordInput: string;
  isLoading: boolean;
  indexingSourceId: number | null;
  jobPolling: boolean;
  onKeywordInputChange: Dispatch<SetStateAction<string>>;
  onKeywordSubmit: (keyword: string) => void;
  onSelectSource: (sourceId: number) => void;
  onIndex: (sourceId: number) => void;
}

export function KnowledgeSourceList({
  sources,
  selectedSourceId,
  keywordInput,
  isLoading,
  indexingSourceId,
  jobPolling,
  onKeywordInputChange,
  onKeywordSubmit,
  onSelectSource,
  onIndex,
}: KnowledgeSourceListProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onKeywordSubmit(keywordInput.trim());
  };

  return (
    <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h2 className="m-0 text-lg font-bold text-slate-950">기반지식 문서</h2>
        <form className="relative md:w-72" onSubmit={handleSubmit}>
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={keywordInput}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              onKeywordInputChange(event.target.value)
            }
            className={`${inputClassName} pl-10`}
            placeholder="문서 검색"
          />
        </form>
      </div>

      <div className="mt-4 space-y-3">
        {sources.map((source) => (
          <div
            key={source.id}
            className={`rounded-2xl border bg-white p-4 transition ${
              selectedSourceId === source.id ? "border-[#315fbc]/50" : "border-slate-200"
            }`}
          >
            <button
              type="button"
              onClick={() => onSelectSource(source.id)}
              className="block w-full text-left"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-semibold text-slate-950">{source.title}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {source.sourceType} · {source.fileExt ?? "-"}
                  </div>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                  {source.chunkCount} chunks
                </span>
              </div>
            </button>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              <StatusPill label={`extract ${source.extractStatus}`} />
              <StatusPill label={`index ${source.indexStatus}`} />
              <button
                type="button"
                disabled={jobPolling || indexingSourceId === source.id}
                onClick={() => onIndex(source.id)}
                className="rounded-full border border-[#315fbc]/20 bg-[#edf4ff] px-3 py-1 font-semibold text-[#315fbc] disabled:opacity-60"
              >
                {indexingSourceId === source.id ? "인덱싱 중" : "인덱싱"}
              </button>
            </div>
          </div>
        ))}
        {!isLoading && sources.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
            기반지식 문서가 없습니다. PDF를 업로드하거나 source_data를 적재하세요.
          </div>
        ) : null}
      </div>
    </article>
  );
}

export function KnowledgeSearchResultsPanel({
  searchResult,
}: {
  searchResult: KnowledgeSearchResponse | null;
}) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <h2 className="m-0 text-lg font-bold text-slate-950">검색 결과</h2>
      <div className="mt-4 space-y-3">
        {searchResult?.results.map((result) => (
          <KnowledgeResultCard key={result.chunk.id} result={result} />
        ))}
        {searchResult && searchResult.results.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
            검색 결과가 없습니다. 먼저 문서를 인덱싱해 주세요.
          </div>
        ) : null}
      </div>
    </article>
  );
}

export function KnowledgeChunkPreviewPanel({
  selectedSourceId,
  chunks,
}: {
  selectedSourceId: number | null;
  chunks: KnowledgeChunk[];
}) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)]">
      <h2 className="m-0 text-lg font-bold text-slate-950">선택 문서 Chunk 미리보기</h2>
      <div className="mt-4 space-y-3">
        {chunks.slice(0, 6).map((chunk) => (
          <div key={chunk.id} className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-bold text-slate-950">
                  {chunk.sectionTitle || chunk.articleNo || `Chunk #${chunk.chunkIndex}`}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {chunk.chunkType} · {chunk.embeddingModel ?? "embedding 없음"}
                </div>
              </div>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
                {chunk.tokenCount ?? "-"} tok
              </span>
            </div>
            <p className="mt-3 line-clamp-4 text-xs leading-5 text-slate-600">
              {chunk.summary || chunk.content}
            </p>
          </div>
        ))}
        {selectedSourceId && chunks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
            chunk가 없습니다. 인덱싱을 실행해 주세요.
          </div>
        ) : null}
      </div>
    </article>
  );
}
