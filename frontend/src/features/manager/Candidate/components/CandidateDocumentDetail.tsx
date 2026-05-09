import {
  ArrowLeft,
  Award,
  BriefcaseBusiness,
  Calendar,
  Download,
  FileText,
  GraduationCap,
  LoaderCircle,
  Mail,
  MapPin,
  Phone,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useMemo } from "react";
import { StatusPill } from "../../../../common/components/StatusPill";
import type {
  CandidateDetailResponse,
  CandidateDocumentDetailResponse,
} from "../types";

interface CandidateDocumentDetailProps {
  candidate: CandidateDetailResponse | null;
  document: CandidateDocumentDetailResponse | null;
  isLoading: boolean;
  isExtractRefreshing: boolean;
  onBack: () => void;
  onDownload: () => void;
}

interface ParsedDocumentSection {
  id: string;
  title: string;
  lines: string[];
}

interface ParsedDocumentText {
  name: string | null;
  summary: string | null;
  contacts: string[];
  sections: ParsedDocumentSection[];
}

const documentSectionHeadings = [
  "프로젝트 및 주요 경험",
  "대외활동 및 추가 경험",
  "핵심 역량 및 경험",
  "협업 및 갈등 경험",
  "실패 및 학습 경험",
  "자격증 및 어학",
  "기술 및 역량",
  "입사 후 포부",
  "지원 동기",
  "자기소개서",
  "보유 역량",
  "학력",
  "경력",
] as const;

const headingSet = new Set<string>(documentSectionHeadings);

const genericHeadingSuffixes = [
  "개요",
  "경력",
  "경험",
  "계획",
  "과정",
  "교육",
  "기술",
  "동기",
  "목표",
  "병역",
  "사항",
  "소개",
  "소개서",
  "수상",
  "스킬",
  "어학",
  "역량",
  "요약",
  "이력",
  "이해",
  "자격",
  "장점",
  "정보",
  "지원",
  "직무",
  "특기",
  "포부",
  "프로젝트",
  "학력",
  "활동",
] as const;

const sectionStyles = [
  {
    match: ["학력"],
    icon: GraduationCap,
    accent: "text-sky-600",
    badge: "bg-sky-50 text-sky-700 ring-sky-100",
  },
  {
    match: ["경력", "프로젝트", "대외활동"],
    icon: BriefcaseBusiness,
    accent: "text-emerald-600",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  },
  {
    match: ["역량", "자격증"],
    icon: Award,
    accent: "text-violet-600",
    badge: "bg-violet-50 text-violet-700 ring-violet-100",
  },
  {
    match: ["자기소개서", "지원 동기", "협업", "실패", "포부"],
    icon: Sparkles,
    accent: "text-amber-600",
    badge: "bg-amber-50 text-amber-700 ring-amber-100",
  },
] as const;

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeExtractedText(text: string) {
  const headingPattern = documentSectionHeadings
    .map(escapeRegExp)
    .join("|");

  return text
    .replace(/\r\n?/g, "\n")
    .replace(new RegExp(`\\s*(${headingPattern})(?=\\s|$)`, "g"), "\n$1\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function normalizeHeadingText(value: string) {
  return value.replace(/[:：]$/, "").trim();
}

function isContactLikeLine(line: string) {
  return (
    line.includes("|") ||
    line.includes("@") ||
    /\d{2,3}-\d{3,4}-\d{4}/.test(line)
  );
}

function isLikelySectionHeading(line: string, allowUntypedShortTitle = false) {
  const normalizedLine = normalizeHeadingText(line);
  const words = normalizedLine.split(/\s+/).filter(Boolean);

  if (!normalizedLine || isContactLikeLine(normalizedLine)) {
    return false;
  }

  if (headingSet.has(normalizedLine)) {
    return true;
  }

  if (
    normalizedLine.startsWith("-") ||
    normalizedLine.length > 34 ||
    words.length > 5 ||
    /[.!?。]$/.test(normalizedLine) ||
    /(습니다|합니다|입니다|했습니다|됩니다|였습니다)$/.test(normalizedLine)
  ) {
    return false;
  }

  if (!/^[가-힣A-Za-z0-9/&().·\s-]+$/.test(normalizedLine)) {
    return false;
  }

  if (
    genericHeadingSuffixes.some((suffix) => normalizedLine.endsWith(suffix)) ||
    /(및|\/|·)/.test(normalizedLine)
  ) {
    return true;
  }

  return allowUntypedShortTitle && normalizedLine.length <= 14 && words.length <= 3;
}

function getSectionHeading(line: string, lineIndex: number) {
  const normalizedLine = normalizeHeadingText(line);

  if (headingSet.has(normalizedLine)) {
    return normalizedLine;
  }

  if (lineIndex === 0) {
    return null;
  }

  return isLikelySectionHeading(normalizedLine) ? normalizedLine : null;
}

function splitInlineSectionLine(line: string) {
  const matchedHeading = documentSectionHeadings.find((heading) =>
    line.startsWith(`${heading} `),
  );

  if (matchedHeading) {
    return {
      heading: matchedHeading,
      content: line.slice(matchedHeading.length).trim(),
    };
  }

  const colonSection = line.match(/^(.{2,34})[:：]\s*(.+)$/);
  if (colonSection && isLikelySectionHeading(colonSection[1], true)) {
    return {
      heading: normalizeHeadingText(colonSection[1]),
      content: colonSection[2].trim(),
    };
  }

  const words = line.split(/\s+/).filter(Boolean);
  for (let prefixLength = Math.min(5, words.length - 1); prefixLength >= 1; prefixLength -= 1) {
    const heading = words.slice(0, prefixLength).join(" ");
    const content = words.slice(prefixLength).join(" ");

    if (content.length >= 12 && isLikelySectionHeading(heading)) {
      return {
        heading,
        content,
      };
    }
  }

  return null;
}

function parseDocumentText(text: string): ParsedDocumentText {
  const lines = normalizeExtractedText(text)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const firstHeadingIndex = lines.findIndex((line, index) => {
    const inlineSection = splitInlineSectionLine(line);
    return Boolean(getSectionHeading(line, index) || (index > 0 && inlineSection));
  });
  const profileLines =
    firstHeadingIndex >= 0 ? lines.slice(0, firstHeadingIndex) : lines.slice(0, 3);
  const contentLines = firstHeadingIndex >= 0 ? lines.slice(firstHeadingIndex) : lines.slice(3);
  const contactIndex = profileLines.findIndex((line) => line.includes("|"));
  const contacts =
    contactIndex >= 0
      ? profileLines[contactIndex]
          .split("|")
          .map((item) => item.trim())
          .filter(Boolean)
      : [];
  const summaryLines = profileLines.filter((_, index) => index !== 0 && index !== contactIndex);
  const sections: ParsedDocumentSection[] = [];
  let currentSection: ParsedDocumentSection | null = null;

  contentLines.forEach((line, index) => {
    const originalLineIndex =
      firstHeadingIndex >= 0 ? firstHeadingIndex + index : profileLines.length + index;
    const inlineSection = splitInlineSectionLine(line);
    const heading = getSectionHeading(line, originalLineIndex) ?? inlineSection?.heading;
    const content = inlineSection?.content;

    if (heading) {
      currentSection = {
        id: `${sections.length}-${heading}`,
        title: heading,
        lines: [],
      };
      sections.push(currentSection);

      if (content) {
        currentSection.lines.push(content);
      }
      return;
    }

    if (!currentSection) {
      currentSection = {
        id: "0-본문",
        title: "본문",
        lines: [],
      };
      sections.push(currentSection);
    }

    currentSection.lines.push(line);
  });

  const mergedSections = sections.reduce<ParsedDocumentSection[]>(
    (result, section) => {
      if (section.lines.length === 0) {
        const previous = result.at(-1);
        if (previous && previous.lines.length === 0) {
          previous.title = `${previous.title} · ${section.title}`;
          previous.id = `${previous.id}-${section.title}`;
          return result;
        }

        result.push({ ...section });
        return result;
      }

      const previous = result.at(-1);
      if (previous && previous.lines.length === 0) {
        previous.title = `${previous.title} · ${section.title}`;
        previous.id = `${previous.id}-${section.title}`;
        previous.lines = section.lines;
        return result;
      }

      result.push(section);
      return result;
    },
    [],
  );

  return {
    name: profileLines[0] ?? null,
    summary: summaryLines.join(" ") || null,
    contacts,
    sections: mergedSections,
  };
}

function getSectionStyle(title: string) {
  return (
    sectionStyles.find((style) =>
      style.match.some((keyword) => title.includes(keyword)),
    ) ?? {
      icon: FileText,
      accent: "text-slate-600",
      badge: "bg-slate-50 text-slate-700 ring-slate-100",
    }
  );
}

function getContactIcon(value: string) {
  if (value.includes("@")) {
    return Mail;
  }

  if (/\d{2,3}-\d{3,4}-\d{4}/.test(value)) {
    return Phone;
  }

  if (/출생|생년|19|20/.test(value)) {
    return Calendar;
  }

  return MapPin;
}

function splitMetaLine(line: string) {
  return line
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);
}

function FormattedDocumentLine({ line }: { line: string }) {
  const cleanLine = line.replace(/^-\s*/, "").trim();
  const isBullet = line.trim().startsWith("-");
  const metaItems = splitMetaLine(cleanLine);

  if (metaItems.length > 1) {
    return (
      <div className="rounded-2xl border border-slate-100 bg-slate-50/80 px-4 py-3">
        <p className="font-semibold leading-6 text-slate-900">{metaItems[0]}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {metaItems.slice(1).map((item) => (
            <span
              key={item}
              className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200"
            >
              {item}
            </span>
          ))}
        </div>
      </div>
    );
  }

  if (isBullet) {
    return (
      <li className="ml-4 list-disc pl-1 leading-7 text-slate-700">
        {cleanLine}
      </li>
    );
  }

  return <p className="leading-7 text-slate-700">{cleanLine}</p>;
}

function StructuredExtractedText({ text }: { text: string }) {
  const parsed = useMemo(() => parseDocumentText(text), [text]);

  return (
    <div className="max-h-[70vh] overflow-auto rounded-2xl border border-slate-200 bg-white">
      {(parsed.name || parsed.summary || parsed.contacts.length > 0) ? (
        <div className="border-b border-slate-100 bg-slate-50/70 p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100">
              <UserRound className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-600">
                Candidate Profile
              </p>
              <h4 className="mt-1 text-2xl font-bold text-slate-950">
                {parsed.name ?? "지원자 문서"}
              </h4>
              {parsed.summary ? (
                <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-700">
                  {parsed.summary}
                </p>
              ) : null}
            </div>
          </div>

          {parsed.contacts.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {parsed.contacts.map((contact) => {
                const Icon = getContactIcon(contact);

                return (
                  <span
                    key={contact}
                    className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 ring-1 ring-slate-200"
                  >
                    <Icon className="h-3.5 w-3.5 text-slate-400" />
                    {contact}
                  </span>
                );
              })}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="space-y-4 p-5">
        {parsed.sections.map((section) => {
          const style = getSectionStyle(section.title);
          const Icon = style.icon;

          return (
            <article
              key={section.id}
              className="rounded-2xl border border-slate-100 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.04)]"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-2xl ring-1 ${style.badge}`}
                >
                  <Icon className="h-5 w-5" />
                </span>
                <h4 className={`text-base font-bold ${style.accent}`}>
                  {section.title}
                </h4>
              </div>

              <div className="mt-4 space-y-3 text-sm">
                {section.lines.length > 0 ? (
                  section.lines.map((line, index) => (
                    <FormattedDocumentLine key={`${section.id}-${index}`} line={line} />
                  ))
                ) : (
                  <p className="text-sm text-slate-500">내용이 없습니다.</p>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function formatDateTime(value?: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");

  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

function formatFileSize(value: number | null) {
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

function getExtractMessage(document: CandidateDocumentDetailResponse | null) {
  if (!document) {
    return "문서 정보를 불러오는 중입니다.";
  }

  if (document.extractStatus === "PENDING") {
    return "텍스트 추출이 아직 진행 중입니다.";
  }

  if (document.extractStatus === "FAILED") {
    return "텍스트 추출에 실패했거나 추출 가능한 본문이 없습니다.";
  }

  return "추출된 텍스트가 없습니다.";
}

export function CandidateDocumentDetail({
  candidate,
  document,
  isLoading,
  isExtractRefreshing,
  onBack,
  onDownload,
}: CandidateDocumentDetailProps) {
  const isPending = document?.extractStatus === "PENDING";
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="flex flex-col gap-4 border-b border-[var(--line)] pb-5 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-4">
          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-700"
            onClick={onBack}
            aria-label="지원자 상세로 이동"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>

          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-600">
              Document
            </p>
            <h2 className="mt-2 text-2xl font-bold text-[var(--text)]">
              {document?.originalFileName ?? "문서 상세"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {candidate ? `${candidate.name} 지원자의 문서 상세와 추출 텍스트를 확인합니다.` : "문서 메타 정보와 추출 결과를 확인합니다."}
            </p>
          </div>
        </div>

        {document ? <StatusPill status={document.extractStatus} /> : null}
      </div>

      {isLoading ? (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-[var(--muted)]">
          문서 상세 정보를 불러오는 중입니다.
        </div>
      ) : (
        <div className="mt-6 grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="space-y-4">
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
              <h3 className="text-lg font-bold text-[var(--text)]">문서 정보</h3>

              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    지원자
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {candidate?.name ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    문서 종류
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {document?.documentType ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    파일 크기
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {formatFileSize(document?.fileSize ?? null)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    생성 날짜
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {formatDateTime(document?.createdAt)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    추출 상태
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {document?.extractStatus ?? "-"}
                  </p>
                  {isPending ? (
                    <div className="mt-2 inline-flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
                      <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                      <span>추출 처리 중</span>
                      {isExtractRefreshing ? <span>· 상태 확인 중</span> : null}
                    </div>
                  ) : null}
                </div>
              </div>

              <button
                type="button"
                className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-2xl border border-sky-200 bg-sky-50 px-4 text-sm font-semibold text-sky-700 transition hover:bg-sky-100"
                onClick={onDownload}
                disabled={!document}
              >
                <Download className="h-4 w-4" />
                문서 다운로드
              </button>
            </div>
          </aside>

          <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-emerald-600" />
              <div>
                <h3 className="text-lg font-bold text-[var(--text)]">추출 텍스트</h3>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  OCR 및 텍스트 추출 결과를 확인하는 영역입니다.
                </p>
                {isPending ? (
                  <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700">
                    <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                    <span>문서 추출이 진행 중입니다. 완료되면 본문이 자동으로 표시됩니다.</span>
                  </div>
                ) : null}
              </div>
            </div>

            {document?.extractedText ? (
              <div className="mt-5">
                <StructuredExtractedText text={document.extractedText} />
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center text-sm text-[var(--muted)]">
                {getExtractMessage(document)}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
