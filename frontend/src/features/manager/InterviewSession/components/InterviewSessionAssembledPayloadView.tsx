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

function truncateText(value: string | null, maxLength = 800) {
  if (!value) {
    return "";
  }
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength)}...`;
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

function renderDocumentCard(document: InterviewSessionPayloadDocument) {
  const textLength = document.extractedText?.length ?? 0;

  return (
    <article
      key={document.documentId}
      className="rounded-[24px] border border-[var(--line)] bg-white/80 p-5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {document.documentType}
        </span>
        <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
          {document.extractStatus}
        </span>
        <span className="inline-flex rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-800">
          text {textLength.toLocaleString()} chars
        </span>
      </div>

      <h4 className="mt-4 text-base font-bold text-[var(--text)]">{document.title}</h4>
      <div className="mt-1 text-sm text-[var(--muted)]">{document.originalFileName}</div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            MIME Type
          </div>
          <div className="mt-2 text-sm text-[var(--text)]">{document.mimeType ?? "-"}</div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            File Ext
          </div>
          <div className="mt-2 text-sm text-[var(--text)]">{document.fileExt ?? "-"}</div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            File Size
          </div>
          <div className="mt-2 text-sm text-[var(--text)]">{renderFileSize(document.fileSize)}</div>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
        <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
          Extracted Text Preview
        </div>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-[var(--text)]">
          {truncateText(document.extractedText) || "추출 텍스트가 없습니다."}
        </pre>
      </div>

      <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
        <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
          Structured Data
        </div>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-[var(--text)]">
          {JSON.stringify(document.structuredData ?? {}, null, 2)}
        </pre>
      </div>
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

  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[var(--text)]">조립된 데이터</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            `request_candidate_interview_prep(...)` 호출 직전 기준으로 조립된 payload입니다.
          </p>
        </div>
        <div className="inline-flex rounded-2xl border border-sky-200 bg-sky-50 px-4 py-2 text-sm font-semibold text-sky-900">
          문서 {payload.candidateDocuments.length}개 / 추출 텍스트{" "}
          {documentTextTotal.toLocaleString()} chars
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <div className="rounded-[24px] border border-[var(--line)] bg-[var(--panel-strong)] p-5">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            Session
          </div>
          <div className="mt-4 space-y-2 text-sm text-[var(--text)]">
            <div>Session ID: {payload.session.sessionId}</div>
            <div>Candidate ID: {payload.session.candidateId}</div>
            <div>Target Job: {getJobPositionLabel(payload.session.targetJob)}</div>
            <div>Difficulty: {payload.session.difficultyLevel ?? "-"}</div>
            <div>Prompt Profile ID: {payload.session.promptProfileId ?? "-"}</div>
            <div>Created At: {formatDateTime(payload.session.createdAt)}</div>
          </div>
        </div>

        <div className="rounded-[24px] border border-[var(--line)] bg-[var(--panel-strong)] p-5">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            Candidate
          </div>
          <div className="mt-4 space-y-2 text-sm text-[var(--text)]">
            <div>Name: {payload.candidate.name}</div>
            <div>Email: {payload.candidate.email ?? "-"}</div>
            <div>Phone: {payload.candidate.phone ?? "-"}</div>
            <div>Birth Date: {payload.candidate.birthDate ?? "-"}</div>
            <div>
              Job Position:{" "}
              {payload.candidate.jobPosition
                ? getJobPositionLabel(payload.candidate.jobPosition)
                : "-"}
            </div>
            <div>Apply Status: {payload.candidate.applyStatus ?? "-"}</div>
          </div>
        </div>

        <div className="rounded-[24px] border border-[var(--line)] bg-[var(--panel-strong)] p-5">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            Prompt Profile
          </div>
          {payload.promptProfile ? (
            <div className="mt-4 space-y-2 text-sm text-[var(--text)]">
              <div>ID: {payload.promptProfile.id}</div>
              <div>Profile Key: {payload.promptProfile.profileKey}</div>
              <div>
                Target Job:{" "}
                {payload.promptProfile.targetJob
                  ? getJobPositionLabel(payload.promptProfile.targetJob)
                  : "-"}
              </div>
              <div className="pt-2 text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                System Prompt
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-[var(--text)]">
                {payload.promptProfile.systemPrompt}
              </pre>
            </div>
          ) : (
            <div className="mt-4 text-sm text-[var(--muted)]">연결된 프롬프트 프로필이 없습니다.</div>
          )}
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <div>
          <h3 className="text-lg font-bold text-[var(--text)]">문서 입력 데이터</h3>
          <p className="mt-2 text-sm text-[var(--muted)]">
            지원자 문서별 추출 결과와 preview입니다.
          </p>
        </div>
        <div className="space-y-4">
          {payload.candidateDocuments.length > 0 ? (
            payload.candidateDocuments.map(renderDocumentCard)
          ) : (
            <div className="rounded-[24px] border border-[var(--line)] bg-[var(--panel-strong)] p-5 text-sm text-[var(--muted)]">
              연결된 문서가 없습니다.
            </div>
          )}
        </div>
      </div>

      {!compact ? (
        <div className="mt-6 rounded-[24px] border border-[var(--line)] bg-[var(--panel-strong)] p-5">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            Raw Payload JSON
          </div>
          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-[var(--text)]">
            {rawPayload}
          </pre>
        </div>
      ) : null}
    </section>
  );
}
