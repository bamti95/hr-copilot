import type { DocumentResponse } from "../../features/manager/Document/types";
import type { InterviewQuestionResponse } from "../../features/manager/InterviewQuestion/types";

export const managerNavItems = [
  { label: "대시보드", path: "/manager/dashboard", icon: "◈" },
  { label: "관리자 관리", path: "/manager/managers", icon: "◎" },
  { label: "지원자 관리", path: "/manager/candidates", icon: "◌" },
  { label: "프롬프트 프로필 관리", path: "/manager/prompt-profiles", icon: "◇" },
  { label: "면접 세션 관리", path: "/manager/interview-sessions", icon: "△" },
];

export const documentList: DocumentResponse[] = [
  { id: 201, title: "Jane Cooper Resume.pdf", documentType: "RESUME", candidateName: "Jane Cooper", extractStatus: "COMPLETED", uploadedAt: "2026-04-16 08:00" },
  { id: 202, title: "Floyd Miles Portfolio.pdf", documentType: "PORTFOLIO", candidateName: "Floyd Miles", extractStatus: "PROCESSING", uploadedAt: "2026-04-16 08:12" },
  { id: 203, title: "Ronald Richards CoverLetter.pdf", documentType: "COVER_LETTER", candidateName: "Ronald Richards", extractStatus: "FAILED", uploadedAt: "2026-04-15 17:20" },
  { id: 204, title: "Marvin McKinney Resume.pdf", documentType: "RESUME", candidateName: "Marvin McKinney", extractStatus: "COMPLETED", uploadedAt: "2026-04-15 15:44" },
  { id: 205, title: "Jerome Bell Resume.pdf", documentType: "RESUME", candidateName: "Jerome Bell", extractStatus: "PENDING", uploadedAt: "2026-04-15 14:31" },
];

export const interviewQuestionList: InterviewQuestionResponse[] = [
  { id: 501, category: "Technical", questionText: "React Suspense 도입 시 데이터 패칭 전략을 설명해 주세요.", expectedAnswer: "fallback, streaming, cache, boundary", priority: "P1" },
  { id: 502, category: "Behavioral", questionText: "실패한 채용 운영 프로젝트를 복구했던 경험을 말해 주세요.", expectedAnswer: "context, action, measurable result", priority: "P2" },
  { id: 503, category: "Rationale", questionText: "이 질문이 JD와 어떤 연결점이 있는지 설명해 주세요.", expectedAnswer: "JD skill alignment", priority: "P1" },
  { id: 504, category: "Follow-up", questionText: "답변 검증을 위해 어떤 꼬리 질문을 던질 건가요?", expectedAnswer: "evidence-based follow-up", priority: "P3" },
];
