import {
  Braces,
  BriefcaseBusiness,
  CalendarClock,
  ClipboardList,
  FileText,
  Mail,
  Phone,
  UserRound,
} from "lucide-react";
import type { ReactNode } from "react";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import type {
  InterviewSessionDetailResponse,
  InterviewSessionPayloadDocument,
} from "../types";

interface InterviewSessionAssembledPayloadViewProps {
  detail: InterviewSessionDetailResponse;
  compact?: boolean;
}

function formatDateTime(value: string | null) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function truncateText(value: string | null, maxLength = 900) {
  if (!value) {
    return "";
  }
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength).trim()}...`;
}

function renderFileSize(value: number | null) {
  if (!value) {
    return "-";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function FieldRow({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="grid gap-1 border-b border-slate-100 py-2 last:border-b-0 sm:grid-cols-[120px_1fr]">
      <dt className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">
        {label}
      </dt>
      <dd className="min-w-0 break-words text-sm font-medium text-slate-800">
        {value ?? "-"}
      </dd>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  tone = "slate",
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone?: "slate" | "sky" | "emerald" | "amber";
}) {
  const toneStyle = {
    slate: "border-slate-200 bg-white text-slate-900",
    sky: "border-sky-200 bg-sky-50 text-sky-900",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-900",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
  }[tone];

  return (
    <div className={`rounded-2xl border p-4 ${toneStyle}`}>
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] opacity-70">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-xl font-bold">{value}</div>
    </div>
  );
}

function DocumentCard({ document }: { document: InterviewSessionPayloadDocument }) {
  const textLength = document.extractedText?.length ?? 0;
  const hasText = textLength > 0;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              {document.documentType}
            </span>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                hasText
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              {document.extractStatus}
            </span>
          </div>
          <h4 className="mt-3 break-words text-base font-bold text-slate-950">
            {document.title}
          </h4>
          <p className="mt-1 break-words text-sm text-slate-500">
            {document.originalFileName}
          </p>
        </div>
        <div className="shrink-0 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-right">
          <div className="text-xs font-semibold text-slate-500">텍스트 길이</div>
          <div className="text-sm font-bold text-slate-900">
            {textLength.toLocaleString()} chars
          </div>
        </div>
      </div>

      <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs font-semibold text-slate-400">MIME</dt>
          <dd className="mt-1 break-words font-medium text-slate-800">
            {document.mimeType ?? "-"}
          </dd>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs font-semibold text-slate-400">확장자</dt>
          <dd className="mt-1 font-medium text-slate-800">{document.fileExt ?? "-"}</dd>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs font-semibold text-slate-400">파일 크기</dt>
          <dd className="mt-1 font-medium text-slate-800">
            {renderFileSize(document.fileSize)}
          </dd>
        </div>
      </dl>

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-slate-500">
          <FileText className="h-3.5 w-3.5" />
          Extracted Text Preview
        </div>
        <pre className="mt-3 max-h-[260px] overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-700">
          {truncateText(document.extractedText) || "추출된 텍스트가 없습니다."}
        </pre>
      </div>

      {Object.keys(document.structuredData ?? {}).length > 0 ? (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-bold text-slate-800">
            Structured Data
            <Braces className="h-4 w-4 text-slate-500" />
          </summary>
          <pre className="mt-3 max-h-[260px] overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-700">
            {JSON.stringify(document.structuredData, null, 2)}
          </pre>
        </details>
      ) : null}
    </article>
  );
}

export function InterviewSessionAssembledPayloadView({
  detail,
  compact = false,
}: InterviewSessionAssembledPayloadViewProps) {
  const payload = detail.assembledPayloadPreview;
  const rawPayload = JSON.stringify(payload, null, 2);
  const documentTextTotal = payload.candidateDocuments.reduce(
    (sum, document) => sum + (document.extractedText?.length ?? 0),
    0,
  );
  const extractedDocumentCount = payload.candidateDocuments.filter(
    (document) => (document.extractedText?.length ?? 0) > 0,
  ).length;

  return (
    <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-6 shadow-[var(--shadow)]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.1em] text-sky-800">
            <ClipboardList className="h-3.5 w-3.5" />
            LangGraph Input
          </div>
          <h2 className="mt-3 text-2xl font-bold text-[var(--text)]">
            질문 생성 입력 Payload
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--muted)]">
            세션, 지원자, 프롬프트 프로필, 문서 추출 결과를 LangGraph 실행 직전
            형태로 확인합니다.
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={<BriefcaseBusiness className="h-4 w-4" />}
          label="Target Job"
          value={getJobPositionLabel(payload.session.targetJob)}
          tone="sky"
        />
        <MetricCard
          icon={<FileText className="h-4 w-4" />}
          label="Documents"
          value={`${payload.candidateDocuments.length}개`}
          tone="emerald"
        />
        <MetricCard
          icon={<FileText className="h-4 w-4" />}
          label="Extracted"
          value={`${extractedDocumentCount}개`}
          tone="amber"
        />
        <MetricCard
          icon={<Braces className="h-4 w-4" />}
          label="Text Volume"
          value={`${documentTextTotal.toLocaleString()} chars`}
        />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-950">
            <CalendarClock className="h-4 w-4 text-sky-600" />
            Session
          </div>
          <dl className="mt-3">
            <FieldRow label="Session ID" value={payload.session.sessionId} />
            <FieldRow label="Candidate ID" value={payload.session.candidateId} />
            <FieldRow
              label="Target Job"
              value={getJobPositionLabel(payload.session.targetJob)}
            />
            <FieldRow label="Difficulty" value={payload.session.difficultyLevel} />
            <FieldRow label="Prompt ID" value={payload.session.promptProfileId} />
            <FieldRow label="Created" value={formatDateTime(payload.session.createdAt)} />
          </dl>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-950">
            <UserRound className="h-4 w-4 text-emerald-600" />
            Candidate
          </div>
          <dl className="mt-3">
            <FieldRow label="Name" value={payload.candidate.name} />
            <FieldRow label="Email" value={payload.candidate.email} />
            <FieldRow label="Phone" value={payload.candidate.phone} />
            <FieldRow label="Birth Date" value={payload.candidate.birthDate} />
            <FieldRow
              label="Position"
              value={
                payload.candidate.jobPosition
                  ? getJobPositionLabel(payload.candidate.jobPosition)
                  : "-"
              }
            />
            <FieldRow label="Status" value={payload.candidate.applyStatus} />
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            {payload.candidate.email ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                <Mail className="h-3.5 w-3.5" />
                Email
              </span>
            ) : null}
            {payload.candidate.phone ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                <Phone className="h-3.5 w-3.5" />
                Phone
              </span>
            ) : null}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-950">
            <Braces className="h-4 w-4 text-amber-600" />
            Prompt Profile
          </div>
          {payload.promptProfile ? (
            <>
              <dl className="mt-3">
                <FieldRow label="ID" value={payload.promptProfile.id} />
                <FieldRow label="Key" value={payload.promptProfile.profileKey} />
                <FieldRow
                  label="Target Job"
                  value={
                    payload.promptProfile.targetJob
                      ? getJobPositionLabel(payload.promptProfile.targetJob)
                      : "-"
                  }
                />
              </dl>
              <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-bold uppercase tracking-[0.1em] text-slate-500">
                  System Prompt
                </div>
                <pre className="mt-3 max-h-[220px] overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-700">
                  {payload.promptProfile.systemPrompt}
                </pre>
              </div>
            </>
          ) : (
            <p className="mt-3 text-sm text-slate-500">
              연결된 프롬프트 프로필이 없습니다.
            </p>
          )}
        </div>
      </div>

      <div className="mt-6">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="text-lg font-bold text-[var(--text)]">문서 입력 데이터</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              지원자 문서별 추출 상태와 LangGraph에 전달될 텍스트 preview입니다.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {extractedDocumentCount} / {payload.candidateDocuments.length} documents
            extracted
          </span>
        </div>

        <div className="mt-4 grid gap-4">
          {payload.candidateDocuments.length > 0 ? (
            payload.candidateDocuments.map((document) => (
              <DocumentCard key={document.documentId} document={document} />
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
              연결된 문서가 없습니다.
            </div>
          )}
        </div>
      </div>

      {!compact ? (
        <details className="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-bold text-slate-900">
            Raw Payload JSON
            <Braces className="h-4 w-4 text-slate-500" />
          </summary>
          <pre className="mt-4 max-h-[520px] overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-700">
            {rawPayload}
          </pre>
        </details>
      ) : null}
    </section>
  );
}
