import { getJobPositionLabel } from "../../common/candidateJobPosition";
import type { PromptProfileFormState } from "../types";
import { DEPARTMENT_REALITY_QUESTIONS, resolveDepartmentRealityLabel } from "./departmentRealityPresets";

function formatList(items: string[], emptyLabel: string) {
  if (items.length === 0) {
    return emptyLabel;
  }
  return items.map((s) => s.trim()).filter(Boolean).join(", ");
}

/**
 * AI 채용 에이전트 설정 폼 값을 하나의 시스템 프롬프트 문자열로 합성합니다.
 */
export function buildAgentSystemPrompt(form: PromptProfileFormState): string {
  const must = form.mustHaveStack.map((s) => s.trim()).filter(Boolean);
  const nice = form.niceToHaveStack.map((s) => s.trim()).filter(Boolean);
  const certs = form.requiredCertificates.map((s) => s.trim()).filter(Boolean);
  const edu = form.requiredEducation.map((s) => s.trim()).filter(Boolean);
  const agentName = form.agentName.trim();
  const department = form.department.trim();
  const jobLine = form.targetJob
    ? getJobPositionLabel(form.targetJob)
    : "";

  const deptReality = form.departmentReality;
  const realityBlocks = DEPARTMENT_REALITY_QUESTIONS.map((q) => {
    const block = deptReality[q.id];
    const lines = block.selectedIds
      .map((oid) => resolveDepartmentRealityLabel(oid, block.customItems))
      .filter((s): s is string => Boolean(s));
    const body =
      lines.length > 0
        ? lines.map((line) => `  - ${line}`).join("\n")
        : "  - (해당 없음 또는 미선택)";
    return `### ${q.title}\n${body}`;
  }).join("\n\n");

  return `당신은 기업 채용을 지원하는 AI 에이전트입니다. 아래에 정리된 조직·직무·기술·자격 맥락을 반드시 존중하고, 면접 질문 설계·지원자 서류·역량 평가 보조·HR 커뮤니케이션 초안 등에 활용합니다. 입력되지 않은 항목은 과장하지 말고, 주어진 사실 범위 안에서만 응답하세요.

## 1. 기본 정보 (Basic Information)
- 에이전트 명칭: ${agentName || "(미입력)"}
- 채용 부서: ${department || "(미입력)"}
- 채용 직무: ${jobLine || "(미입력)"}

## 2. 기술 및 자격 요건 (Technical Requirements)
- 필수 기술 스택 (Must-have): ${formatList(must, "(미입력)")}
- 우대 기술 스택 (Nice-to-have): ${formatList(nice, "(해당 없음 또는 미입력)")}
- 필수 자격증: ${formatList(certs, "(미입력)")}
- 필수 학력: ${formatList(edu, "(미입력)")}

## 3. 부서 실무 상황 설정 (Department Reality - Internal Only)
(내부 운영 맥락입니다. 지원자에게 그대로 노출하거나 면접에서 직접 인용하지 마세요.)

${realityBlocks}`;
}

export function validateAgentConfigForCreate(form: PromptProfileFormState): string | null {
  if (!form.profileKey.trim()) {
    return "프로필 키는 필수입니다.";
  }
  if (!form.agentName.trim()) {
    return "에이전트 명칭을 입력해 주세요.";
  }
  if (!form.department.trim()) {
    return "채용 부서를 입력해 주세요.";
  }
  if (!form.targetJob) {
    return "채용 직무를 선택해 주세요.";
  }
  if (form.mustHaveStack.filter((s) => s.trim()).length === 0) {
    return "필수 기술 스택을 한 가지 이상 선택하거나 추가해 주세요.";
  }
  return null;
}
