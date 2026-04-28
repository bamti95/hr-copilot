import { CheckSquare, RefreshCcw, Square, UserRound, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { InterviewSessionAssembledPayloadView } from "./InterviewSessionAssembledPayloadView";
import { InterviewSessionQuestionGenerationView } from "./InterviewSessionQuestionGenerationView";
import type { InterviewSessionDetailResponse } from "../types";

interface InterviewSessionDetailModalProps {
  open: boolean;
  detail: InterviewSessionDetailResponse | null;
  isLoading: boolean;
  isSaving: boolean;
  onClose: () => void;
  onEdit: (sessionId: number) => void;
  onDelete: (sessionId: number, candidateName: string) => void;
  onTriggerQuestionGeneration: (sessionId: number) => void;
}

interface InterviewQuestionCardItem {
  id: string;
  category: string;
  question: string;
  generationReason: string;
  expectedAnswer: string;
  followUpQuestions: string[];
  evaluationGuide: {
    high: string;
    medium: string;
    low: string;
  };
}

interface CandidateContext {
  name: string;
  targetJobLabel: string;
  jobPositionLabel: string;
  applyStatus: string;
  phone: string;
  difficulty: string;
  documentCount: number;
  documentTitles: string;
  snippet: string;
}

function formatDateTime(value: string | null) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function extractCandidateContext(detail: InterviewSessionDetailResponse): CandidateContext {
  const payload = detail.assembledPayloadPreview;
  const documents = payload.candidateDocuments;
  const titles = documents.map((document) => document.title).filter(Boolean);
  const snippets = documents
    .map((document) => document.extractedText?.replace(/\s+/g, " ").trim())
    .filter((value): value is string => Boolean(value))
    .slice(0, 2)
    .join(" / ");

  return {
    name: payload.candidate.name,
    targetJobLabel: getJobPositionLabel(detail.targetJob),
    jobPositionLabel: payload.candidate.jobPosition
      ? getJobPositionLabel(payload.candidate.jobPosition)
      : "미입력",
    applyStatus: payload.candidate.applyStatus ?? "미입력",
    phone: payload.candidate.phone ?? "-",
    difficulty: detail.difficultyLevel ?? "미설정",
    documentCount: documents.length,
    documentTitles: titles.length > 0 ? titles.join(", ") : "지원자 문서 없음",
    snippet:
      snippets ||
      `${payload.candidate.name} 지원자의 자기소개서와 경력 문서 내용을 기준으로 질문을 검토합니다.`,
  };
}

function buildQuestionVariants(context: CandidateContext): Record<string, InterviewQuestionCardItem[]> {
  const { name, targetJobLabel, applyStatus, difficulty, documentCount, documentTitles, snippet } =
    context;

  return {
    "hard-skill": [
      {
        id: "hard-skill",
        category: "직무 역량 적합성 검증",
        question: `${name}님은 ${targetJobLabel} 포지션에서 사용한 기술 중 가장 자신 있는 스택을 하나 꼽는다면 무엇인가요? 그 기술로 성능이나 품질을 개선할 때 비교했던 대안은 무엇이었고, 왜 그 선택이 최적이었다고 판단했나요?`,
        generationReason: `지원 직무가 ${targetJobLabel}이고, 조립된 문서 ${documentCount}건(${documentTitles})을 기준으로 기술 선택 근거와 실제 숙련도를 검증할 필요가 있습니다.`,
        expectedAnswer: `${targetJobLabel} 실무에서 기술을 왜 선택했는지, 당시 제약 조건과 대안 기술 비교, 도입 전후 지표 변화까지 자기 언어로 설명하는 답변이 기대됩니다.`,
        followUpQuestions: [
          "그 기술을 선택하지 않았다면 차선책으로 어떤 접근을 고려했나요?",
          "성능 개선이나 품질 향상을 수치로 설명할 수 있는 결과가 있었나요?",
        ],
        evaluationGuide: {
          high: "기술 선택의 이유와 대안 비교, 개선 결과를 수치와 맥락으로 구체적으로 설명한다.",
          medium: "기술 특징은 알고 있지만 프로젝트 맥락에 맞춘 판단 근거가 다소 평면적이다.",
          low: "유행이나 타인 권유 중심으로 사용했고 기술 원리와 선택 기준을 설명하지 못한다.",
        },
      },
      {
        id: "hard-skill",
        category: "직무 역량 적합성 검증",
        question: `${name}님이 ${targetJobLabel} 관련 프로젝트에서 기술 스택을 새로 도입하거나 교체했던 경험이 있다면, 기존 방식을 유지하지 않고 바꾸기로 결정한 결정적 이유는 무엇이었나요?`,
        generationReason: `${targetJobLabel} 직무 적합성을 볼 때 단순 사용 경험보다 실제 기술 의사결정 경험을 확인하는 것이 중요합니다. 문서 요약(${snippet}) 기준으로도 선택 이유를 깊게 물을 필요가 있습니다.`,
        expectedAnswer: "기술 도입의 명확한 배경, 기존 방식의 한계, 대안 비교, 리스크 관리, 도입 후 얻은 개선점을 연결해서 설명하는 답변이 적절합니다.",
        followUpQuestions: [
          "도입 직후 예상과 달랐던 문제는 무엇이었고 어떻게 보완했나요?",
          "기술적으로는 좋아도 팀이 받아들이기 어려운 상황이었다면 어떻게 설득했나요?",
        ],
        evaluationGuide: {
          high: "기술 교체의 배경과 효과, 조직 내 설득 포인트를 실무적으로 설명한다.",
          medium: "경험은 있으나 선택 기준과 트레이드오프 설명이 다소 단편적이다.",
          low: "왜 바꿨는지보다 단순히 써보았다는 수준의 답변에 머문다.",
        },
      },
    ],
    "culture-fit": [
      {
        id: "culture-fit",
        category: "조직 및 문화 적합성",
        question: `${name}님이 중요하게 생각하는 일하는 방식이 분명한 상황에서, 팀 전체가 마감 직전이라 일주일 정도 고강도 대응이 필요하다면 어떻게 행동하시겠습니까? 조직 목표와 개인 효율 사이에서 어떤 기준으로 판단하실 건가요?`,
        generationReason: `현재 지원 상태는 ${applyStatus}이고, 문서 요약(${snippet}) 기준으로 가치관과 실제 업무 압박 상황에서의 대응 방식을 함께 검증해야 합니다.`,
        expectedAnswer: "공동 목표를 인정하면서도 본인의 업무 우선순위 조정, 효율 개선, 마감 이후 회복과 보상 방식까지 균형 있게 설명하는 답변이 적절합니다.",
        followUpQuestions: [
          "같은 상황이 반복된다면 팀장과 어떤 방식으로 개선 대화를 시도하시겠습니까?",
          "개인 컨디션이 이미 한계에 가까운 상태라면 어떤 기준으로 선을 정하실 건가요?",
        ],
        evaluationGuide: {
          high: "조직 목표를 인정하면서도 개인 효율과 지속 가능성을 함께 고려한 현실적 대안을 제시한다.",
          medium: "상황에 순응은 하지만 능동적인 기여 전략이나 커뮤니케이션 기준이 부족하다.",
          low: "개인 권리만 강조하거나 반대로 무조건 희생하는 식으로 극단적인 태도를 보인다.",
        },
      },
      {
        id: "culture-fit",
        category: "조직 및 문화 적합성",
        question: `예상보다 훨씬 촉박한 일정 때문에 ${name}님이 원래 중요하게 생각하던 업무 원칙을 일부 포기해야 하는 상황이라면, 어떤 기준으로 타협하고 어떤 선은 끝까지 지키시겠습니까?`,
        generationReason: `${targetJobLabel} 역할에서는 일정 압박과 품질 사이의 타협이 자주 발생할 수 있어, 실제 업무 문화 적응력을 확인하려는 질문입니다.`,
        expectedAnswer: "팀 성과를 위해 조정 가능한 부분과 절대 포기하면 안 되는 기준을 분리해서 설명하고, 그 기준을 팀과 어떻게 공유할지 말하는 답변이 바람직합니다.",
        followUpQuestions: [
          "팀의 압박과 본인 기준이 충돌할 때 최종 의사결정은 누구와 어떻게 맞추시겠습니까?",
          "타협한 뒤 품질 리스크를 줄이기 위해 어떤 후속 조치를 하시겠습니까?",
        ],
        evaluationGuide: {
          high: "타협 기준과 비타협 기준을 분명히 나누고 팀과 소통하는 방식을 구체적으로 제시한다.",
          medium: "조직에 맞추려는 의지는 있으나 본인 기준과 팀 기준 정리가 모호하다.",
          low: "갈등 상황에서 기준 없이 흔들리거나 일방적으로 거부한다.",
        },
      },
    ],
    "problem-solving": [
      {
        id: "problem-solving",
        category: "문제 해결 및 논리 사고력",
        question: `${targetJobLabel} 업무를 맡은 상태에서 오픈 직전 치명적인 장애가 발생했고, 원인도 불명확하며 바로 의사결정을 내려야 하는 상황이라면 1시간 안에 무엇부터 하시겠습니까? 복구와 원인 분석의 우선순위를 어떻게 나누실 건가요?`,
        generationReason: `현재 세션 난이도는 ${difficulty}이며, 제한된 시간과 정보 속에서 생존형 문제 해결 능력을 확인할 필요가 있습니다.`,
        expectedAnswer: "패닉보다 우선순위 판단이 보여야 하며, 롤백과 임시 우회, 영향 범위 파악, 장애 공지 등 비즈니스 피해를 줄이는 행동을 먼저 정의하는 답변이 좋습니다.",
        followUpQuestions: [
          "원인을 끝내 못 찾은 채 서비스만 복구했다면 이후 후속 조치는 어떻게 설계하시겠습니까?",
          "사수나 동료와 연락이 닿는 순간 가장 먼저 어떤 정보를 공유하시겠습니까?",
        ],
        evaluationGuide: {
          high: "복구 우선 전략과 원인 분석을 구분하고, 피해 최소화 기준을 분명하게 설명한다.",
          medium: "책임감 있게 해결하려 하지만 복구보다 코드 수정 자체에 과도하게 매달릴 가능성이 보인다.",
          low: "상황 탓을 하거나 타인의 지시가 없으면 움직이지 못하는 태도를 보인다.",
        },
      },
      {
        id: "problem-solving",
        category: "문제 해결 및 논리 사고력",
        question: `${name}님이 맡은 기능에서 장애 원인은 여러 곳이 의심되는데 시간은 30분밖에 없고 로그도 충분하지 않다면, 어디부터 의심하고 어떤 기준으로 확인 순서를 정하시겠습니까?`,
        generationReason: `${targetJobLabel} 실무에서는 완벽한 정보 없이도 빠른 판단이 필요합니다. 문서 기반 경험을 실제 장애 대응 시나리오로 전환한 질문입니다.`,
        expectedAnswer: "사용자 영향 범위가 큰 부분부터 확인하고, 최근 변경점과 재현 가능성, 롤백 여부를 기준으로 좁혀가는 구조적 접근을 설명해야 합니다.",
        followUpQuestions: [
          "로그가 부족한 상태에서 임시로 어떤 관측 포인트를 추가하시겠습니까?",
          "원인 후보가 2개 이상일 때 팀 내 의사결정을 어떻게 끌고 가시겠습니까?",
        ],
        evaluationGuide: {
          high: "제한된 정보에서도 영향도와 가능성을 기준으로 우선순위를 세운다.",
          medium: "문제를 풀려는 의지는 있으나 확인 순서와 기준이 다소 감에 의존한다.",
          low: "막연한 추측만 반복하거나 시간 관리 없이 한 지점에만 매달린다.",
        },
      },
    ],
    "self-driven": [
      {
        id: "self-driven",
        category: "자기 주도적 성장 가능성",
        question: `${name}님이 다음 주부터 한 번도 써본 적 없는 프레임워크로 ${targetJobLabel} 관련 기능을 개발해야 한다면, 교육 지원 없이 주말과 퇴근 후 시간을 어떻게 활용해서 월요일 아침 바로 코드를 짤 수 있는 상태를 만들겠습니까?`,
        generationReason: `${name}님의 지원 문서와 직무 매칭을 기준으로, 회사 지원이 부족한 환경에서도 실무 적응 속도를 끌어올릴 수 있는지 검증하려는 질문입니다.`,
        expectedAnswer: "공식 문서 파악, 최소 실행 예제 작성, 오픈소스 레퍼런스 분석, 필수 개념 압축 학습, 실제 기능 단위의 작은 프로토타입 작성 같은 구체적인 루틴이 필요합니다.",
        followUpQuestions: [
          "학습한 내용을 월요일 오전 실제 업무 코드에 붙일 때 가장 먼저 만드는 산출물은 무엇인가요?",
          "주말 학습만으로도 막히는 부분이 생기면 어떤 채널로 빠르게 해결하실 건가요?",
        ],
        evaluationGuide: {
          high: "짧은 시간 안에 실무 가능한 수준으로 도달하는 본인만의 학습 루틴과 실행 순서가 명확하다.",
          medium: "열심히 하겠다는 의지는 있으나 어떤 자료를 어떤 순서로 볼지 구체성이 부족하다.",
          low: "회사 교육이나 타인의 도움 없이는 시작하기 어렵다는 태도를 보인다.",
        },
      },
      {
        id: "self-driven",
        category: "자기 주도적 성장 가능성",
        question: `${targetJobLabel} 포지션 업무에 바로 투입돼야 하는데 현재 경험이 부족한 영역이 분명하다면, ${name}님은 첫 3일 동안 무엇을 학습하고 어떤 기준으로 '실무 투입 가능' 상태를 판단하시겠습니까?`,
        generationReason: `지원자의 문서와 현재 세션 난이도(${difficulty})를 고려할 때, 빠른 적응력과 자기 주도 학습 루틴을 함께 확인하기 위한 질문입니다.`,
        expectedAnswer: "필수 개념 정리, 기존 코드베이스 구조 파악, 작은 단위 기능 재현, 업무와 직접 연결된 실습 우선 순서가 드러나는 답변이 기대됩니다.",
        followUpQuestions: [
          "학습 범위가 너무 넓을 때 버릴 것과 먼저 볼 것을 어떻게 정하시겠습니까?",
          "실무 투입 전에 반드시 검증하고 싶은 최소 역량은 무엇인가요?",
        ],
        evaluationGuide: {
          high: "학습 범위를 스스로 좁히고 실무와 연결되는 최소 역량 기준을 세운다.",
          medium: "성실히 공부할 의지는 있으나 실무 우선순위 구분이 약하다.",
          low: "배워가면서 하겠다는 태도만 있고 준비 전략이 거의 없다.",
        },
      },
    ],
    communication: [
      {
        id: "communication",
        category: "커뮤니케이션 및 협업 역량",
        question: `옆 팀 동료가 ${name}님의 코드에 대해 무례하게 전면 수정을 요구했지만, 기술적으로는 그 지적이 맞는 상황이라면 일정 압박 속에서 어떻게 대응하시겠습니까? 감정과 일의 우선순위를 어떻게 분리하실 건가요?`,
        generationReason: `문서 맥락(${snippet})과 ${targetJobLabel} 협업 환경을 고려할 때, 갈등 상황에서 실무를 끝까지 되게 만드는 소통 방식을 확인해야 합니다.`,
        expectedAnswer: "감정적 반응보다 기술적 타당성을 먼저 수용하고, 당장 필요한 수정 범위를 빠르게 정리한 뒤, 이후 적절한 시점에 소통 방식에 대한 피드백을 분리해서 전달하는 접근이 좋습니다.",
        followUpQuestions: [
          "상대방의 태도가 반복된다면 업무 관계를 해치지 않으면서 어떤 경계 설정을 하시겠습니까?",
          "당장 수정 일정이 촉박할 때 우선 합의해야 할 핵심 포인트는 무엇인가요?",
        ],
        evaluationGuide: {
          high: "감정과 업무를 분리하고 기술적 타당성을 우선 반영한 뒤, 관계 회복까지 고려한다.",
          medium: "문제는 해결하지만 감정을 누르기만 해서 후속 협업 리스크가 남을 수 있다.",
          low: "자존심 문제로 논쟁을 키우거나 필요한 수정을 거부해 더 큰 리스크를 만든다.",
        },
      },
      {
        id: "communication",
        category: "커뮤니케이션 및 협업 역량",
        question: `${targetJobLabel} 업무를 진행하는 중 기획자나 동료가 말도 안 되는 요구를 강하게 밀어붙이지만, 관계를 깨지 않고 일은 되게 만들어야 한다면 ${name}님은 어떤 순서로 소통하시겠습니까?`,
        generationReason: `${targetJobLabel} 포지션은 요구사항 충돌과 일정 압박이 잦을 수 있어, 정치적이면서도 실무적인 협업 대응력을 확인하려는 질문입니다.`,
        expectedAnswer: "요구를 감정적으로 반박하기보다 리스크와 영향 범위를 구조화해서 설명하고, 가능한 대안과 우선순위를 제시해 합의점을 찾는 답변이 바람직합니다.",
        followUpQuestions: [
          "상대가 끝까지 비합리적인 요구를 고수하면 누구를 어떤 근거로 설득하시겠습니까?",
          "관계를 망치지 않으면서도 반드시 거절해야 하는 요구는 어떻게 표현하시겠습니까?",
        ],
        evaluationGuide: {
          high: "상대의 체면을 살리면서도 리스크와 대안을 명확히 제시해 합의를 끌어낸다.",
          medium: "문제 해결은 시도하지만 논리 전달력이나 완충 방식이 다소 약하다.",
          low: "감정 대립으로 번지거나, 반대로 비합리적 요구를 그대로 수용해 문제를 키운다.",
        },
      },
    ],
  };
}

function buildInitialQuestions(context: CandidateContext): InterviewQuestionCardItem[] {
  const variants = buildQuestionVariants(context);
  return [
    variants["hard-skill"][0],
    variants["culture-fit"][0],
    variants["problem-solving"][0],
    variants["self-driven"][0],
    variants.communication[0],
  ];
}

function SummaryPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white/80 px-4 py-4">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
        {label}
      </div>
      <div className="mt-2 text-base font-bold text-[var(--text)]">{value}</div>
    </div>
  );
}

export function InterviewSessionDetailModal({
  open,
  detail,
  isLoading,
  isSaving,
  onClose,
  onDelete,
  onTriggerQuestionGeneration,
}: InterviewSessionDetailModalProps) {
  const context = useMemo(() => {
    if (!detail) {
      return null;
    }
    return extractCandidateContext(detail);
  }, [detail]);

  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);
  const [questions, setQuestions] = useState<InterviewQuestionCardItem[]>([]);
  const [variantIndexes, setVariantIndexes] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!open || !context) {
      setSelectedQuestionIds([]);
      setQuestions([]);
      setVariantIndexes({});
      return;
    }

    const initialQuestions = buildInitialQuestions(context);
    setQuestions(initialQuestions);
    setSelectedQuestionIds([]);
    setVariantIndexes({
      "hard-skill": 0,
      "culture-fit": 0,
      "problem-solving": 0,
      "self-driven": 0,
      communication: 0,
    });
  }, [open, context]);

  if (!open) {
    return null;
  }

  const toggleQuestion = (questionId: string) => {
    setSelectedQuestionIds((current) =>
      current.includes(questionId)
        ? current.filter((id) => id !== questionId)
        : [...current, questionId],
    );
  };

  const handleRegenerateQuestions = () => {
    if (!detail || !context || selectedQuestionIds.length === 0) {
      return;
    }

    const variants = buildQuestionVariants(context);

    setQuestions((currentQuestions) =>
      currentQuestions.map((question) => {
        if (!selectedQuestionIds.includes(question.id)) {
          return question;
        }

        const nextIndex =
          ((variantIndexes[question.id] ?? 0) + 1) % variants[question.id].length;
        return variants[question.id][nextIndex];
      }),
    );

    setVariantIndexes((current) => {
      const next = { ...current };
      selectedQuestionIds.forEach((questionId) => {
        next[questionId] =
          ((current[questionId] ?? 0) + 1) %
          buildQuestionVariants(context)[questionId].length;
      });
      return next;
    });

    void onTriggerQuestionGeneration(detail.id);
  };

  const handleConfirmQuestions = () => {
    window.alert("질문이 확정되었습니다.");
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[95] flex items-center justify-center overflow-hidden bg-slate-950/45 p-2 backdrop-blur-sm sm:p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="flex h-[92dvh] max-h-[92dvh] w-full max-w-6xl min-w-0 flex-col overflow-hidden rounded-[24px] border border-white/70 bg-[var(--panel)] shadow-[0_40px_120px_rgba(15,23,42,0.25)] sm:rounded-[34px]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-[var(--line)] px-4 py-4 sm:px-7 sm:py-6">
          <div className="min-w-0">
            <div className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
              Interview Session Brief
            </div>
            <h2 className="mt-2 truncate text-xl font-bold text-[var(--text)] sm:text-3xl">
              {detail ? `${detail.candidateName}님의 면접 세션` : "면접 세션"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              마음에 들지 않는 질문만 체크해서 다시 생성하고, 최종 질문을 확정할 수 있습니다.
            </p>
          </div>

          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--line)] bg-white/80 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
            onClick={onClose}
            aria-label="닫기"
            disabled={isSaving}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-16 text-center text-sm text-[var(--muted)] sm:px-7">
            세션 상세 정보를 불러오는 중입니다...
          </div>
        ) : null}

        {detail && context ? (
          <>
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
            <div className="grid gap-3 border-b border-[var(--line)] px-4 py-4 sm:px-7 sm:py-5 md:grid-cols-4">
              <SummaryPill label="세션" value={`#${detail.id}`} />
              <SummaryPill label="목표 직무" value={context.targetJobLabel} />
              <SummaryPill label="난이도" value={context.difficulty} />
              <SummaryPill label="문서 수" value={String(context.documentCount)} />
            </div>

            <InterviewSessionQuestionGenerationView sessionId={detail.id} compact />

            <InterviewSessionAssembledPayloadView detail={detail} compact />

            <div className="border-b border-[var(--line)] px-4 py-5 sm:px-7">
              <div className="mb-3 flex items-center gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                  <UserRound className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text)]">지원자 요약</h3>
                  <p className="text-sm text-[var(--muted)]">
                    모달 상단에서 핵심 지원자 정보를 가로형으로 바로 확인합니다.
                  </p>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-4">
                <SummaryPill label="이름" value={context.name} />
                <SummaryPill label="지원 직무" value={context.jobPositionLabel} />
                <SummaryPill label="지원 상태" value={context.applyStatus} />
                <SummaryPill label="연락처" value={context.phone} />
              </div>
            </div>

            <div className="px-4 py-5 sm:px-7 sm:py-6">
              <div className="space-y-5">
                {questions.map((item, index) => {
                  const isSelected = selectedQuestionIds.includes(item.id);

                  return (
                    <article
                      key={`${item.id}-${index}-${item.question}`}
                      className="min-w-0 rounded-[24px] border-2 border-[color:var(--line)] bg-white/90 shadow-[0_20px_48px_rgba(15,23,42,0.08)] sm:rounded-[28px]"
                    >
                      <button
                        type="button"
                        className="flex w-full items-start gap-4 rounded-t-[26px] px-5 py-5 text-left"
                        onClick={() => toggleQuestion(item.id)}
                      >
                        <span className="mt-0.5 text-[var(--primary)]">
                          {isSelected ? (
                            <CheckSquare className="h-7 w-7" />
                          ) : (
                            <Square className="h-7 w-7" />
                          )}
                        </span>
                        <div className="min-w-0">
                          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                            {item.category}
                          </div>
                          <h3 className="mt-2 break-words text-lg font-bold leading-7 text-[var(--text)] [overflow-wrap:anywhere] sm:text-[1.35rem] sm:leading-8 lg:text-[1.65rem] lg:leading-9">
                            {index + 1}. {item.question}
                          </h3>
                        </div>
                      </button>

                      <div className="border-t border-slate-200 px-6 py-5">
                        <div className="space-y-4 break-words text-base leading-7 text-[var(--text)] [overflow-wrap:anywhere] sm:text-[1.08rem] sm:leading-8 lg:text-[1.18rem] lg:leading-9">
                          <div>
                            <span className="font-extrabold">💡 생성 근거:</span>{" "}
                            {item.generationReason}
                          </div>
                          <div>
                            <span className="font-extrabold">✅ 예상 답변:</span>{" "}
                            {item.expectedAnswer}
                          </div>
                          <div>
                            <span className="font-extrabold">🔎 꼬리 질문:</span>
                            <div className="mt-1 pl-8">
                              {item.followUpQuestions.map((question, followUpIndex) => (
                                <div key={question}>
                                  {followUpIndex + 1}. {question}
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <span className="font-extrabold">📋 평가 가이드:</span>
                            <div className="mt-1 pl-8">
                              <div>[상] {item.evaluationGuide.high}</div>
                              <div>[중] {item.evaluationGuide.medium}</div>
                              <div>[하] {item.evaluationGuide.low}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
            </div>

            <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] bg-[var(--panel)] px-4 py-4 sm:px-7 sm:py-5">
              <button
                type="button"
                className="inline-flex h-11 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 px-4 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => onDelete(detail.id, detail.candidateName)}
                disabled={isSaving}
              >
                세션 삭제
              </button>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-5 text-sm font-semibold text-[var(--text)] transition hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={handleRegenerateQuestions}
                  disabled={isSaving || selectedQuestionIds.length === 0}
                >
                  <RefreshCcw className="h-4 w-4" />
                  질문 재생성
                </button>
                <button
                  type="button"
                  className="inline-flex h-11 items-center justify-center rounded-2xl bg-linear-to-r from-[var(--primary)] to-[var(--primary-strong)] px-5 text-sm font-semibold text-white shadow-[0_18px_36px_color-mix(in_srgb,var(--primary)_24%,transparent)] transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={handleConfirmQuestions}
                  disabled={isSaving}
                >
                  질문 확정
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
