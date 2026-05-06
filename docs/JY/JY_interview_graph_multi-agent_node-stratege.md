## 개요

초기 구현 상태는 여러 에이전트가 순차적으로 협업하는 구조이며, 각 노드는 State에 저장된 질문 목록(questions)과 각 에이전트별 결과(answers, follow_ups, reviews, scores)를 공유하면서 자신의 역할만 수행합니다.

**핵심 전략:**
하나의 에이전트가 모든 일을 처리하는 방식이 아니라, 다음 단계들을 역할 별로 분리한 멀티 에이전트 입니다.

```
문맥 준비 → 문서 분석 → 질문 생성 → 답변 예측 → 꼬리질문 생성 → 품질 검토 → 채점 → 선별 → 최종 조립
```

---

## Agent 및 Node 구성

| 에이전트 / 노드 | 역할 | 주요 미션 |
| --- | --- | --- |
| **BuildState** (문맥 준비 노드) | 입력 문맥 정리 | 세션 정보, 지원자 정보, 문서 텍스트를 하나의 공통 문맥(candidate_context)으로 병합. 추출 텍스트가 없으면 메타데이터 중심으로 처리한다는 경고를 node_warnings에 기록 |
| **Analyzer** (문서 분석자) | 문서 분석 | candidate_context와 채용 기준을 바탕으로 강점, 약점, 리스크, 검증 포인트를 구조화해 document_analysis를 생성. 이후 모든 에이전트가 이 분석 결과를 공유 입력으로 사용 |
| **Questioner** (질문자) | 기초 질문 설계 | document_analysis 기반으로 핵심 질문과 평가 가이드 초안 생성. 질문 생성 근거(generation_basis)와 문서 근거(document_evidence)를 함께 기록. human_action 값에 따라 신규 생성 / 부분 재생성을 분기 처리 |
| **Predictor** (예측자) | 답변 시뮬레이션 | 지원자의 입장에서 가장 현실적인 예상 답변(predicted_answer)을 생성하고, 답변 신뢰도(answer_confidence)와 위험 포인트(answer_risk_points)를 함께 기록. 실패 시 fallback 답변으로 안전하게 처리 |
| **Driller** (추적자) | 꼬리 질문 생성 | 예상 답변의 빈틈, 역할 범위, 수치, 의사결정 지점을 파고드는 심층 꼬리질문(follow_up_question) 설계. 꼬리질문 목적(drill_type)도 함께 기록. 실패 시 fallback 꼬리질문으로 안전하게 처리 |
| **Reviewer** (검토자) | 품질 보증 (QA) | 채용 기준과 질문 품질 루브릭에 따라 각 질문을 검토하고 approved / needs_revision / rejected 판정 부여. 반려 사유(reject_reason)와 수정 제안(recommended_revision)도 함께 기록. 실패 시 fallback 리뷰로 처리 |
| **Scorer** (채점자) | 점수 산정 | 리뷰 판정, 문서 근거 존재 여부, 평가 가이드, 역량 태그, 꼬리질문 연결성, 중복 여부를 종합해 질문별 0~100점 품질 점수 계산. review_summary(승인 수, 저점수 ID 목록, 평균 점수, 품질 이슈 목록)를 생성해 라우터에 전달 |
| **Review Router** (분기 노드) | 재시도 여부 판단 | Scorer 결과(review_summary)를 보고 Driller 재시도 / Questioner 재시도 / Selector 진행 중 하나로 분기 결정 |
| **Selector** (선별자) | 최종 질문 선별 | 중복 질문 제거 후, 리뷰 승인 여부와 점수를 기준으로 정렬하여 리스크 질문을 우선 포함한 상위 5개 질문 선별 |
| **FinalFormatter** (최종 조립 노드) | 결과 조립 | 선별된 질문에 answers, follow_ups, reviews, scores를 매핑하고 QuestionGenerationResponse 스키마로 조립해 최종 응답 반환 |

---

## 전략적 특징

- **BuildState**는 질문을 만들지 않고, 뒤 노드들이 공통으로 참고할 입력 문맥을 정리하는 전처리 노드입니다.
- **Analyzer**는 문서 분석 전담으로, 이 결과(document_analysis)가 Questioner · Predictor · Driller · Reviewer 모두의 공통 입력이 됩니다.
- **Questioner**는 질문 생성만 담당하고, 답변 예측이나 품질 판정은 직접 하지 않습니다.
- **Predictor · Driller**는 실패 시 그래프를 중단하지 않고 fallback 값을 삽입하여 파이프라인 연속성을 보장합니다.
- **Scorer**는 LLM 호출 없이 규칙 기반(점수 베이스: approved=38, needs_revision=20, rejected=0)으로 품질 점수를 계산하고 라우터에 필요한 review_summary를 생성합니다.
- **Review Router**는 Reviewer가 아닌 Scorer 이후에 위치하며, FOLLOW_UP_TOO_WEAK 플래그는 Driller 재시도로, LOW_SCORE · REVIEW_NOT_APPROVED 등은 Questioner 재시도로 각각 분리 라우팅합니다.
- **Selector**는 중복 제거와 리스크 질문 우선 선발 로직을 수행하며, 최종 5개 질문으로 압축합니다.
- `questions`, `answers`, `follow_ups`, `reviews`, `scores`는 각 에이전트가 별도 리스트에 기록하고, `question_id`로 매핑합니다. 단일 QuestionSet 객체에 모든 필드를 임베드하는 방식을 사용하지 않습니다.
- 사람의 개입(더보기, 재생성, 추가 질문 등)은 LangGraph 내부가 아니라 **서비스 레이어**에서 처리합니다.
- **LangGraph**는 순수하게 AI 파이프라인만 담당하고, 사람과의 인터랙션은 프론트/백엔드가 결과를 받아 재호출하는 방식으로 구현합니다.
- JY 그래프는 서비스 레이어에서 `human_action`, `target_question_ids`, `additional_instruction`, `existing_questions`를 조립해 재호출하는 구조입니다.

---

## LangGraph 노드 구성 및 상태 관리

### 전체 워크플로우

```
START
  ↓
[1. Input Data]
  - 지원자 문서 목록 + 채용 기준용 프롬프트 프로필
  - 서비스 레이어에서 넘어온 재호출 파라미터 주입
  ↓
[2. State Initialization]
  - 에이전트 공유용 AgentState 초기화
  - 재호출 시: human_action, target_question_ids, existing_questions 복원
  ↓
[3. Multi-Agent Sequential Logic]
  ↓
Node 0: BuildState
  ↓
Agent 1: Analyzer (문서 분석자)
  ↓
Agent 2: Questioner (질문자)
  ↓
Agent 3: Predictor (예측자)
  ↓
Agent 4: Driller (추적자)
  ↓
Agent 5: Reviewer (검토자)
  ↓
Node 6: Scorer (채점자)
  ↓
[Review Router 분기]
  - FOLLOW_UP_TOO_WEAK → retry_driller → Driller
  - LOW_SCORE / REVIEW_NOT_APPROVED → retry_questioner → Questioner
  - 품질 이슈 없음 → Selector
  ↓
Node 7: Selector (선별자)
  ↓
Node 8: FinalFormatter (최종 조립 노드)
  ↓
FINISH
```

---

## 서비스 레이어 설계 (Human Interaction)

LangGraph는 실행이 끝나면 결과 JSON을 반환하고 종료합니다. 이후 사람의 액션(더보기, 재생성, 추가 질문 등)은 **서비스 레이어(프론트+백엔드)**가 결과를 받아 적절한 파라미터를 조립한 뒤 LangGraph를 재호출하는 방식으로 처리합니다.

### Human Interaction 플로우

```
[1. LangGraph 실행]
  ↓
결과 JSON 반환
  ↓
[2. 서비스 레이어]
  - 사람에게 결과 화면 노출
  ↓
[3. 사람이 액션 선택]
  - ① 더보기
  - ② 재생성 요청
  - ③ 추가 질문
  - ④ 종료 및 저장
  ↓
[4. 파라미터 조립]
  - human_action + target_question_ids
  - additional_instruction + existing_questions 조립
  ↓
피드백 반영 후 재실행 → [1. LangGraph 실행]
```

### 케이스별 재호출 파라미터 조립 방식

| 액션 | 서비스 레이어가 하는 일 | LangGraph에 넘기는 파라미터 |
| --- | --- | --- |
| ① 추천 질문 더보기 | 기존 결과 JSON을 유지하고 추가 생성만 요청 | `human_action: "more"` 또는 `"more_questions"`, 기존 questions 배열 그대로 주입 |
| ② 전체 재생성 | 모든 질문 초기화 후 처음부터 재실행 | `existing_questions` 비움, `human_action` 제거 후 재호출 |
| ② 개별 재생성 | 사용자가 선택한 질문만 재작성 대상으로 지정 | `target_question_ids`, `human_action: "regenerate_question"`, 기존 questions 주입. Questioner는 지정된 ID 수만큼만 생성 후 `_replace_questions_by_id`로 기존 목록에 병합 |
| ③ 추가 질문 생성 | 사용자가 입력한 지시사항을 기반으로 신규 질문 추가 | `human_action: "add_question"` 또는 유사 액션, `additional_instruction` 세팅, 기존 questions 유지 |

**핵심 원칙:**
LangGraph 자체를 바꾸는 것이 아니라, 서비스 레이어가 `human_action`과 보조 파라미터를 조립해서 재호출합니다. Questioner 에이전트는 이 값을 읽어 신규 생성 / 더보기 / 부분 재생성 / 추가 생성을 분기합니다.

---

## State 및 데이터 구조 정의

### 1. 에이전트별 출력 데이터 구조

JY 파이프라인은 단일 QuestionSet 객체에 모든 필드를 임베드하지 않고, 에이전트별 결과를 독립 리스트로 관리하며 `question_id`로 매핑합니다.

### Questioner가 작성하는 필드 (questions 리스트)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 ID | `id` | String | 질문 고유 ID. jy-q-001 형식으로 자동 부여. 부분 재생성, 리뷰 결과 매핑에 사용 |
| 질문 카테고리 | `category` | String | 질문 유형 분류 (TECH, EXPERIENCE, RISK 등) |
| 질문 본문 | `question_text` | String | 지원자 문서 내용을 기반으로 생성한 핵심 면접 질문 |
| 생성 근거 | `generation_basis` | String | 이 질문을 생성한 구체적 근거. 문서의 어느 문구/경험/수치를 보고 왜 생성했는지 기술 |
| 문서 근거 목록 | `document_evidence` | List[String] | 질문 생성에 사용한 핵심 문서 근거 목록. 존재 여부가 Scorer 점수(+20)에 영향 |
| 평가 가이드 | `evaluation_guide` | String | 답변 정답 여부가 아닌, 평가 의도 및 고득점/감점 기준. 존재 여부가 Scorer 점수(+12)에 영향 |
| 리스크 태그 | `risk_tags` | List[String] | 질문이 검증하려는 리스크 태그. 존재 시 Scorer 점수 +10 |
| 역량 태그 | `competency_tags` | List[String] | 질문이 검증하려는 역량 태그. 존재 여부가 Scorer 점수(+10)에 영향 |

### Predictor가 작성하는 필드 (answers 리스트)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 참조 ID | `question_id` | String | 대응하는 질문의 ID |
| 예측 답변 | `predicted_answer` | String | 해당 질문에 대해 지원자가 내놓을 것으로 예상되는 가상 답변 (2~3문장). 존재 여부가 Scorer 점수(+5)에 영향 |
| 예측 답변 근거 | `predicted_answer_basis` | String | 왜 그 답변이 나올 가능성이 높은지에 대한 짧은 근거 |
| 답변 신뢰도 | `answer_confidence` | String | 예상 답변의 신뢰도 (low, medium, high) |
| 답변 위험 포인트 | `answer_risk_points` | List[String] | 예상 답변에서 불확실하거나 과장 가능성이 있는 지점 |

### Driller가 작성하는 필드 (follow_ups 리스트)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 참조 ID | `question_id` | String | 대응하는 질문의 ID |
| 꼬리질문 | `follow_up_question` | String | 예상 답변의 허점을 찌르거나 깊이를 파고드는 2차 꼬리 질문. 존재 여부가 Scorer 점수(+5)에 영향. 부재 시 FOLLOW_UP_TOO_WEAK 플래그 발생 → Driller 재시도 라우팅 |
| 꼬리질문 근거 | `follow_up_basis` | String | 왜 이 꼬리질문이 필요한지 설명하는 근거 |
| 꼬리질문 유형 | `drill_type` | String | 꼬리질문의 검증 목적 (역할_검증, 수치_확인, 의사결정_검증 등) |

### Reviewer가 작성하는 필드 (reviews 리스트)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 참조 ID | `question_id` | String | 대응하는 질문의 ID |
| 리뷰 상태 | `status` | String | Reviewer가 내린 판정 (approved / needs_revision / rejected). Scorer 기본 점수 베이스: approved=38, needs_revision=20, rejected=0 |
| 리뷰 요약 | `reason` | String | Reviewer가 남긴 검토 요약 |
| 반려 사유 | `reject_reason` | String | 반려 시 구체적인 반려 사유. 존재 시 Scorer 점수 -10 |
| 수정 제안 | `recommended_revision` | String | 수정 방향 제안 |

### Scorer가 산출하는 필드 (scores 리스트 + review_summary)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 참조 ID | `question_id` | String | 대응하는 질문의 ID |
| 품질 점수 | `score` | Int | 0~100점. 규칙 기반 계산 (중복 감점 -15, 저점수 임계값 80점) |
| 점수 사유 | `score_reason` | String | 점수 산출 근거 요약 |
| 품질 플래그 | `quality_flags` | List[String] | 감점 원인 플래그 목록 (EVIDENCE_TOO_WEAK, FOLLOW_UP_TOO_WEAK, LOW_SCORE, DUPLICATE_RISK 등) |

**review_summary 필드**에는 `approved_count`, `low_score_count`, `low_score_question_ids`, `avg_score`, `quality_issues`, `scored_question_count`가 집약되며 Review Router의 분기 판단 기준으로 사용됩니다.

---

### 2. Review Router 분기 로직

Scorer 실행 후 `route_after_review` 함수가 다음 순서로 분기를 결정합니다.

| 조건 | 분기 대상 | 처리 내용 |
| --- | --- | --- |
| `retry_count >= max_retry_count` (기본값 2) | `selector` | 무한 루프 방지. 재시도 횟수 초과 시 강제 종료 |
| `FOLLOW_UP_TOO_WEAK` 플래그 존재 AND `driller_retry_count < max_driller_retry_count` (기본값 1) | `retry_driller` | `follow_ups` 초기화 후 Driller 재실행 |
| `low_score_count > 0` OR `approved_count < 5` OR `QUESTION_REWRITE_FLAGS` 존재 AND `questioner_retry_count < max_questioner_retry_count` (기본값 1) | `retry_questioner` | 저점수 ID 최대 2개를 `target_question_ids`에 설정 후 Questioner 부분 재생성 |
| 위 조건 모두 해당 없음 | `selector` | 품질 기준 충족, Selector로 진행 |

**QUESTION_REWRITE_FLAGS** = {REVIEW_NOT_APPROVED, LOW_SCORE, EVIDENCE_TOO_WEAK, LOW_JOB_RELEVANCE, DUPLICATE_RISK}

---

### 3. 통합 에이전트 공유 상태 (Object: AgentState)

### 입력 데이터 영역 (Input Context)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 세션 ID | `session_id` | Int | 면접 세션 식별자 |
| 지원자 ID | `candidate_id` | Int | 지원자 식별자 |
| 지원자 이름 | `candidate_name` | String | 지원자 이름 |
| 지원 직무 | `target_job` | String | 지원 직무 |
| 난이도 | `difficulty_level` | String / None | 신입/경력/시니어 수준 판단에 사용 |
| 프롬프트 프로필 | `prompt_profile` | Dict / None | 채용 기준 및 평가 기준이 담긴 프롬프트 프로필. Questioner system_prompt 앞에 prepend되어 직무별 맞춤 지시 가능 |
| 문서 목록 | `documents` | List[DocumentRef] | 이력서, 자기소개서, 포트폴리오 등 입력 문서 목록 (document_id, document_type, title, extracted_text 포함) |

### 파생 입력 영역 (Prepared Context)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 공통 문맥 | `candidate_context` | String | BuildState가 세션/지원자/문서 정보를 병합해 만든 공통 입력 문맥. 최대 18,000자로 클리핑 |
| 문서 분석 결과 | `document_analysis` | Dict | Analyzer가 생성한 구조화된 분석 결과. 이후 모든 에이전트의 공통 입력 |

### 핵심 프로세스 데이터 영역 (Core Process)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 질문 목록 | `questions` | List[Dict] | Questioner가 생성한 질문 메타데이터 목록 |
| 예측 답변 목록 | `answers` | List[Dict] | Predictor가 생성한 예측 답변 목록 (question_id로 매핑) |
| 꼬리질문 목록 | `follow_ups` | List[Dict] | Driller가 생성한 꼬리질문 목록 (question_id로 매핑) |
| 리뷰 목록 | `reviews` | List[Dict] | Reviewer가 생성한 리뷰 결과 목록 (question_id로 매핑) |
| 점수 목록 | `scores` | List[Dict] | Scorer가 산출한 품질 점수 목록 (question_id로 매핑) |
| 리뷰 요약 | `review_summary` | Dict | Scorer가 집약한 승인 수, 저점수 ID 목록, 평균 점수, 품질 이슈 목록 |

### 시스템 제어 영역 (Flow Control)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 전체 재시도 횟수 | `retry_count` | Int | 재시도 루프 진입 누적 횟수 |
| 최대 재시도 횟수 | `max_retry_count` | Int | 무한 루프 방지 상한선 (기본값 2) |
| Questioner 재시도 횟수 | `questioner_retry_count` | Int | Questioner 전용 재시도 횟수 |
| Driller 재시도 횟수 | `driller_retry_count` | Int | Driller 전용 재시도 횟수 |
| Questioner 최대 재시도 | `max_questioner_retry_count` | Int | Questioner 재시도 상한선 (기본값 1) |
| Driller 최대 재시도 | `max_driller_retry_count` | Int | Driller 재시도 상한선 (기본값 1) |
| 재시도 피드백 | `retry_feedback` | String / None | 재시도 시 Questioner/Driller에게 전달되는 이전 리뷰 결과 요약 |

### 서비스 레이어 재호출 파라미터 영역 (Re-invocation Params)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| 재호출 액션 유형 | `human_action` | String / None | 사람이 선택한 액션 유형 (more, regenerate_question, add_question 등). Questioner 내부 분기 조건으로 사용 |
| 추가 질문 지시사항 | `additional_instruction` | String / None | 사람이 입력한 추가 질문 생성 요청 문장 |
| 재생성 대상 질문 ID 목록 | `target_question_ids` | List[String] | 개별 재생성 시 대상 질문 ID 목록. Questioner가 해당 개수만큼만 생성 후 기존 목록에 병합 |

### 관측성 영역 (Observability)

| 구분 | 필드명 (Field) | 데이터 타입 | 상세 설명 |
| --- | --- | --- | --- |
| LLM 사용량 기록 | `llm_usages` | Annotated[List, operator.add] | 노드별 모델명, 입출력 토큰, 비용, 소요시간 기록. 각 노드 결과가 누적 합산됨 |
| 노드 경고 기록 | `node_warnings` | Annotated[List, operator.add] | 매칭 실패, fallback 사용, 추출 텍스트 없음 등 경고 정보. 각 노드 결과가 누적 합산됨 |

---

## 코드 예시

```python
from typing import Annotated, Any, TypedDict
import operator

# 1. 개별 질문 데이터 (Questioner 출력)
class QuestionDict(TypedDict):
    id: str
    category: str
    question_text: str
    generation_basis: str
    document_evidence: list[str]
    evaluation_guide: str
    risk_tags: list[str]
    competency_tags: list[str]

# 2. 에이전트별 출력 (question_id로 questions와 매핑)
class PredictedAnswer(TypedDict):
    question_id: str
    predicted_answer: str
    predicted_answer_basis: str
    answer_confidence: str        # low / medium / high
    answer_risk_points: list[str]

class FollowUpQuestion(TypedDict):
    question_id: str
    follow_up_question: str
    follow_up_basis: str
    drill_type: str

class ReviewResult(TypedDict):
    question_id: str
    status: str                   # approved / needs_revision / rejected
    reason: str
    reject_reason: str
    recommended_revision: str

class ScoreResult(TypedDict):
    question_id: str
    score: int                    # 0~100
    score_reason: str
    quality_flags: list[str]

# 3. 전체 에이전트가 공유하는 State
class AgentState(TypedDict, total=False):
    # 입력
    session_id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    difficulty_level: str | None
    prompt_profile: dict | None
    documents: list[dict]
    # 파생 입력
    candidate_context: str
    document_analysis: dict[str, Any]
    # 핵심 프로세스 (에이전트별 독립 리스트, question_id로 매핑)
    questions: list[QuestionDict]
    answers: list[PredictedAnswer]
    follow_ups: list[FollowUpQuestion]
    reviews: list[ReviewResult]
    scores: list[ScoreResult]
    review_summary: dict[str, Any]
    # 시스템 제어
    retry_count: int
    max_retry_count: int
    questioner_retry_count: int
    driller_retry_count: int
    max_questioner_retry_count: int
    max_driller_retry_count: int
    retry_feedback: str | None
    # 재호출 파라미터
    human_action: str | None
    additional_instruction: str | None
    target_question_ids: list[str]
    # 관측성 (누적 합산)
    llm_usages: Annotated[list[dict], operator.add]
    node_warnings: Annotated[list[dict], operator.add]
    # 출력
    final_response: dict[str, Any]

# 4. 서비스 레이어 재호출 예시 (pseudo-code)
def reinvoke_langgraph(prev_result: dict, user_action: dict) -> dict:
    payload = build_base_payload(prev_result)

    if user_action["type"] == "more":
        payload["human_action"] = "more"
        payload["existing_questions"] = prev_result["questions"]

    elif user_action["type"] == "regenerate_all":
        payload["existing_questions"] = []
        payload["human_action"] = None

    elif user_action["type"] == "regenerate_partial":
        payload["human_action"] = "regenerate_question"
        payload["target_question_ids"] = user_action["question_ids"]
        payload["existing_questions"] = prev_result["questions"]

    elif user_action["type"] == "add_question":
        payload["human_action"] = "add_question"
        payload["additional_instruction"] = user_action["instruction"]
        payload["existing_questions"] = prev_result["questions"]

    return langgraph_run(payload)
```

---

## 주요 변경 사항 요약

- **노드 추가:** PrepareContext → BuildState + Analyzer 분리, Scorer, Selector, FinalFormatter 신규 추가
- **라우터 위치 변경:** Reviewer 이후 → Scorer 이후로 이동, Driller/Questioner 각각 독립 재시도 분기 추가
- **데이터 구조 변경:** 단일 QuestionSet 임베드 방식 → questions, answers, follow_ups, reviews, scores 독립 리스트 + question_id 매핑 방식
- **Scorer 로직 명시:** 규칙 기반 점수 산출 기준(베이스 점수, 가산/감산 항목, 플래그 체계) 추가
- **State 필드 정합:** document_analysis, review_summary, retry_feedback, 별도 재시도 카운터, Annotated 누적 합산 필드 반영