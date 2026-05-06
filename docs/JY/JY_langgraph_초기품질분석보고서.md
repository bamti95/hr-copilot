# JY LangGraph 초기 품질 분석 보고서 (Baseline)

> 작성일: 2026-05-06
> 
> 
> 목적: `interview_graph_JY` 초기 구현의 생성 품질 구조를 정량/정성적으로 진단하여 추후 개선 실험과 비교하기 위한 베이스라인 문서
> 
> 데이터 범위: 단일 실행 1건, LLM 호출 9회, 총 100,166 tokens
> 
> 평가 기준: 그래프 실행 흐름, 재시도 발생 여부, 노드별 역할, 토큰 사용량, 품질 수렴 구조
> 
> 참고 코드: `backend/ai/interview_graph_JY`
> 

---

## 1. 전체 현황 요약 (핵심 KPI 10종)

| KPI | 값 | 비고 |
| --- | --- | --- |
| 평가 실행 수 | 1건 | 단일 LangGraph 실행 |
| 총 LLM 호출 수 | 9회 | 최초 5회 + 재시도 4회 |
| 성공률 | 100.0% | 실패 호출 없음 |
| 총 소비 토큰 | 100,166 tokens | Input 69,515 / Output 30,651 |
| 최초 생성 경로 호출 수 | 5회 | analyzer~reviewer |
| 재시도 경로 호출 수 | 4회 | questioner~reviewer |
| 재시도 발생 여부 | 발생 | `retry_questioner` 경로 진입 |
| 최종 선택 구조 | 최대 5문항 선별 | `selector_node` 기준 |
| 품질 검증 구조 | reviewer + scorer | LLM 검토 후 규칙 기반 점수화 |
| 품질 수렴 리스크 | 확인됨 | 재시도 후 selector로 종료 |

**요약 해석:**

- 초기 JY 그래프는 `analyzer → questioner → predictor → driller → reviewer → scorer` 구조를 통해 문서 분석, 질문 생성, 예상답변, 꼬리질문, 리뷰, 점수화를 모두 수행한다.
- 단일 실행에서 LLM 호출은 모두 성공했으므로 실행 안정성은 확보되었다.
- 다만 `scorer` 이후 `retry_questioner`로 진입했기 때문에 최초 생성 결과가 내부 품질 기준을 한 번에 통과하지 못한 것으로 해석된다.
- 재시도 후에는 다시 `questioner → predictor → driller → reviewer → scorer`를 수행한 뒤 `selector → final_formatter`로 종료되었다.
- 핵심 품질 리스크는 “리뷰어 미실행”이 아니라, **재시도 이후 품질이 충분히 개선되었는지 보장하는 수렴 조건이 약한 점**이다.

---

## 2. 평가 방식 및 루브릭

### 2-1. 평가 방식

이번 데이터에는 실제 생성된 질문 원문과 평가가이드 원문이 포함되어 있지 않다. 따라서 예시 보고서처럼 문항별 1~5점 수동 채점은 수행할 수 없다.

대신 다음 기준으로 초기 품질을 진단했다.

| 평가 축 | 확인 방식 |
| --- | --- |
| 질문 생성 품질 | `questioner_node` 프롬프트/출력 구조 |
| 문서 근거성 | `analyzer_node`, `candidate_context`, `document_analysis` 사용 여부 |
| 예상답변 품질 | `predictor_node` 프롬프트 제약 |
| 꼬리질문 품질 | `driller_node` 프롬프트 제약 |
| 리뷰 품질 | `reviewer_node` 판정 기준 |
| 점수화 품질 | `scorer_node` 규칙 기반 점수 계산 |
| 재시도 수렴성 | `route_after_review`, retry 경로 발생 여부 |

### 2-2. 질문 품질 평가 항목

| 항목 | 코드상 반영 여부 |
| --- | --- |
| 직무 관련성 | `target_job`, `prompt_profile`, 채용 기준 반영 |
| 문서 근거성 | `candidate_context`, `document_analysis`, `document_evidence` 반영 |
| 검증력 | 리스크, 역할, 성과, 의사결정 검증 지시 |
| 구체성 | `generation_basis`, `evaluation_guide` 요구 |
| 차별성/중복도 | `scorer_node`에서 중복 질문 감점 |
| 면접 사용성 | 존댓말 질문, 평가 가이드 포함 |
| 핵심 이력 반영도 | analyzer 결과 기반 질문 생성 |

### 2-3. 평가가이드 품질 평가 항목

| 항목 | 코드상 반영 여부 |
| --- | --- |
| 질문 정합성 | questioner가 질문과 guide를 함께 생성 |
| 기준 구체성 | `evaluation_guide` 필수 생성 |
| 관찰 가능성 | scorer에서 guide 존재 여부 점수화 |
| 판별력 | reviewer가 approved/needs_revision/rejected 판정 |
| 문서/직무 연계성 | document evidence, competency tags 반영 |
| 실무 활용성 | final formatter에서 면접 질문 형태로 통합 |
| 핵심 평가포인트 포착도 | analyzer의 risk/fit 분석 활용 |

---

## 3. 실행 흐름 기반 품질 집계

| 구간 | 노드 | 품질상 의미 | 결과 |
| --- | --- | --- | --- |
| 상태 구성 | build_state | 문서/세션 컨텍스트 구성 | 비LLM |
| 문서 분석 | jy_analyzer | 질문 근거 추출 | 성공 |
| 질문 생성 | jy_questioner | 8개 후보 질문 생성 | 성공 |
| 예상답변 생성 | jy_predictor | 질문별 예상 답변 생성 | 성공 |
| 꼬리질문 생성 | jy_driller | 질문별 follow-up 생성 | 성공 |
| 품질 리뷰 | jy_reviewer | 사용 가능성 판정 | 성공 |
| 점수화 | scorer | 규칙 기반 품질 점수 계산 | 비LLM |
| 재시도 | retry_questioner | 낮은 점수/미승인 보완 | 발생 |
| 재생성 | jy_questioner 재시도 | 질문 보완 생성 | 성공 |
| 재검증 | predictor~reviewer 재시도 | downstream 재평가 | 성공 |
| 선별 | selector | 최종 최대 5문항 선택 | 비LLM |
| 포맷팅 | final_formatter | 최종 응답 생성 | 비LLM |

**관찰 사항:**

- 최초 생성 결과가 바로 selector로 가지 않고 `retry_questioner`로 이동했다.
- 이는 `route_after_review` 기준에서 낮은 점수, 승인 부족, 또는 품질 플래그가 발생했음을 의미한다.
- JY 그래프는 reviewer만으로 종료하지 않고 scorer를 통해 점수와 품질 플래그를 계산한다는 점에서 품질 통제 구조는 명확하다.
- 그러나 재시도 후에는 questioner retry 가능 횟수가 소진되면 품질이 완전히 수렴하지 않아도 selector로 이동할 수 있다.

---

## 4. 항목별 품질 분석

### 4-1. 질문 품질 항목별 경향

| 항목 | 현재 수준 | 해석 |
| --- | --- | --- |
| 직무 관련성 | 중~높음 | `target_job`, 채용 기준, prompt profile이 questioner에 주입됨 |
| 문서 근거성 | 중~높음 | analyzer 결과와 candidate context를 함께 사용 |
| 검증력 | 높음 | 역할, 성과, 의사결정, 리스크 검증을 명시적으로 요구 |
| 구체성 | 높음 | 근거, 평가가이드, 역량 태그까지 생성하도록 설계 |
| 차별성/중복도 | 중간 | scorer에서 중복 감지는 있으나 생성 단계의 강제 제약은 약함 |
| 면접 사용성 | 중간 | 출력 필드가 풍부해질수록 질문/가이드가 장문화될 가능성 있음 |
| 핵심 이력 반영도 | 중~높음 | analyzer 기반이나, analyzer 출력이 장황하면 downstream 품질이 흔들릴 수 있음 |

### 4-2. 평가가이드 품질 항목별 경향

| 항목 | 현재 수준 | 해석 |
| --- | --- | --- |
| 질문 정합성 | 높음 | 질문 생성 시 evaluation guide를 함께 생성 |
| 기준 구체성 | 높음 | scorer가 guide 존재 여부를 품질 점수에 반영 |
| 관찰 가능성 | 중간 | 체크리스트형 강제 구조는 없음 |
| 판별력 | 중~높음 | reviewer와 scorer가 별도 작동하므로 판별 구조는 존재 |
| 문서/직무 연계성 | 높음 | document evidence, competency tags 반영 |
| 실무 활용성 | 중간 | guide 길이 제한이 없어 비전문 면접관 사용성이 낮아질 수 있음 |
| 핵심포인트 포착도 | 중~높음 | analyzer 결과 의존도가 높음 |

---

## 5. LangGraph/실행 흐름 기반 품질 진단

### 5-1. 핵심 사례: 단일 실행 trace

- 실행 흐름:
    
    `build_state → jy_analyzer → jy_questioner → jy_predictor → jy_driller → jy_reviewer → scorer → retry_questioner → jy_questioner → jy_predictor → jy_driller → jy_reviewer → scorer → selector → final_formatter`
    
- 총 LLM 호출: 9회
- 총 토큰: 100,166 tokens
- 재시도 경로 토큰: 50,511 tokens
- 재시도 경로 비중: 약 50.4%

### 5-2. 확인 결과

- reviewer는 정상 실행되었다.
- scorer 이후 retry가 발생했으므로, 최초 결과에 품질 이슈가 있었던 것으로 볼 수 있다.
- 재시도는 questioner부터 reviewer까지 전체 downstream을 다시 실행하는 방식이다.
- 재시도 후 selector로 종료되었지만, 종료 사유가 “완전 품질 충족”인지 “재시도 한계 또는 retry 조건 소진”인지는 trace만으로 확정할 수 없다.

**요약 해석:**

초기 JY 그래프의 품질 병목은 단순히 질문 생성 능력 부족이라기보다, **품질 플래그를 재작성 지시로 얼마나 정확히 환류시키는가**에 있다. 현재 구조는 재시도 루프는 존재하지만, 재시도 결과가 어떤 항목에서 얼마나 개선되었는지 정량적으로 비교하는 수렴 장치가 약하다.

---

## 6. 식별된 문제점 및 개선 시나리오

### 문제 요약

| # | 문제 | 영향 영역 | 심각도 |
| --- | --- | --- | --- |
| Q1 | 재시도 발생 후 품질 개선 정도를 비교하지 않음 | 품질 수렴성 | 높음 |
| Q2 | questioner 출력량이 많아 질문/가이드 장문화 가능성 | 면접 사용성 | 높음 |
| Q3 | analyzer 출력이 downstream 전체 품질을 좌우 | 문서 근거성 | 중간 |
| Q4 | predictor 예상답변이 꼬리질문을 과도하게 유도할 수 있음 | 꼬리질문 품질 | 중간 |
| Q5 | scorer 점수는 존재하지만 항목별 상세 루브릭 점수는 없음 | 품질 진단력 | 중간 |
| Q6 | retry가 questioner 전체 재생성 중심 | 비용/품질 안정성 | 높음 |
| Q7 | selector가 최종 5개를 고르지만 탈락 사유 추적은 제한적 | 운영 설명가능성 | 중간 |

### 개선 시나리오 5종

**시나리오 1: 재시도 전후 품질 diff 도입**

- 개선 방향: retry 전후 `score`, `quality_flags`, reviewer status 변화를 비교 저장
- 기대 효과: 재시도가 실제로 품질을 개선했는지 정량 확인 가능

**시나리오 2: questioner 출력 길이 및 형식 제한**

- 개선 방향: 질문 1문장, generation_basis 1~2문장, evaluation_guide 체크형 3개 이하로 제한
- 기대 효과: 면접 현장 사용성 개선, 장문 가이드 감소

**시나리오 3: 평가가이드 3단계 체크형 구조화**

- 개선 방향: `우수 / 보통 / 미흡` 또는 `강한 신호 / 보완 신호 / 리스크 신호`로 고정
- 기대 효과: 비전문 면접관도 즉시 사용할 수 있는 판별 기준 확보

**시나리오 4: 재시도 대상 질문 단위 downstream 제한**

- 개선 방향: 낮은 점수 질문만 predictor/driller/reviewer 재실행
- 기대 효과: 비용 절감뿐 아니라, 통과한 질문의 품질이 재생성으로 흔들리는 문제 방지

**시나리오 5: scorer 루브릭 세분화**

- 개선 방향: 현재 단일 score 외에 `evidence_score`, `job_relevance_score`, `usability_score`, `duplication_score` 등을 분리
- 기대 효과: 품질 병목 원인을 더 명확히 추적 가능

---

## 7. 베이스라인 수치 정리 (추후 비교용)

| 지표 | 초기 구현 Baseline | 목표 | 비고 |
| --- | --- | --- | --- |
| LLM 호출 성공률 | 100.0% | 100.0% 유지 | 실행 안정성 |
| 총 LLM 호출 수 | 9회 | 5~7회 | 재시도 최적화 |
| 총 토큰 | 100,166 | 70,000 이하 | 품질 유지 전제 |
| 재시도 발생 여부 | 발생 | 감소 | 최초 생성 품질 개선 |
| 재시도 경로 토큰 비중 | 50.4% | 30% 이하 | 부분 재시도 필요 |
| reviewer 실행 여부 | 정상 | 정상 유지 | 품질 검증 필수 |
| scorer 실행 여부 | 정상 | 정상 유지 | 규칙 기반 보정 |
| 최종 selector 도달 | 도달 | 도달 | 완료성 |
| 재시도 수렴성 | 불명확 | 전후 개선량 기록 | 핵심 개선 지표 |
| 문항별 수동 품질 점수 | 미측정 | 31/35 이상 | 원문 기반 별도 평가 필요 |