import { ArrowLeft } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import {
  KnowledgeChunkPreviewPanel,
  KnowledgeSearchPanel,
  KnowledgeSearchResultsPanel,
  KnowledgeSourceList,
  KnowledgeUploadPanel,
} from "../components/KnowledgeBasePanels";
import { JobProgressCard as SharedJobProgressCard } from "../components/JobProgressCard";
import { useJobPolling } from "../hooks/useJobPolling";
import {
  fetchActiveKnowledgeIndexJob,
  fetchKnowledgeChunks,
  fetchKnowledgeIndexJob,
  fetchKnowledgeSources,
  searchKnowledgeSources,
  submitKnowledgeIndexJob,
  submitSeedSourceDataJob,
  uploadKnowledgeSource,
} from "../services/jobPostingService";
import type {
  JobPostingAiJob,
  KnowledgeChunk,
  KnowledgeSearchResponse,
  KnowledgeSource,
} from "../types";

const ACTIVE_KNOWLEDGE_INDEX_JOB_KEY = "hrCopilot.activeKnowledgeIndexJob";

function readStoredKnowledgeIndexJob(): JobPostingAiJob | null {
  try {
    const raw = window.localStorage.getItem(ACTIVE_KNOWLEDGE_INDEX_JOB_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<JobPostingAiJob>;
    return typeof parsed.jobId === "number" && typeof parsed.status === "string"
      ? (parsed as JobPostingAiJob)
      : null;
  } catch {
    return null;
  }
}

function storeKnowledgeIndexJob(job: JobPostingAiJob | null) {
  try {
    if (job) {
      window.localStorage.setItem(ACTIVE_KNOWLEDGE_INDEX_JOB_KEY, JSON.stringify(job));
    } else {
      window.localStorage.removeItem(ACTIVE_KNOWLEDGE_INDEX_JOB_KEY);
    }
  } catch {
    // Best-effort refresh recovery only.
  }
}

function resolveJobSourceId(job: JobPostingAiJob): number | null {
  return Number(job.resultPayload?.source_id ?? job.requestPayload?.source_id ?? job.targetId) || null;
}

export function JobPostingKnowledgePage() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [versionLabel, setVersionLabel] = useState("");
  const [query, setQuery] = useState("개인 정보와 가족관계 기재 요구");
  const [searchMode, setSearchMode] = useState<"HYBRID" | "KEYWORD" | "VECTOR">(
    "HYBRID",
  );
  const [searchResult, setSearchResult] =
    useState<KnowledgeSearchResponse | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [indexingSourceId, setIndexingSourceId] = useState<number | null>(null);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const loadSources = useCallback(async () => {
    setPageLoading(true);
    setErrorMessage("");
    try {
      const data = await fetchKnowledgeSources({
        page: 0,
        size: 50,
        keyword,
      });
      setSources(data.items);
      if (!selectedSourceId && data.items[0]) {
        setSelectedSourceId(data.items[0].id);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "기반지식 문서 목록을 불러오지 못했습니다.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [keyword, selectedSourceId]);

  const handleIndexJobCompleted = useCallback(
    async (completedJob: JobPostingAiJob) => {
      const result = completedJob.resultPayload ?? {};
      const sourceId = Number(result.source_id ?? completedJob.targetId ?? indexingSourceId);
      if (result.total_sources !== undefined || result.total_chunks !== undefined) {
        setMessage(
          `source_data 적재 완료: ${Number(result.total_sources ?? 0)}개 문서, ${Number(result.total_chunks ?? 0)}개 chunk`,
        );
      } else {
        setMessage(
          `인덱싱 완료: ${Number(result.chunk_count ?? 0)}개 chunk가 생성되었습니다.`,
        );
      }

      setIsSeeding(false);
      setIndexingSourceId(null);
      storeKnowledgeIndexJob(null);
      if (sourceId) {
        setSelectedSourceId(sourceId);
        setChunks(await fetchKnowledgeChunks(sourceId));
      }
      await loadSources();
    },
    [indexingSourceId, loadSources],
  );

  const handleIndexJobFailed = useCallback((failedJob: JobPostingAiJob) => {
    setIsSeeding(false);
    setIndexingSourceId(null);
    storeKnowledgeIndexJob(null);
    setErrorMessage(
      failedJob.errorMessage || "문서 인덱싱 작업이 실패했습니다.",
    );
  }, []);

  const {
    job: activeIndexJob,
    isPolling: indexJobPolling,
    startPolling: startIndexJobPolling,
    clearJob: clearIndexJob,
  } = useJobPolling({
    fetcher: fetchKnowledgeIndexJob,
    onCompleted: handleIndexJobCompleted,
    onFailed: handleIndexJobFailed,
    onError: (error) => {
      setIsSeeding(false);
      setIndexingSourceId(null);
      setErrorMessage(
        error instanceof Error ? error.message : "작업 상태를 불러오지 못했습니다.",
      );
    },
  });

  useEffect(() => {
    let cancelled = false;

    async function initPage() {
      setPageLoading(true);
      setErrorMessage("");

      const storedJob = readStoredKnowledgeIndexJob();
      if (storedJob) {
        startIndexJobPolling(storedJob);
        setIndexingSourceId(resolveJobSourceId(storedJob));
      }

      void fetchActiveKnowledgeIndexJob()
        .then((activeJob) => {
          if (cancelled || !activeJob) {
            return;
          }
          storeKnowledgeIndexJob(activeJob);
          startIndexJobPolling(activeJob);
          setIndexingSourceId(resolveJobSourceId(activeJob));
        })
        .catch(() => {
          // Keep the locally restored card if the active-job probe is delayed.
        });

      const slowListTimer = window.setTimeout(() => {
        if (!cancelled) {
          setPageLoading(false);
        }
      }, 5000);

      try {
        const data = await fetchKnowledgeSources({
          page: 0,
          size: 50,
          keyword,
        });
        if (cancelled) {
          return;
        }

        setSources(data.items);
        setSelectedSourceId((current) => current ?? data.items[0]?.id ?? null);
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "기반지식 문서 목록을 불러오지 못했습니다.",
          );
        }
      } finally {
        window.clearTimeout(slowListTimer);
        if (!cancelled) {
          setPageLoading(false);
        }
      }
    }

    void initPage().catch(() => {
      if (!cancelled) {
        setPageLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [keyword, startIndexJobPolling]);

  useEffect(() => {
    if (!selectedSourceId) {
      setChunks([]);
      return;
    }
    const sourceId = selectedSourceId;
    async function loadChunks() {
      try {
        setChunks(await fetchKnowledgeChunks(sourceId));
      } catch {
        setChunks([]);
      }
    }
    void loadChunks();
  }, [selectedSourceId]);

  async function handleUpload() {
    if (!file) {
      setErrorMessage("업로드할 법률 PDF 또는 문서 파일을 선택해 주세요.");
      return;
    }
    setIsUploading(true);
    setErrorMessage("");
    setMessage("");
    try {
      const source = await uploadKnowledgeSource({
        file,
        title: title || undefined,
        versionLabel: versionLabel || undefined,
      });
      setMessage("기반지식 문서가 업로드되었습니다. 인덱싱을 실행해 주세요.");
      setSelectedSourceId(source.id);
      setFile(null);
      setTitle("");
      setVersionLabel("");
      await loadSources();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "문서 업로드에 실패했습니다.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleIndex(sourceId: number) {
    setIndexingSourceId(sourceId);
    setErrorMessage("");
    setMessage("");
    clearIndexJob();
    try {
      const submittedJob = await submitKnowledgeIndexJob(sourceId);
      storeKnowledgeIndexJob(submittedJob);
      startIndexJobPolling(submittedJob);
      setMessage("인덱싱 작업을 백그라운드로 시작했습니다. 진행 상태는 아래 카드에서 확인할 수 있습니다.");
      setSelectedSourceId(sourceId);
    } catch (error) {
      setIndexingSourceId(null);
      setErrorMessage(
        error instanceof Error ? error.message : "문서 인덱싱 작업을 시작하지 못했습니다.",
      );
    }
  }
  async function handleSeed() {
    setIsSeeding(true);
    setErrorMessage("");
    setMessage("");
    clearIndexJob();
    try {
      const submittedJob = await submitSeedSourceDataJob();
      storeKnowledgeIndexJob(submittedJob);
      startIndexJobPolling(submittedJob);
      setMessage("source_data 적재 작업을 백그라운드로 시작했습니다. 완료되면 목록이 자동으로 갱신됩니다.");
    } catch (error) {
      setIsSeeding(false);
      setErrorMessage(
        error instanceof Error ? error.message : "source_data 적재 작업을 시작하지 못했습니다.",
      );
    }
  }
  async function handleSearch() {
    if (!query.trim()) {
      setErrorMessage("검색할 위반 사례 또는 법률 쟁점을 입력해 주세요.");
      return;
    }
    setIsSearching(true);
    setErrorMessage("");
    try {
      setSearchResult(
        await searchKnowledgeSources({
          query,
          searchMode,
          limit: 10,
        }),
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "기반지식 검색에 실패했습니다.",
      );
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Knowledge Base RAG"
        title="채용공고 법률 기반지식"
        description="법률·가이드 문서를 업로드하고, 백그라운드 인덱싱 상태와 검색 품질을 확인합니다."
        actions={
          <Link
            to="/manager/job-postings"
            className="inline-flex h-11 items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-4 text-sm font-semibold text-[var(--text)]"
          >
            <ArrowLeft className="h-4 w-4" />
            공고 분석
          </Link>
        }
      />

      {message ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}
      {activeIndexJob ? <SharedJobProgressCard job={activeIndexJob} /> : null}

      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <KnowledgeUploadPanel
          title={title}
          versionLabel={versionLabel}
          file={file}
          isUploading={isUploading}
          isSeeding={isSeeding}
          onTitleChange={setTitle}
          onVersionLabelChange={setVersionLabel}
          onFileChange={setFile}
          onUpload={() => void handleUpload()}
          onSeed={() => void handleSeed()}
        />
        <KnowledgeSearchPanel
          query={query}
          searchMode={searchMode}
          searchResult={searchResult}
          isSearching={isSearching}
          onQueryChange={setQuery}
          onSearchModeChange={setSearchMode}
          onSearch={() => void handleSearch()}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <KnowledgeSourceList
          sources={sources}
          selectedSourceId={selectedSourceId}
          keywordInput={keywordInput}
          isLoading={pageLoading}
          indexingSourceId={indexingSourceId}
          jobPolling={indexJobPolling}
          onKeywordInputChange={setKeywordInput}
          onKeywordSubmit={setKeyword}
          onSelectSource={setSelectedSourceId}
          onIndex={(sourceId) => void handleIndex(sourceId)}
        />
        <div className="space-y-5">
          <KnowledgeSearchResultsPanel searchResult={searchResult} />
          <KnowledgeChunkPreviewPanel
            selectedSourceId={selectedSourceId}
            chunks={chunks}
          />
        </div>
      </section>
    </div>
  );
}



