import { AlertTriangle, Cpu, FileJson2 } from "lucide-react";
import { JsonViewer } from "./JsonViewer";
import { NodeDetailTabs } from "./NodeDetailTabs";
import {
  formatCost,
  formatDateTime,
  formatMs,
  formatNumber,
  isRecord,
  normalizeStatus,
  statusClasses,
  statusLabel,
  type DetailTab,
  type LlmCallLog,
} from "../types/workflowDashboard.types";

interface NodeDetailPanelProps {
  log: LlmCallLog | null;
  activeTab: DetailTab;
  onTabChange: (tab: DetailTab) => void;
}

export function NodeDetailPanel({
  log,
  activeTab,
  onTabChange,
}: NodeDetailPanelProps) {
  return (
    <div className="flex max-h-[760px] min-w-0 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 truncate text-lg font-bold text-slate-950">노드 상세</h2>
          <p className="m-0 mt-1 truncate text-xs text-slate-500">
            {log?.nodeName ?? "노드를 선택하세요"}
          </p>
        </div>
        <FileJson2 className="h-5 w-5 shrink-0 text-[#315fbc]" />
      </div>

      {log ? (
        <>
          <NodeDetailTabs activeTab={activeTab} onChange={onTabChange} />
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <NodeTabContent log={log} activeTab={activeTab} />
          </div>
        </>
      ) : (
        <EmptyState text="선택된 노드가 없습니다." />
      )}
    </div>
  );
}

function NodeTabContent({
  log,
  activeTab,
}: {
  log: LlmCallLog;
  activeTab: DetailTab;
}) {
  if (activeTab === "input") {
    return (
      <ReadablePayload
        title="입력 데이터"
        value={log.requestJson}
        preferredKeys={["node", "model", "response_model"]}
      />
    );
  }

  if (activeTab === "output") {
    return <ReadablePayload title="출력 데이터" value={log.outputJson} />;
  }

  if (activeTab === "state") {
    return (
      <ReadablePayload
        title="상태 데이터"
        value={{
          "입력 상태": log.requestJson?.state ?? null,
          "출력 상태": log.outputJson?.state ?? log.outputJson,
        }}
      />
    );
  }

  if (activeTab === "router") {
    return (
      <ReadablePayload
        title="라우터 데이터"
        value={{
          "라우터": log.outputJson?.router ?? log.responseJson?.router ?? null,
          "현재 노드": log.nodeName,
          "실행 순서": log.executionOrder,
        }}
      />
    );
  }

  if (activeTab === "meta") {
    return <MetaDetail log={log} />;
  }

  return <FeedbackDetail log={log} />;
}

function ReadablePayload({
  title,
  value,
  preferredKeys = [],
}: {
  title: string;
  value: unknown;
  preferredKeys?: string[];
}) {
  if (value === null || value === undefined) {
    return <EmptyState text={`${title}가 없습니다.`} />;
  }

  if (!isRecord(value)) {
    return (
      <div className="space-y-3">
        <SectionTitle title={title} />
        <ReadableScalar value={value} />
      </div>
    );
  }

  const entries = Object.entries(value);
  const preferred = preferredKeys
    .map((key) => [key, value[key]] as const)
    .filter(([, item]) => item !== undefined);
  const scalarEntries = entries.filter(([, item]) => isScalar(item));
  const objectEntries = entries.filter(([, item]) => isRecord(item));
  const arrayEntries = entries.filter(([, item]) => Array.isArray(item));

  return (
    <div className="space-y-3">
      <SectionTitle title={title} />

      {preferred.length > 0 ? (
        <div className="grid gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm md:grid-cols-3">
          {preferred.map(([key, item]) => (
            <InfoItem key={key} label={labelize(key)} value={formatScalar(item)} />
          ))}
        </div>
      ) : null}

      {arrayEntries.map(([key, item]) => (
        <ArraySection key={key} name={key} items={Array.isArray(item) ? item : []} />
      ))}

      {objectEntries.map(([key, item]) => (
        <ObjectSection key={key} name={key} value={isRecord(item) ? item : {}} />
      ))}

      {scalarEntries.length > 0 ? (
        <div className="grid gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm">
          {scalarEntries.map(([key, item]) => (
            <KeyValueRow key={key} label={labelize(key)} value={formatScalar(item)} />
          ))}
        </div>
      ) : null}

      <details className="rounded-lg border border-slate-200 bg-white">
        <summary className="cursor-pointer px-3 py-2 text-sm font-semibold text-slate-700">
          원본 JSON 보기
        </summary>
        <div className="border-t border-slate-200 p-3">
          <JsonViewer value={value} maxHeightClassName="max-h-[320px]" />
        </div>
      </details>
    </div>
  );
}

function ArraySection({ name, items }: { name: string; items: unknown[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="m-0 text-sm font-bold text-slate-950">{labelize(name)}</h3>
        <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-500">
          {items.length.toLocaleString("ko-KR")}개 항목
        </span>
      </div>
      <div className="max-h-[430px] space-y-3 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <EmptyState text="항목이 없습니다." />
        ) : (
          items.map((item, index) => (
            <ReadableCard key={index} title={`${labelize(name)} #${index + 1}`} value={item} />
          ))
        )}
      </div>
    </section>
  );
}

function ObjectSection({
  name,
  value,
}: {
  name: string;
  value: Record<string, unknown>;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="m-0 text-sm font-bold text-slate-950">{labelize(name)}</h3>
        <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-500">
          {Object.keys(value).length.toLocaleString("ko-KR")}개 필드
        </span>
      </div>
      <ReadableObject value={value} />
    </section>
  );
}

function ReadableCard({ title, value }: { title: string; value: unknown }) {
  if (!isRecord(value)) {
    return (
      <article className="rounded-lg border border-slate-200 bg-white p-3">
        <div className="mb-2 text-sm font-semibold text-slate-900">{title}</div>
        <ReadableScalar value={value} />
      </article>
    );
  }

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="mb-2 text-sm font-semibold text-slate-900">
        {extractCardTitle(value, title)}
      </div>
      <ReadableObject value={value} />
    </article>
  );
}

function ReadableObject({ value }: { value: Record<string, unknown> }) {
  const scalarEntries = Object.entries(value).filter(([, item]) => isScalar(item));
  const nestedEntries = Object.entries(value).filter(
    ([, item]) => !isScalar(item) && item !== null && item !== undefined,
  );

  return (
    <div className="space-y-2">
      {scalarEntries.map(([key, item]) => (
        <KeyValueRow key={key} label={labelize(key)} value={formatScalar(item)} />
      ))}
      {nestedEntries.map(([key, item]) => (
        <div key={key} className="rounded-lg bg-slate-50 p-3">
          <div className="mb-2 text-xs font-bold text-slate-500">{labelize(key)}</div>
          {Array.isArray(item) ? (
            <div className="max-h-[360px] space-y-2 overflow-y-auto pr-1">
              {item.map((child, index) => (
                <ReadableCard
                  key={index}
                  title={`${labelize(key)} #${index + 1}`}
                  value={child}
                />
              ))}
            </div>
          ) : isRecord(item) ? (
            <ReadableObject value={item} />
          ) : (
            <ReadableScalar value={item} />
          )}
        </div>
      ))}
    </div>
  );
}

function KeyValueRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 rounded-lg border border-slate-100 bg-white px-3 py-2 md:grid-cols-[130px_1fr]">
      <span className="text-xs font-semibold text-slate-500">{label}</span>
      <span className="min-w-0 whitespace-pre-wrap break-words text-sm leading-6 text-slate-900">
        {value}
      </span>
    </div>
  );
}

function ReadableScalar({ value }: { value: unknown }) {
  return (
    <div className="max-h-[220px] overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-800">
      {formatScalar(value)}
    </div>
  );
}

function FeedbackDetail({ log }: { log: LlmCallLog }) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="mb-2 flex items-center gap-2">
          {normalizeStatus(log.callStatus) === "failed" ? (
            <AlertTriangle className="h-4 w-4 text-rose-500" />
          ) : (
            <Cpu className="h-4 w-4 text-[#315fbc]" />
          )}
          <strong className="text-sm text-slate-950">{log.nodeName ?? "unknown"}</strong>
          <StatusPill status={log.callStatus} />
        </div>
        <p className="m-0 whitespace-pre-wrap break-words text-sm leading-6 text-slate-600">
          {log.errorMessage ??
            "오류 없이 실행된 노드입니다. 입력, 출력, 상태, 라우터, 메타 탭에서 실행 데이터를 확인할 수 있습니다."}
        </p>
      </div>
      <ReadablePayload
        title="실행 요약"
        value={{
          "실행시간(ms)": log.elapsedMs,
          "총 토큰": log.totalTokens,
          "예상 비용": log.estimatedCost,
          "모델명": log.modelName,
        }}
      />
    </div>
  );
}

function MetaDetail({ log }: { log: LlmCallLog }) {
  return (
    <ReadablePayload
      title="메타 정보"
      value={{
        "노드명": log.nodeName ?? "-",
        "실행 유형": log.runType ?? "-",
        "실행 ID": log.runId ?? "-",
        "상위 실행 ID": log.parentRunId ?? "-",
        "추적 ID": log.traceId ?? "-",
        "실행 순서": log.executionOrder ?? "-",
        "입력 토큰": formatNumber(log.inputTokens),
        "출력 토큰": formatNumber(log.outputTokens),
        "총 토큰": formatNumber(log.totalTokens),
        "예상 비용": formatCost(log.estimatedCost),
        "실행시간": formatMs(log.elapsedMs),
        "상태": statusLabel(log.callStatus),
        "시작 시각": formatDateTime(log.startedAt),
        "종료 시각": formatDateTime(log.endedAt),
        "오류": log.errorMessage ?? "-",
      }}
    />
  );
}

function SectionTitle({ title }: { title: string }) {
  return <h3 className="m-0 text-sm font-bold text-slate-950">{title}</h3>;
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-semibold text-slate-500">{label}</div>
      <div className="mt-1 truncate text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-1 text-[11px] font-semibold ${statusClasses(
        status,
      )}`}
    >
      {statusLabel(status)}
    </span>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function isScalar(value: unknown): boolean {
  return (
    value === null ||
    value === undefined ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  );
}

function formatScalar(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return value.toLocaleString("ko-KR");
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function labelize(value: string): string {
  const labels: Record<string, string> = {
    input: "입력 메시지",
    output: "출력",
    reviews: "리뷰 결과",
    scores: "점수 결과",
    questions: "질문",
    answers: "예상 답변",
    follow_ups: "꼬리 질문",
    final_response: "최종 응답",
    response_model: "응답 스키마",
    model: "모델",
    node: "노드",
    role: "역할",
    content: "내용",
    status: "상태",
    reason: "사유",
    question_id: "질문 ID",
    score: "점수",
    score_reason: "점수 사유",
    recommended_revision: "수정 권장 사항",
    reject_reason: "반려 사유",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function extractCardTitle(value: Record<string, unknown>, fallback: string): string {
  const title =
    value.question_id ??
    value.id ??
    value.category ??
    value.status ??
    value.role ??
    fallback;
  return String(title);
}
