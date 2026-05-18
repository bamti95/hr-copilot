# HR Copilot LangGraph AS-IS 설계 문서

> 초기 LangGraph 설계 기준점 정리 문서  
> 목적: 개선 전 구조의 설계 근거, 노드별 역할, State 흐름, generation_basis 작성 기준을 일목요연하게 정리한다.

---

## 1. 문서 목적

본 문서는 HR Copilot의 초기 LangGraph 기반 면접 질문 생성 파이프라인을 AS-IS 기준으로 정리한 문서이다.

초기 구조는 단순히 LLM에게 면접 질문을 한 번에 생성시키는 방식이 아니라, 실제 면접관이 사고하는 흐름을 여러 노드로 분리하여 구성한 구조이다.

전체 흐름은 다음과 같다.

```text
지원자 문서/세션 정보 입력
→ 지원자 문맥 구성
→ 문서 분석
→ 질문 후보 생성
→ 1차 선별
→ 예상 답변 생성
→ 꼬리 질문 생성
→ HR 품질 검수
→ 점수 평가
→ 조건부 재시도
→ 최종 질문 선택
→ API 응답 포맷 변환
```

---

## 2. 초기 설계 핵심 철학

| 구분 | 설계 원칙 | 설명 | 기대 효과 |
|---|---|---|---|
| 1 | 역할 기반 노드 분리 | analyzer, questioner, reviewer, scorer처럼 실제 면접 운영 역할을 노드로 분리 | 각 단계의 책임이 명확해지고 디버깅이 쉬워짐 |
| 2 | 단계별 품질 제어 | 질문 생성 이후 reviewer와 scorer를 통해 품질을 검증 | 질문 품질을 한 번 더 통제 가능 |
| 3 | 비용 최적화 | selector_lite에서 8개 질문 중 5개만 선별한 뒤 후속 LLM 노드 실행 | predictor, driller, reviewer 등 고비용 노드 호출량 감소 |
| 4 | 부분 재생성 | 전체 질문을 다시 만들지 않고 낮은 점수 질문만 재생성 | 토큰 낭비 감소 및 재시도 효율 향상 |
| 5 | State 기반 워크플로우 | 모든 노드가 AgentState를 읽고 필요한 필드만 갱신 | 노드 간 데이터 흐름 추적 가능 |
| 6 | 조건부 라우팅 | route_after_scoring에서 점수/리뷰 결과에 따라 다음 노드를 결정 | 품질 부족 시 자동 보정 흐름 가능 |
| 7 | 관측 가능성 확보 | llm_usages를 통해 노드별 토큰, 비용, 시간, 실패 여부를 기록 | 비용 대시보드와 성능 개선 근거 확보 |

---

## 3. AS-IS 전체 FLOW

```text
build_state
  ↓
analyzer
  ↓
questioner
  ↓
selector_lite
  ↓
predictor
  ↓
driller
  ↓
reviewer
  ↓
scorer
  ↓
route_after_scoring
  ├─ retry_questioner → questioner
  ├─ retry_driller → driller
  └─ selector
        ↓
final_formatter
```

---

## 4. AgentState 데이터 흐름 요약

| 영역 | 필드 | 설명 | 주 사용 노드 |
|---|---|---|---|
| Input | documents | 지원자 이력서, 포트폴리오 등 문서 데이터 | build_state, analyzer |
| Input | session_id | 질문 생성 세션 ID | build_state, final_formatter |
| Input | target_job | 대상 직무 | build_state, analyzer, questioner |
| Input | difficulty_level | 질문 난이도 | questioner, final_formatter |
| Input | prompt_profile | 프롬프트 프로필 설정 | analyzer, questioner, reviewer |
| Input | target_question_ids | 부분 재생성 대상 질문 ID | retry_questioner, questioner |
| Input | human_action | 사용자 요청 또는 재생성 액션 구분값 | questioner, retry_questioner |
| Input | additional_instruction | 사용자 추가 지시사항 또는 재생성 보완 지시 | questioner, retry_questioner |
| Workflow | candidate_context | 지원자/직무/문서 정보를 합친 공통 문맥 | analyzer, questioner, predictor |
| Workflow | document_analysis | 강점, 약점, 리스크, 검증 포인트 | questioner, driller, reviewer |
| Workflow | questions | 생성된 면접 질문 목록 | selector_lite, predictor, reviewer, scorer |
| Workflow | answers | 예상 답변 목록 | driller, reviewer, final_formatter |
| Workflow | follow_ups | 꼬리 질문 목록 | reviewer, scorer, final_formatter |
| Workflow | reviews | HR 품질 검수 결과 | scorer, selector, final_formatter |
| Workflow | scores | 질문별 점수 결과 | router, selector, final_formatter |
| Workflow | review_summary | 승인 수, 반려 수, 낮은 점수 질문 등 요약 | route_after_scoring |
| Control | retry_count | 전체 재시도 횟수 | router, retry 노드 |
| Control | max_retry_count | 최대 재시도 횟수 | router |
| Control | questioner_retry_count | questioner 재시도 횟수 | router, retry_questioner |
| Control | driller_retry_count | driller 재시도 횟수 | router, retry_driller |
| Control | max_questioner_retry_count | questioner 최대 재시도 횟수 | router |
| Control | max_driller_retry_count | driller 최대 재시도 횟수 | router |
| Control | retry_feedback | 재생성 시 참고할 피드백 | questioner, driller |
| Control | node_warnings | 노드 실행 중 발생한 경고 | final_formatter |
| Observability | llm_usages | 노드별 LLM 호출 로그 | runner, dashboard |
| Output | final_response | API 최종 응답 | final_formatter |

---

## 5. 노드별 AS-IS 설계 요약

| 순서 | 노드 | 역할 | IN 읽는 필드 | OUT 쓰는 필드 | LLM 호출 | 설계 근거 |
|---:|---|---|---|---|---|---|
| 1 | build_state | 접수 담당자 | documents, session_id, target_job, difficulty_level | candidate_context, retry_count, max_retry_count | 없음 | 이후 모든 LLM 노드가 공통으로 참조할 문맥을 먼저 정리하기 위함 |
| 2 | analyzer | 서류 분석관 | candidate_context, documents, prompt_profile | document_analysis, llm_usages | gpt-5-mini | 질문 생성 전에 강점, 약점, 리스크, 검증 포인트를 구조화하기 위함 |
| 3 | questioner | 질문 설계자 | candidate_context, document_analysis, target_question_ids, retry_feedback | questions, llm_usages | gpt-5-mini | 문서 분석 결과를 기반으로 면접 질문 후보를 생성하기 위함 |
| 4 | selector_lite | 1차 편집자 | questions | questions | 없음 | 후속 고비용 LLM 노드 실행 전에 질문 수를 줄이기 위함 |
| 5 | predictor | 답변 예측관 | questions, candidate_context, document_analysis | answers, llm_usages | gpt-5-mini | 지원자가 답변할 가능성이 있는 내용을 미리 예측하여 꼬리 질문 품질을 높이기 위함 |
| 6 | driller | 심층 면접관 | questions, answers, document_analysis | follow_ups, llm_usages | gpt-5-mini | 예상 답변의 모호함, 과장 가능성, 근거 부족을 검증하기 위함 |
| 7 | reviewer | HR 품질 검수관 | questions, answers, follow_ups, target_job, prompt_profile | reviews, llm_usages | gpt-5-mini | 질문의 직무 적합성, 공정성, 중복, 면접 활용성을 검수하기 위함 |
| 8 | scorer | 정량 평가관 | questions, answers, follow_ups, reviews | scores, review_summary | 없음 | LLM scorer 제거, reviewer 기반 규칙형 scorer로 확정 예정 |
| 9 | route_after_scoring | 편집장 | review_summary, retry_count, max_retry_count, questioner_retry_count, driller_retry_count, max_questioner_retry_count, max_driller_retry_count | 다음 노드 결정 | 없음 | 점수와 리뷰 결과, 노드별 재시도 한도에 따라 재생성 또는 최종 선택 여부를 결정하기 위함 |
| 10 | retry_questioner | 질문 수정 지시자 | review_summary, scores, retry_count | target_question_ids, human_action, additional_instruction, retry_feedback, questioner_retry_count | 없음 | 낮은 점수 질문만 부분 재생성하기 위함 |
| 11 | retry_driller | 꼬리 질문 수정 지시자 | review_summary, follow_ups, retry_count | retry_feedback, driller_retry_count | 없음 | 꼬리 질문 품질 이슈만 별도로 수정하기 위함 |
| 12 | selector | 최종 선별자 | questions, reviews, scores | questions | 없음 | 최종 면접에 사용할 질문 5개를 선별하기 위함 |
| 13 | final_formatter | 최종 응답 편집자 | questions, answers, follow_ups, reviews, scores, node_warnings | final_response | 없음 | API 응답 스키마로 변환하고 completed/partial_completed 상태를 결정하기 위함 |

---

## 6. 노드별 상세 설계

### 6.1 build_state

| 항목 | 내용 |
|---|---|
| 역할 | 지원자 문서, 세션 정보, 직무 정보, 난이도 정보를 하나의 실행 문맥으로 조립하는 전처리 노드 |
| 비유 | 접수 담당자 |
| IN | documents, session_id, candidate_id, candidate_name, target_job, difficulty_level, prompt_profile, human_action, additional_instruction |
| OUT | candidate_context, retry_count, max_retry_count |
| LLM 호출 | 없음 |
| 설계 근거 | LLM 노드마다 입력 데이터를 따로 해석하게 두면 문맥 불일치가 발생할 수 있으므로, 최초 단계에서 지원자/직무/문서 정보를 하나의 candidate_context로 통합한다. |
| generation_basis | 해당 없음. 이 노드는 생성 노드가 아니라 입력 정규화 노드이다. |

#### build_state 출력 예시

```json
{
  "candidate_context": "지원자: 서현석 / 지원 직무: AI 백엔드 개발자 / 주요 문서: 이력서, 포트폴리오 / 난이도: MEDIUM",
  "retry_count": 0,
  "max_retry_count": 3
}
```

---

### 6.2 analyzer

| 항목 | 내용 |
|---|---|
| 역할 | 지원자 문서와 직무 기준을 분석하여 강점, 약점, 리스크, 면접 검증 포인트를 도출 |
| 비유 | 서류 분석관 |
| IN | candidate_context, documents, target_job, difficulty_level, prompt_profile |
| OUT | document_analysis, llm_usages |
| LLM 호출 | gpt-5-mini |
| 설계 근거 | 질문을 바로 생성하면 문서의 어떤 부분을 근거로 질문이 만들어졌는지 설명하기 어렵다. 따라서 먼저 지원자 문서를 분석해 질문 생성의 기준 데이터를 만든다. |
| generation_basis | 문서에서 어떤 근거로 강점/약점/리스크를 도출했는지 기록한다. |

#### analyzer generation_basis 예시

```json
{
  "strengths": [
    {
      "title": "React 기반 관리자 UI 구현 경험",
      "evidence": "포트폴리오에 CMS 관리자 화면 구현 경험이 기재되어 있음",
      "source": "portfolio",
      "confidence": 0.86
    }
  ],
  "weaknesses": [
    {
      "title": "성능 최적화 경험 부족",
      "evidence": "대용량 트래픽, 쿼리 튜닝, 캐싱 적용 사례가 명확히 기재되어 있지 않음",
      "source": "resume/portfolio",
      "confidence": 0.78
    }
  ],
  "risks": [
    {
      "risk_type": "missing_experience",
      "description": "운영 환경에서의 성능 개선 경험이 부족할 가능성",
      "interview_focus": "실제 성능 병목을 발견하고 개선한 경험이 있는지 검증 필요"
    }
  ]
}
```

---

### 6.3 questioner

| 항목 | 내용 |
|---|---|
| 역할 | analyzer 결과를 기반으로 면접 질문 후보를 생성 |
| 비유 | 질문 설계자 |
| IN | candidate_context, document_analysis, target_job, difficulty_level, retry_feedback, target_question_ids |
| OUT | questions, llm_usages |
| 기본 생성 수 | 8개 |
| LLM 호출 | gpt-5-mini |
| 설계 근거 | 질문은 단순 일반 질문이 아니라 문서 분석 결과의 약점, 리스크, 강점 검증 포인트를 기반으로 생성되어야 한다. 특히 실무 면접에서는 잘하는 점보다 확인이 필요한 지점을 질문하는 것이 중요하므로 weakness/risk 기반 질문을 우선 생성한다. |
| generation_basis | 질문이 어떤 분석 결과에서 파생되었는지, 어떤 역량/리스크를 검증하려는지 기록한다. |

#### questioner generation_basis 예시

```json
{
  "question_id": "Q-003",
  "question": "성능 개선이 필요한 상황을 직접 발견하고 개선해 본 경험이 있다면 설명해 주세요.",
  "category": "TECH",
  "generation_basis": {
    "from_node": "analyzer",
    "source_type": "weakness",
    "source_summary": "성능 최적화 경험이 문서에 명확히 드러나지 않음",
    "target_skill": "performance_optimization",
    "intent": "운영 환경에서의 성능 개선 경험 검증",
    "risk_type": "missing_experience",
    "expected_signal": "병목 원인 분석, 개선 방법, 수치 기반 성과 설명 여부",
    "confidence": 0.82
  }
}
```

---

### 6.4 selector_lite

| 항목 | 내용 |
|---|---|
| 역할 | questioner가 생성한 8개 질문 후보 중 후속 처리할 5개를 1차 선별 |
| 비유 | 1차 편집자 |
| IN | questions |
| OUT | questions |
| LLM 호출 | 없음 |
| 선별 기준 | 문서 근거 존재 여부, 리스크 검증력, 카테고리 다양성, 질문 중복 여부, 직무 관련성 |
| 설계 근거 | 모든 질문에 대해 predictor, driller, reviewer를 실행하면 비용과 지연 시간이 증가한다. 따라서 LLM 호출 없이 먼저 질문 수를 줄여 후속 고비용 노드의 실행량을 줄인다. |
| generation_basis | selector_lite는 LLM 생성 노드가 아니므로 generation_basis 대신 selection_basis를 둘 수 있다. |

#### selector_lite selection_basis 예시

```json
{
  "selected_question_ids": ["Q-001", "Q-002", "Q-003", "Q-005", "Q-007"],
  "selection_basis": [
    {
      "question_id": "Q-003",
      "reason": "성능 최적화 경험 부족이라는 핵심 리스크를 검증하는 질문",
      "priority": "HIGH"
    }
  ],
  "removed_question_ids": ["Q-004", "Q-006", "Q-008"],
  "remove_reason": "중복 또는 직무 관련성 낮음"
}
```

---

### 6.5 predictor

| 항목 | 내용 |
|---|---|
| 역할 | 선별된 질문에 대해 지원자가 답변할 가능성이 있는 예상 답변을 생성 |
| 비유 | 답변 예측관 |
| IN | questions, candidate_context, document_analysis |
| OUT | answers, llm_usages |
| LLM 호출 | gpt-5-mini |
| 설계 근거 | 좋은 꼬리 질문을 만들기 위해서는 지원자의 가능한 답변을 먼저 예측해야 한다. 예상 답변이 있어야 답변의 모호함, 과장 가능성, 검증 포인트를 기반으로 심층 질문을 만들 수 있다. |
| generation_basis | 예상 답변이 어떤 문서 근거와 어떤 추론에 기반했는지 기록한다. |

#### predictor generation_basis 예시

```json
{
  "question_id": "Q-003",
  "predicted_answer": "프로젝트에서 로딩 속도가 느린 화면을 개선하기 위해 API 호출 구조를 정리하고 일부 컴포넌트를 분리했습니다.",
  "predicted_answer_basis": {
    "source": "portfolio",
    "evidence": "React 관리자 화면 구현 및 API 연동 경험이 기재되어 있음",
    "inference": "성능 개선 경험이 직접적으로 적혀 있지는 않지만 프론트엔드 최적화 수준의 답변을 할 가능성이 있음",
    "risk_points": ["정량 수치 부족", "백엔드 성능 개선 경험 여부 불명확"],
    "answer_confidence": 0.64
  }
}
```

---

### 6.6 driller

| 항목 | 내용 |
|---|---|
| 역할 | 예상 답변을 기반으로 꼬리 질문을 생성 |
| 비유 | 심층 면접관 |
| IN | questions, answers, document_analysis |
| OUT | follow_ups, llm_usages |
| LLM 호출 | gpt-5-mini |
| 설계 근거 | 일반 질문만으로는 지원자의 실제 역할, 성과, 문제 해결 과정을 검증하기 어렵다. 예상 답변의 빈틈을 기준으로 꼬리 질문을 생성해 면접의 검증력을 높인다. |
| generation_basis | 꼬리 질문이 어떤 답변의 모호성 또는 리스크를 검증하기 위해 생성되었는지 기록한다. |

#### driller generation_basis 예시

```json
{
  "question_id": "Q-003",
  "follow_up_question": "개선 전후의 응답 시간이나 로딩 시간이 얼마나 달라졌는지 수치로 설명할 수 있나요?",
  "follow_up_basis": {
    "trigger": "predicted_answer",
    "detected_issue": "정량적 성과 지표가 부족할 가능성",
    "drill_type": "METRIC_VERIFICATION",
    "intent": "성과 수치 검증",
    "expected_signal": "개선 전후 수치, 측정 방법, 본인 기여도 설명 여부"
  }
}
```

---

### 6.7 reviewer

| 항목 | 내용 |
|---|---|
| 역할 | 질문, 예상 답변, 꼬리 질문을 HR 기준으로 검수 |
| 비유 | HR 품질 검수관 |
| IN | questions, answers, follow_ups, target_job, prompt_profile |
| OUT | reviews, llm_usages |
| LLM 호출 | gpt-5-mini |
| 검수 기준 | 직무 관련성, 문서 근거, 리스크 검증력, 면접 활용성, 공정성, 중복 위험 |
| 설계 근거 | 질문 생성 결과가 실제 면접에서 사용 가능한 수준인지 검증하는 단계가 필요하다. 특히 채용 면접 질문은 공정성, 직무 관련성, 중복 여부를 반드시 확인해야 한다. |
| generation_basis | 리뷰 판단의 기준과 승인/수정/반려 사유를 기록한다. |

#### reviewer review_basis 예시

```json
{
  "question_id": "Q-003",
  "status": "needs_revision",
  "review_basis": {
    "criteria": {
      "job_relevance": "HIGH",
      "evidence_based": "MEDIUM",
      "risk_validation": "HIGH",
      "fairness": "PASS",
      "duplication": "LOW"
    },
    "reason": "성능 경험을 검증하는 방향은 적절하지만 질문이 다소 넓어 구체적인 상황 제시가 필요함",
    "recommendation": "프로젝트 상황, 병목 원인, 개선 수치를 포함하도록 질문을 구체화"
  }
}
```

---

### 6.8 scorer

| 항목 | 내용 |
|---|---|
| 역할 | 리뷰 결과와 질문 품질을 기반으로 질문별 점수를 산출하고 review_summary를 생성 |
| 비유 | 정량 평가관 |
| IN | questions, answers, follow_ups, reviews |
| OUT | scores, review_summary |
| LLM 호출 | 없음 |
| 점수 범위 | 0~100 |
| 설계 근거 | LLM scorer 제거, reviewer 기반 규칙형 scorer로 확정 예정. router가 재시도 여부를 판단하려면 정성 리뷰만으로는 부족하므로 승인 수, 반려 수, 낮은 점수 질문 ID, 평균 점수 같은 정량 데이터가 필요하다. |
| generation_basis | scorer는 생성 노드라기보다 평가 노드이므로 score_basis를 기록한다. |

#### scorer score_basis 예시

```json
{
  "question_id": "Q-003",
  "score": 78,
  "score_basis": {
    "job_relevance": 22,
    "evidence_based": 16,
    "specificity": 14,
    "risk_validation": 20,
    "fairness": 6,
    "total": 78,
    "low_score_reason": "질문 의도는 적절하지만 구체적인 상황과 평가 기준이 부족함"
  }
}
```

#### review_summary 예시

```json
{
  "approved_count": 4,
  "rejected_count": 0,
  "needs_revision_count": 1,
  "average_score": 84.6,
  "low_score_question_ids": ["Q-003"],
  "low_score_count": 1,
  "driller_issue_question_ids": [],
  "questioner_retry_target_ids": ["Q-003"]
}
```

---

### 6.9 route_after_scoring

| 항목 | 내용 |
|---|---|
| 역할 | scorer의 review_summary를 기준으로 다음 실행 노드를 결정 |
| 비유 | 편집장 |
| IN | review_summary, retry_count, max_retry_count, questioner_retry_count, driller_retry_count, max_questioner_retry_count, max_driller_retry_count |
| OUT | retry_questioner, retry_driller, selector 중 하나로 분기 |
| LLM 호출 | 없음 |
| 설계 근거 | 질문 품질이 부족할 때 무조건 실패 처리하지 않고, 문제 유형과 노드별 재시도 한도에 따라 질문 재생성 또는 꼬리 질문 재생성으로 되돌리는 자동 보정 흐름을 만들기 위함이다. |

#### route_after_scoring 분기 기준 예시

| 조건 | 분기 대상 | 설명 |
|---|---|---|
| 낮은 점수 질문이 1~2개 | retry_questioner | 일부 질문만 재생성 |
| 꼬리 질문 품질 이슈 존재 | retry_driller | 꼬리 질문만 재생성 |
| 승인 질문 수 부족 | retry_questioner | 질문 후보 품질 개선 필요 |
| 최대 재시도 도달 | selector | 더 이상 재시도하지 않고 현재 결과 중 최선 선택 |
| questioner 재시도 한도 도달 | selector | 질문 재생성을 더 이상 수행하지 않음 |
| driller 재시도 한도 도달 | selector 또는 retry_questioner | 꼬리 질문 재생성을 더 이상 수행하지 않음 |
| 품질 기준 충족 | selector | 최종 질문 선택 단계로 이동 |

---

### 6.10 retry_questioner

| 항목 | 내용 |
|---|---|
| 역할 | 낮은 점수 질문만 다시 생성하도록 questioner 실행 조건을 설정 |
| 비유 | 질문 수정 지시자 |
| IN | review_summary, scores, retry_count |
| OUT | target_question_ids, human_action, additional_instruction, retry_feedback, questioner_retry_count |
| LLM 호출 | 없음 |
| 설계 근거 | 질문 5개 전체를 다시 생성하면 비용과 시간이 증가한다. 낮은 점수 질문이 일부라면 해당 질문 ID만 대상으로 재생성하여 효율적으로 품질을 개선한다. |

#### retry_questioner 제어 상태 예시

```json
{
  "human_action": "regenerate_question",
  "target_question_ids": ["Q-003"],
  "additional_instruction": "점수가 낮은 대상 질문만 개선해 새 질문으로 재생성하세요.",
  "retry_feedback": "Q-003은 성능 개선 검증 의도는 좋지만 구체성이 부족하므로 프로젝트 상황, 병목 원인, 개선 수치를 포함해 재작성 필요",
  "questioner_retry_count": 1
}
```

---

### 6.11 retry_driller

| 항목 | 내용 |
|---|---|
| 역할 | 꼬리 질문 품질 이슈가 있는 경우 driller를 다시 실행하도록 제어 상태를 설정 |
| 비유 | 꼬리 질문 수정 지시자 |
| IN | review_summary, follow_ups, retry_count |
| OUT | retry_feedback, driller_retry_count |
| LLM 호출 | 없음 |
| 설계 근거 | 본 질문은 적절하지만 꼬리 질문만 약한 경우 전체 질문 생성 단계로 되돌아갈 필요가 없다. driller만 재실행하여 비용을 줄인다. |

#### retry_driller 제어 상태 예시

```json
{
  "retry_feedback": "Q-002의 꼬리 질문이 너무 일반적이므로 본인 역할과 정량 성과를 검증하는 방향으로 재작성 필요",
  "driller_retry_count": 1
}
```

---

### 6.12 selector

| 항목 | 내용 |
|---|---|
| 역할 | 리뷰와 점수 결과를 기반으로 최종 질문 5개를 선택 |
| 비유 | 최종 선별자 |
| IN | questions, reviews, scores |
| OUT | questions |
| LLM 호출 | 없음 |
| 선택 기준 | 승인 여부, 점수, 문서 근거, 리스크 검증력, 카테고리 다양성, 중복 제거 |
| 설계 근거 | 최종 면접 질문은 단순히 점수가 높은 순서가 아니라 카테고리 균형과 검증 목적이 함께 고려되어야 한다. |

#### selector selection_basis 예시

```json
{
  "final_question_ids": ["Q-001", "Q-002", "Q-003", "Q-005", "Q-007"],
  "selection_basis": [
    {
      "question_id": "Q-003",
      "score": 86,
      "reason": "성능 개선 경험 부족 리스크를 직접 검증하며, 최종 수정 후 구체성이 개선됨"
    }
  ]
}
```

---

### 6.13 final_formatter

| 항목 | 내용 |
|---|---|
| 역할 | 최종 질문, 예상 답변, 꼬리 질문, 리뷰, 점수를 API 응답 구조로 변환 |
| 비유 | 최종 응답 편집자 |
| IN | questions, answers, follow_ups, reviews, scores, node_warnings, retry_count |
| OUT | final_response |
| LLM 호출 | 없음 |
| 응답 상태 | completed, partial_completed, failed |
| 설계 근거 | 내부 그래프 상태는 복잡하므로 프론트엔드/API 소비자가 바로 사용할 수 있는 응답 스키마로 변환해야 한다. 또한 문서 없음, 질문 부족, 승인 부족, 재시도 한계 등 부분 완료 상태를 명확히 표시해야 한다. |

#### final_formatter 출력 예시

```json
{
  "status": "completed",
  "questions": [
    {
      "question_id": "Q-003",
      "question": "성능 병목을 발견하고 개선한 경험을 구체적인 수치와 함께 설명해 주세요.",
      "category": "TECH",
      "predicted_answer": "API 호출 구조 개선 및 화면 렌더링 최적화 경험을 설명할 가능성이 있음",
      "follow_up_question": "개선 전후 수치를 어떻게 측정했는지 설명할 수 있나요?",
      "score": 86,
      "review_status": "approved"
    }
  ]
}
```

---

## 7. generation_basis 작성 기준

### 7.1 generation_basis의 목적

| 목적 | 설명 |
|---|---|
| 설명 가능성 확보 | 왜 이 질문이 생성되었는지 설명할 수 있음 |
| 디버깅 가능 | 질문 품질이 낮을 때 어떤 근거가 문제였는지 추적 가능 |
| HR 신뢰성 확보 | 면접관 또는 관리자가 질문 생성 이유를 확인 가능 |
| 재생성 품질 향상 | retry 시 기존 문제 원인을 피드백으로 활용 가능 |
| 대시보드 확장 | 질문 생성 근거별 통계, 리스크 유형별 질문 비중 분석 가능 |

---

### 7.2 generation_basis 공통 필드

| 필드 | 타입 | 설명 | 예시 |
|---|---|---|---|
| from_node | string | 어떤 노드 결과에서 파생되었는지 | analyzer |
| source_type | string | 근거 유형 | strength, weakness, risk, document_evidence |
| source_summary | string | 근거 요약 | 성능 최적화 경험이 문서에 부족함 |
| evidence | string | 실제 문서 또는 분석 근거 | 포트폴리오에 성능 수치가 없음 |
| target_skill | string | 검증하려는 기술/역량 | performance_optimization |
| intent | string | 질문 생성 목적 | 경험 공백 검증 |
| risk_type | string | 리스크 유형 | missing_experience |
| expected_signal | string | 답변에서 기대하는 판단 신호 | 수치, 원인 분석, 본인 역할 |
| confidence | number | 근거 신뢰도 | 0.82 |

---

### 7.3 generation_basis 표준 예시

```json
{
  "generation_basis": {
    "from_node": "analyzer",
    "source_type": "weakness",
    "source_summary": "성능 최적화 경험이 명확히 드러나지 않음",
    "evidence": "이력서와 포트폴리오에 트래픽 처리, 캐싱, 쿼리 튜닝 관련 경험이 없음",
    "target_skill": "performance_optimization",
    "intent": "실제 성능 개선 경험 보유 여부 검증",
    "risk_type": "missing_experience",
    "expected_signal": "성능 병목 발견 과정, 개선 방식, 개선 전후 수치, 본인 기여도",
    "confidence": 0.82
  }
}
```

---

## 8. partial_completed 판단 조건

| 조건 | 설명 | 예시 |
|---|---|---|
| 문서 없음 | 추출된 문서 텍스트가 없거나 부족 | extracted_text가 모두 비어 있음 |
| 질문 부족 | 최종 질문 수가 목표 개수보다 적음 | 최종 질문 5개 미만 |
| 승인 부족 | reviewer 기준 승인 질문이 부족 | approved_count < 5 |
| 재시도 한계 | max_retry_count에 도달 | retry_count >= max_retry_count |
| 노드 경고 | 특정 노드에서 fallback 또는 warning 발생 | node_warnings 존재 |

---

## 9. AS-IS 장점

| 장점 | 설명 |
|---|---|
| 흐름 추적 용이 | 노드가 역할별로 분리되어 어디서 문제가 발생했는지 확인하기 쉬움 |
| 품질 통제 가능 | reviewer와 scorer를 통해 질문 품질을 검증 가능 |
| 비용 절감 구조 포함 | selector_lite를 통해 후속 LLM 호출 대상 질문 수를 줄임 |
| 부분 재생성 가능 | 낮은 점수 질문만 다시 생성해 토큰 낭비를 줄임 |
| 운영 관측 가능 | llm_usages와 llm_call_log를 통해 노드별 비용, 토큰, 지연 시간 기록 가능 |
| API 응답 안정성 | final_formatter에서 completed/partial_completed/failed 상태를 명확히 구분 가능 |

---

## 10. AS-IS 한계

| 한계 | 설명 | 개선 방향 |
|---|---|---|
| 카테고리 표준화 부족 | 질문 카테고리와 drill_type에 영어/한글 값이 혼재될 수 있음 | enum 표준화 및 한국어 라벨 분리 |
| 평가 독립성 부족 | 생성과 평가가 같은 파이프라인 내부에서 이루어짐 | evaluator 또는 external_reviewer 노드 분리 |
| 후보 질문 다양성 제한 | 초기 후보 질문 수가 8개로 제한됨 | 10~12개 후보 생성 후 선별 |
| scorer 중복 가능성 | reviewer가 이미 품질 판단을 하는데 LLM scorer가 다시 평가할 수 있음 | LLM scorer 제거, reviewer 결과 기반 규칙형 scorer로 확정 예정 |
| 대량 처리 한계 | BackgroundTasks 기반 실행은 대량 세션 처리에 한계 | Celery/RQ/worker 큐 구조 도입 |
| 개선 전후 비교 부족 | 노드별 로그는 있으나 AS-IS/TO-BE 비교 지표가 약함 | workflow_version, graph_version, 개선 실험 테이블 추가 |

---

## 11. AS-IS 핵심 요약

| 항목 | 내용 |
|---|---|
| 기본 질문 후보 수 | 8개 |
| selector_lite 이후 질문 수 | 5개 |
| 최종 질문 수 | 5개 목표 |
| 주요 LLM 노드 | analyzer, questioner, predictor, driller, reviewer |
| 규칙 기반 노드 | build_state, selector_lite, scorer, router, retry 노드, selector, final_formatter |
| 비용 절감 포인트 | selector_lite, partial retry |
| 품질 통제 포인트 | reviewer, scorer, route_after_scoring |
| 재시도 방식 | 낮은 점수 질문 또는 꼬리 질문 품질 이슈만 부분 재시도 |
| 최종 응답 상태 | completed, partial_completed, failed |

---

## 12. 면접/포트폴리오 설명용 요약

```text
초기 LangGraph 구조는 단순히 LLM으로 질문을 생성하는 방식이 아니라,
실제 면접관의 사고 과정을 analyzer, questioner, predictor, driller, reviewer, scorer 노드로 분리한 구조입니다.

지원자 문서를 먼저 분석하고, 분석 결과의 약점과 리스크를 기반으로 질문을 생성한 뒤,
예상 답변과 꼬리 질문을 만들고, HR 기준으로 검수한 후 점수화합니다.

또한 selector_lite를 통해 8개 후보 중 5개만 후속 처리하여 비용을 줄이고,
낮은 점수 질문만 부분 재생성하는 방식으로 토큰 낭비를 줄였습니다.

즉, 이 구조의 핵심은 문서 기반 질문 생성, 품질 검증, 비용 최적화, 부분 재시도를 모두 포함한
상태 기반 면접 질문 생성 워크플로우입니다.
```

---

## 13. 최종 한 줄 정의

```text
면접관의 사고 흐름을 LangGraph 노드로 분해하고, 질문 품질은 reviewer/scorer로 검증하며, 비용은 selector_lite와 partial retry로 제어하는 초기 AS-IS 구조이다.
```
