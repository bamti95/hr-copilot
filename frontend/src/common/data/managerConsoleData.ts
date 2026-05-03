import type {
  DashboardActivity,
  DashboardMetric,
} from "../../features/manager/Dashboard/types";
import type { CandidateResponse } from "../../features/manager/Candidate/types";
import type { DocumentResponse } from "../../features/manager/Document/types";
import type { InterviewQuestionResponse } from "../../features/manager/InterviewQuestion/types";
import type { OpsLogResponse } from "../../features/manager/OpsLog/types";

export const managerNavItems = [
  { label: "대시보드", path: "/manager/dashboard", icon: "◈" },
  { label: "관리자 관리", path: "/manager/managers", icon: "◎" },
  { label: "지원자 관리", path: "/manager/candidates", icon: "◌" },
  { label: "프롬프트 프로필 관리", path: "/manager/prompt-profiles", icon: "◇" },
  { label: "면접 세션 관리", path: "/manager/interview-sessions", icon: "△" },
];

export const dashboardMetrics: DashboardMetric[] = [
  { id: "managers", label: "Active Managers", value: 18, hint: "권한 운영 중", icon: "◎" },
  { id: "candidates", label: "Candidates", value: 5423, hint: "이번 달 +164", icon: "◌" },
  { id: "sessions", label: "Interview Sessions", value: 1893, hint: "생성 완료", icon: "△" },
  { id: "documents", label: "Documents Parsed", value: 8721, hint: "OCR 파이프라인", icon: "▣" },
];

export const dashboardActivities: DashboardActivity[] = [
  { id: 1, title: "채용 운영 매니저 신규 생성", owner: "Platform Admin", status: "ACTIVE", dueDate: "2026-04-16" },
  { id: 2, title: "백오피스 지원자 OCR 배치 검수", owner: "Ops Lead", status: "PROCESSING", dueDate: "2026-04-17" },
  { id: 3, title: "프롬프트 프로파일 업데이트", owner: "AI PM", status: "REVIEW", dueDate: "2026-04-18" },
];


export const candidateList: CandidateResponse[] = [
  { id: 101, name: "Jane Cooper", email: "jane@sample.com", phone: "010-2012-1111", applyStatus: "ACTIVE", targetJob: "Frontend Engineer" },
  { id: 102, name: "Floyd Miles", email: "floyd@sample.com", phone: "010-2012-2222", applyStatus: "REVIEW", targetJob: "AI Product Manager" },
  { id: 103, name: "Ronald Richards", email: "ronald@sample.com", phone: "010-2012-3333", applyStatus: "PROCESSING", targetJob: "Backend Engineer" },
  { id: 104, name: "Marvin McKinney", email: "marvin@sample.com", phone: "010-2012-4444", applyStatus: "ACTIVE", targetJob: "Data Engineer" },
  { id: 105, name: "Jerome Bell", email: "jerome@sample.com", phone: "010-2012-5555", applyStatus: "REVIEW", targetJob: "HR Analyst" },
  { id: 106, name: "Kathryn Murphy", email: "kathryn@sample.com", phone: "010-2012-6666", applyStatus: "ACTIVE", targetJob: "Recruiter" },
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

export const opsLogList: OpsLogResponse[] = [
  { id: 601, modelName: "gpt-5.4-mini", candidateName: "Jane Cooper", totalTokens: 6120, costAmount: "$0.18", callStatus: "SUCCESS" },
  { id: 602, modelName: "gpt-5.4-mini", candidateName: "Floyd Miles", totalTokens: 8400, costAmount: "$0.25", callStatus: "SUCCESS" },
  { id: 603, modelName: "gpt-5.4", candidateName: "Ronald Richards", totalTokens: 11100, costAmount: "$0.64", callStatus: "ERROR" },
  { id: 604, modelName: "gpt-5.4", candidateName: "Kathryn Murphy", totalTokens: 4900, costAmount: "$0.16", callStatus: "SUCCESS" },
];
