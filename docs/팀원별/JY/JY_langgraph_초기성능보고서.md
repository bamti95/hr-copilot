# JY LangGraph 초기 구현 성능 보고서 (Baseline)

> 작성일: 2026-05-06  
> 목적: `backend/ai/interview_graph_JY` 초기 LangGraph 구현의 단일 실행 성능을 정량화하여 추후 개선 실험과 비교하기 위한 베이스라인 문서  
> 데이터 범위: 단일 실행 1건, LLM 호출 9회, 모델 `gpt-5-mini`  
> 실행 경로: `build_state -> jy_analyzer -> jy_questioner -> jy_predictor -> jy_driller -> jy_reviewer -> scorer -> retry_questioner -> jy_questioner -> jy_predictor -> jy_driller -> jy_reviewer -> scorer -> selector -> final_formatter`

---

## 1. 전체 현황 요약 (핵심 KPI 10종)

| KPI | 값 | 비고 |
| --- | ---: | --- |
| 총 LLM 호출 수 | 9건 | 최초 경로 5건 + 재시도 경로 4건 |
| 성공률 | 100.0% | 실패 0건 |
| 총 소비 토큰 | 100,166 tokens | Input 69,515 / Output 30,651 |
| Input/Output 비율 | 2.27 : 1 | Input이 Output의 약 2.27배 |
| 총 LLM 시간 | 309.29초 | 제공 usage 기준 |
| 평균 레이턴시 | 34,366 ms (34.4s) | 전체 호출 평균 |
| 중앙값 레이턴시 | 37,290 ms (37.3s) |  |
| P90 레이턴시 | 50,420 ms (50.4s) | 단일 실행 9건 기준 nearest-rank |
| P95 레이턴시 | 50,420 ms (50.4s) | 단일 실행 9건 기준 nearest-rank |
| 최대 레이턴시 | 50,420 ms (50.4s) | `jy_questioner` 최초 호출 |
| 최소 레이턴시 | 20,380 ms (20.4s) | `jy_reviewer` 재시도 호출 |

**요약 해석:**

- 전체 LLM 호출 9건이 모두 성공하여 단일 실행 기준 안정성 문제는 관찰되지 않았다.
- 총 LLM 시간은 약 309.3초이며, 호출 평균은 34.4초로 여전히 실시간 UX에는 부담이 큰 수준이다.
- 60초 초과 호출은 없었지만, 40초 초과 호출이 2건 발생했다.
- 재시도 경로가 실행되면서 `questioner`, `predictor`, `driller`, `reviewer`가 추가로 1회씩 호출되었고, 이로 인해 단일 실행 토큰이 100K tokens를 초과했다.
- `interview_graph_JY` 로직상 `build_state`, `scorer`, `retry_questioner`, `selector`, `final_formatter`는 LLM 호출 없이 상태 구성, 점수 계산, 라우팅, 최종 포맷팅을 담당한다.

---

## 2. 노드별 성능 분석

### 2-1. 노드별 레이턴시

| 노드 | 호출 수 | 평균 레이턴시 | 중앙값 | P95 | 최대값 | 최솟값 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| jy_analyzer | 1 | 48,260 ms | 48,260 ms | 48,260 ms | 48,260 ms | 48,260 ms |
| jy_questioner | 2 | 43,855 ms | 43,855 ms | 50,420 ms | 50,420 ms | 37,290 ms |
| jy_predictor | 2 | 39,070 ms | 39,070 ms | 39,100 ms | 39,100 ms | 39,040 ms |
| jy_driller | 2 | 25,745 ms | 25,745 ms | 28,490 ms | 28,490 ms | 23,000 ms |
| jy_reviewer | 2 | 21,835 ms | 21,835 ms | 23,290 ms | 23,290 ms | 20,380 ms |

**레이턴시 기준 노드 순위 (느린 순):**  
`jy_analyzer` > `jy_questioner` > `jy_predictor` > `jy_driller` > `jy_reviewer`

**관찰 사항:**

- 기존 예시의 baseline과 달리, 이번 실행에서는 `reviewer`가 병목이 아니었다.
- 가장 느린 단일 호출은 최초 `jy_questioner` 50.42초이며, 두 번째로 느린 호출은 `jy_analyzer` 48.26초이다.
- `jy_reviewer`는 평균 21.84초로 가장 빠른 LLM 노드였다.
- `jy_predictor`는 최초/재시도 모두 약 39초로 매우 안정적이지만, 절대 시간은 낮지 않다.

### 2-2. 노드별 토큰 사용량

| 노드 | 평균 Input | 평균 Output | 평균 Total | I/O 비율 |
| --- | ---: | ---: | ---: | ---: |
| jy_analyzer | 2,814 | 3,451 | 6,265 | 0.82 : 1 |
| jy_questioner | 7,428 | 4,662 | 12,090 | 1.59 : 1 |
| jy_predictor | 7,830 | 3,727 | 11,557 | 2.10 : 1 |
| jy_driller | 9,430 | 2,900 | 12,330 | 3.25 : 1 |
| jy_reviewer | 8,664 | 2,312 | 10,975 | 3.75 : 1 |

**관찰 사항:**

- 평균 Total 토큰은 `jy_driller`가 12,330 tokens로 가장 높다.
- `jy_questioner`는 평균 Output 4,662 tokens로 출력량이 가장 많고, 레이턴시도 두 번째로 높다.
- `jy_analyzer`는 Input보다 Output이 더 큰 유일한 노드이며, 단일 호출 기준 48.26초로 느리다. 문서 분석 결과의 생성 분량이 지연에 영향을 주었을 가능성이 있다.
- `jy_reviewer`는 I/O 비율이 3.75:1로 Input 편중이 가장 강하지만, 레이턴시는 가장 낮았다.

### 2-3. 노드별 레이턴시 구간 분포

| 노드 | 0~20s | 20~40s | 40~60s | 60s 초과 |
| --- | ---: | ---: | ---: | ---: |
| jy_analyzer | 0건 (0.0%) | 0건 (0.0%) | 1건 (100.0%) | 0건 (0.0%) |
| jy_questioner | 0건 (0.0%) | 1건 (50.0%) | 1건 (50.0%) | 0건 (0.0%) |
| jy_predictor | 0건 (0.0%) | 2건 (100.0%) | 0건 (0.0%) | 0건 (0.0%) |
| jy_driller | 0건 (0.0%) | 2건 (100.0%) | 0건 (0.0%) | 0건 (0.0%) |
| jy_reviewer | 0건 (0.0%) | 2건 (100.0%) | 0건 (0.0%) | 0건 (0.0%) |

**핵심 발견:**

- 전체 9건 중 7건이 20~40초 구간에 위치한다.
- 40~60초 구간은 `jy_analyzer`, `jy_questioner`에서만 발생했다.
- 60초 초과 호출은 없으므로 극단적 tail latency는 이번 단일 실행에서는 확인되지 않았다.

---

## 3. 모델 × 노드 교차 테이블

> 현재 모든 LLM 호출에서 동일 모델 `gpt-5-mini`를 사용하고 있어 모델 간 비교는 불가능하다. 다만 노드별 토큰/레이턴시 특성이 달라 추후 Model Routing 실험의 기준값으로 사용할 수 있다.

| 모델 | 노드 | 호출 수 | 평균 Total 토큰 | 평균 레이턴시 |
| --- | --- | ---: | ---: | ---: |
| gpt-5-mini | jy_analyzer | 1 | 6,265 | 48,260 ms |
| gpt-5-mini | jy_questioner | 2 | 12,090 | 43,855 ms |
| gpt-5-mini | jy_predictor | 2 | 11,557 | 39,070 ms |
| gpt-5-mini | jy_driller | 2 | 12,330 | 25,745 ms |
| gpt-5-mini | jy_reviewer | 2 | 10,975 | 21,835 ms |
| **합계** | **전체** | **9** | **11,130 avg** | **34,366 ms** |

---

## 4. 실행 경로별 집계

| 구간 | 호출 수 | 총 소비 토큰 | 평균 레이턴시 | 포함 LLM 노드 |
| --- | ---: | ---: | ---: | --- |
| 최초 경로 | 5 | 49,655 | 36,802 ms | jy_analyzer, jy_questioner, jy_predictor, jy_driller, jy_reviewer |
| 재시도 경로 | 4 | 50,511 | 31,315 ms | jy_questioner, jy_predictor, jy_driller, jy_reviewer |
| 전체 | 9 | 100,166 | 34,366 ms | 전체 LLM 호출 |

**관찰 사항:**

- 재시도 경로는 analyzer를 다시 실행하지 않지만, 총 토큰은 50,511 tokens로 최초 경로보다 약간 높다.
- 재시도 경로의 평균 레이턴시는 31.3초로 최초 경로 36.8초보다 낮다.
- 재시도 경로에서 `jy_questioner` 입력 토큰이 9,770 tokens로 증가했다. 이는 기존 질문, 리뷰 결과, 점수, retry feedback이 프롬프트에 포함되기 때문으로 해석된다.
- 현재 그래프는 코드 기준으로 `questioner -> predictor -> driller -> reviewer`가 순차 실행된다. 따라서 재시도 발생 시 end-to-end 시간이 크게 증가한다.

---

## 5. 전체 레이턴시 구간 분포

| 구간 | 건수 | 비율 | 누적 비율 |
| --- | ---: | ---: | ---: |
| 0 ~ 20s | 0 | 0.0% | 0.0% |
| 20 ~ 40s | 7 | 77.8% | 77.8% |
| 40 ~ 60s | 2 | 22.2% | 100.0% |
| 60s 초과 | 0 | 0.0% | 100.0% |

- 전체 호출의 77.8%가 40초 이내에 완료된다.
- 40초를 초과한 호출은 `jy_analyzer`, 최초 `jy_questioner` 2건이다.
- 60초 초과 호출은 없지만, 단일 실행 전체 LLM 시간이 309초이므로 그래프 단위 체감 시간은 여전히 크다.

---

## 6. 식별된 문제점 및 개선 시나리오

### 문제 요약

| # | 문제 | 영향 노드 | 심각도 |
| --- | --- | --- | --- |
| P1 | 재시도 발생 시 LLM 호출이 5회에서 9회로 증가 | 전체, 특히 questioner 이후 | 높음 |
| P2 | 단일 실행 총 토큰 100,166 tokens로 비용/시간 부담 큼 | 전체 | 높음 |
| P3 | jy_questioner 출력량 과다 및 최대 레이턴시 발생 | jy_questioner | 높음 |
| P4 | jy_analyzer 단일 호출 레이턴시 48.26초 | jy_analyzer | 중간 |
| P5 | predictor, driller, reviewer가 순차 실행되어 end-to-end 시간 누적 | predictor, driller, reviewer | 중간 |
| P6 | 모든 노드에 동일 모델 적용 | 전체 | 중간 |

### 개선 시나리오 5종

**시나리오 1: 재시도 범위 축소 및 부분 재생성 강화**

- 현황: 재시도 경로에서 `questioner -> predictor -> driller -> reviewer` 전체가 다시 실행됨
- 개선 방향: 낮은 점수 질문 ID가 1~2개일 때 해당 질문만 재생성하고, downstream 노드도 대상 질문만 처리하도록 제한
- 기대 효과: 재시도 경로 토큰 50,511 tokens를 대폭 축소, end-to-end 시간 감소

**시나리오 2: questioner 출력 제한 및 스키마 압축**

- 현황: `jy_questioner` 평균 Output 4,662 tokens, 최대 레이턴시 50.42초
- 개선 방향: `generation_basis`, `evaluation_guide`, `document_evidence`의 문장 수 제한, 후보 질문 수와 필드별 길이 상한 명시
- 기대 효과: questioner 레이턴시와 output token 동시 감소

**시나리오 3: analyzer 결과 요약/압축**

- 현황: `jy_analyzer`는 Input 2,814 tokens 대비 Output 3,451 tokens로 출력이 더 큼
- 개선 방향: analyzer 출력 필드를 질문 생성에 필요한 `risk`, `evidence`, `job_fit`, `question_points` 중심으로 제한
- 기대 효과: analyzer 자체 레이턴시 감소 및 이후 questioner/predictor/driller 입력 컨텍스트 감소

**시나리오 4: predictor/driller 병렬화 가능성 검토**

- 현황: 현재 그래프는 `questioner -> predictor -> driller -> reviewer` 순차 구조
- 제약: `driller`는 예상 답변을 입력으로 사용하므로 predictor 결과에 의존함
- 개선 방향: driller가 반드시 predicted answer를 필요로 하지 않는 모드라면 `predictor`와 `driller`를 questioner 이후 병렬화하거나, reviewer 직전 join 구조로 변경
- 기대 효과: 그래프 단위 end-to-end 시간 단축

**시나리오 5: 노드별 모델 라우팅 적용**

- 현황: 모든 노드가 `gpt-5-mini` 사용
- 개선 방향: reviewer처럼 상대적으로 짧고 판정 중심인 노드는 더 경량 모델 실험, analyzer/questioner는 품질 유지 모델 사용
- 기대 효과: 품질 영향이 낮은 노드부터 비용 및 레이턴시 절감

---

## 7. 베이스라인 수치 정리 (추후 비교용)

| 항목 | 기준값 |
| --- | ---: |
| 총 LLM 호출 수 | 9 |
| 총 Input tokens | 69,515 |
| 총 Output tokens | 30,651 |
| 총 tokens | 100,166 |
| 총 LLM 시간 | 309.29초 |
| 평균 호출 레이턴시 | 34.4초 |
| P95 호출 레이턴시 | 50.4초 |
| 최대 호출 레이턴시 | 50.4초 |
| 60초 초과 호출 비율 | 0.0% |
| 재시도 경로 토큰 비중 | 50.4% |
| 최다 평균 토큰 노드 | jy_driller, 12,330 tokens |
| 최장 평균 레이턴시 노드 | jy_analyzer, 48.26초 |
| 최장 단일 레이턴시 노드 | jy_questioner, 50.42초 |

> 이 수치들은 `interview_graph_JY` 초기 구현의 단일 실행 기준값이다. 개선 실험 후에는 특히 `총 LLM 시간`, `재시도 경로 토큰`, `questioner output tokens`, `analyzer latency`, `end-to-end 실행 시간`을 우선 비교 지표로 삼는 것이 적절하다.