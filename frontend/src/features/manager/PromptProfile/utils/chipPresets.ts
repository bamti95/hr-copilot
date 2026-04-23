import type { CandidateJobPosition } from "../../Candidate/types";

/** AI·개발·데이터 직무 — 필수·우대 기술 스택 제안 (표시는 # 접두). */
export const SKILL_STACK_SUGGESTIONS = [
  "Python",
  "FastAPI",
  "Django",
  "PostgreSQL",
  "MySQL",
  "Redis",
  "Docker",
  "Kubernetes",
  "AWS",
  "TypeScript",
  "React",
  "Vue.js",
  "Java",
  "Spring Boot",
  "Go",
];

export const CERTIFICATE_SUGGESTIONS = [
  "정보처리기사",
  "SQLD",
  "AWS SAA",
  "CKA",
  "OCP",
];

export const EDUCATION_SUGGESTIONS = [
  "학사 이상",
  "석사 이상",
  "관련 전공",
  "CS 전공",
];

export interface PromptProfileChipSuggestions {
  mustHaveStack: string[];
  niceToHaveStack: string[];
  certificates: string[];
}

const AI_DEV_DATA_PRESET: PromptProfileChipSuggestions = {
  mustHaveStack: SKILL_STACK_SUGGESTIONS,
  niceToHaveStack: SKILL_STACK_SUGGESTIONS,
  certificates: CERTIFICATE_SUGGESTIONS,
};

const HR_PRESET: PromptProfileChipSuggestions = {
  mustHaveStack: [
    "HR 기본 이해",
    "노동법",
    "인사 규정",
    "Excel",
    "Notion",
    "Slack",
    "Google Workspace",
  ],
  niceToHaveStack: ["SQL", "Python"],
  certificates: [
    "직업상담사",
    "공인노무사",
    "컴퓨터활용능력 1/2급",
    "SQLD",
    "경영지도사",
    "ERP 인사 1급",
    "HRM 전문가",
    "PHR",
    "SPHR",
  ],
};

const STRATEGY_PLANNING_PRESET: PromptProfileChipSuggestions = {
  mustHaveStack: ["Excel", "PPT", "VBA"],
  niceToHaveStack: ["Tableau", "Power BI", "SQL", "Python"],
  certificates: [
    "컴퓨터활용능력 1급",
    "ADsP",
    "SQLD",
    "사회조사분석사 2급",
    "AICPA",
    "CFA",
  ],
};

const MARKETING_PRESET: PromptProfileChipSuggestions = {
  mustHaveStack: [
    "콘텐츠 기획",
    "브랜딩",
    "광고 성과 분석",
    "상품 소싱",
    "상품 기획",
    "매출 분석",
    "재고 관리",
    "가격 전략",
  ],
  niceToHaveStack: ["SQL", "Python", "Tableau", "Power BI", "Photoshop", "Figma"],
  certificates: [
    "ADsP",
    "SQLD",
    "검색광고마케터 1급",
    "사회조사분석사 2급",
    "유통관리사 2급",
    "컴퓨터활용능력 1급",
  ],
};

const SALES_PRESET: PromptProfileChipSuggestions = {
  mustHaveStack: [
    "Slack",
    "Zoom",
    "Google Workspace",
    "Excel",
    "PPT",
    "비즈니스 이해",
  ],
  niceToHaveStack: [
    "Salesforce",
    "HubSpot",
    "B2B 솔루션 이해도",
    "데이터 시각화",
  ],
  certificates: [
    "자동차 운전면허 (1종/2종)",
    "컴퓨터활용능력 1/2급",
    "공인어학성적",
    "금융/보험 영업",
    "유통/무역 영업",
    "기술 영업",
  ],
};

const PRESETS_BY_JOB: Record<CandidateJobPosition, PromptProfileChipSuggestions> = {
  AI_DEV_DATA: AI_DEV_DATA_PRESET,
  HR: HR_PRESET,
  STRATEGY_PLANNING: STRATEGY_PLANNING_PRESET,
  MARKETING: MARKETING_PRESET,
  SALES: SALES_PRESET,
};

/**
 * 채용 직무에 맞는 칩 제안. 직무 미선택·알 수 없는 값이면 AI·개발·데이터 기본과 동일.
 */
export function getPromptProfileChipSuggestions(targetJob: string): PromptProfileChipSuggestions {
  const key = targetJob.trim() as CandidateJobPosition;
  if (!key || !(key in PRESETS_BY_JOB)) {
    return AI_DEV_DATA_PRESET;
  }
  return PRESETS_BY_JOB[key];
}
