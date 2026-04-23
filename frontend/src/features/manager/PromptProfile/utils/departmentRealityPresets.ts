import type { DepartmentRealityCustomItem, DepartmentRealityQuestionId } from "../types";

export interface DepartmentRealityPresetOption {
  id: string;
  label: string;
}

export interface DepartmentRealityQuestionDef {
  id: DepartmentRealityQuestionId;
  title: string;
  presets: DepartmentRealityPresetOption[];
}

export const DEPARTMENT_REALITY_QUESTIONS: DepartmentRealityQuestionDef[] = [
  {
    id: "q1",
    title: "Q1. 업무 강도 및 마감 대응 (야근 빈도)",
    presets: [
      {
        id: "q1-worklife",
        label: "워라밸 지향: 업무 시간 내 효율을 중시하며 야근은 거의 없음.",
      },
      {
        id: "q1-flex-deadline",
        label: "유동적 대응: 평소엔 자유로우나 마감 전 1~2주간 집중 야근 발생.",
      },
      {
        id: "q1-immersion",
        label: "몰입 중심: 상시 업무 강도가 높으며, 마감을 위해 주말/야근 동참이 필수적임.",
      },
    ],
  },
  {
    id: "q2",
    title: "Q2. 교육 환경 및 자생력 (사수 유무)",
    presets: [
      {
        id: "q2-education",
        label: "교육 중심: 체계적인 온보딩과 전담 사수의 밀착 가이드가 있음.",
      },
      {
        id: "q2-hands-on",
        label: "실전 투입: 가이드는 주어지나 업무량이 많아 스스로 해결해야 함.",
      },
      {
        id: "q2-jungle",
        label: "정글 생존: 사수 없음. 입사 즉시 독학으로 결과물을 내야 하며 물어볼 곳이 없음.",
      },
    ],
  },
  {
    id: "q3",
    title: "Q3. 의사결정 수용성 (복종도)",
    presets: [
      {
        id: "q3-horizontal",
        label: "수평적 토론: 개인의 기술적 소신과 비판적 사고를 적극 장려함.",
      },
      {
        id: "q3-consensus",
        label: "합의 후 실행: 토론은 하되, 결정된 사항에 대해서는 빠르게 실행함.",
      },
      {
        id: "q3-topdown",
        label: "상명하복: 결정된 사항에 토 달지 않고 속도감 있게 완수하는 능력이 최우선임.",
      },
    ],
  },
  {
    id: "q4",
    title: "Q4. 직무 유연성 (잡무 비중)",
    presets: [
      {
        id: "q4-specialist",
        label: "전문성 집중: 개발 업무 외의 타 직군 업무는 거의 발생하지 않음.",
      },
      {
        id: "q4-adjacent",
        label: "유연한 협업: 기획 수정, 운영 툴 관리 등 인접 직군 업무를 일부 병행함.",
      },
      {
        id: "q4-allrounder",
        label: "올라운더: 직무 구분 없이 회사에 필요한 일(청소, 기획, 운영 등)이면 뭐든 해야 함.",
      },
    ],
  },
];

const PRESET_LABEL_BY_ID = new Map<string, string>();
for (const q of DEPARTMENT_REALITY_QUESTIONS) {
  for (const p of q.presets) {
    PRESET_LABEL_BY_ID.set(p.id, p.label);
  }
}

export function resolveDepartmentRealityLabel(
  optionId: string,
  customItems: DepartmentRealityCustomItem[],
): string | null {
  const preset = PRESET_LABEL_BY_ID.get(optionId);
  if (preset) {
    return preset;
  }
  const custom = customItems.find((c) => c.id === optionId);
  if (custom?.text.trim()) {
    return custom.text.trim();
  }
  return null;
}
