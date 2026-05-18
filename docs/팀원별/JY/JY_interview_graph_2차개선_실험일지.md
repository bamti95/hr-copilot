# 실험 개요

- **대상:** `interview_graph_JY`의 `selector_lite` 선별 경로 및 downstream 노드
- **한 줄 목적:** 최종 선별 전에 `predictor`/`driller`/`reviewer`가 전체 질문을 처리하던 구조를 개선하여 latency와 토큰 사용량을 줄인다
- **실험 유형**: Latency / 실행 그래프 구조 개선

---

# 문제 정의 및 관측 데이터

> 이 섹션에서는 "무엇이 문제인지"를 감이 아니라 관측된 현상으로 설명한다.

### 문제 현상

- 1차 개선으로 전체 토큰은 감소했지만 전체 처리 시간은 증가했다.
- 특히 `jy_predictor`가 토큰 감소 후에도 느리게 동작했다.
- 원인은 JY 그래프가 최종 선별 전에 `predictor`/`driller`/`reviewer`를 실행하는 구조였다.
- 최종적으로 5개 질문만 사용하더라도 `jy_predictor`는 `jy_questioner`가 생성한 8개 질문 전체에 대해 예상 답변을 생성하고 있었다.
- 입력 토큰은 줄었지만 구조화 출력은 질문 수만큼 생성되어야 하므로 출력량과 constrained decoding 시간이 충분히 줄지 않았다.

### 관측 데이터

|항목|1차 개선 후 AS-IS|2차 개선 후 TO-BE|변화|
|---|---|---|---|
|전체 지연 시간|424.25s|345.62s|↓ 78.63s (-18.5%)|
|전체 LLM 호출 수|9회|9회|동일|
|입력 토큰|49,551|41,312|↓ 8,239 (-16.6%)|
|출력 토큰|27,723|24,318|↓ 3,405 (-12.3%)|
|전체 토큰|77,274|65,630|↓ 11,644 (-15.1%)|
|호출 비용|$0.0000|$0.0000|변화 없음|
|성공률|100%|100%|유지|
|에러 유형|없음|없음|timeout/parsing error 미관측|

---

# 원인 가설

> 이 섹션에서는 원인을 단정하지 않고, 가능한 원인 후보를 세운다.

### 가설 후보

|번호|가설|그렇게 생각한 이유|확인 방법|
|---|---|---|---|
|H1|최종 선별 전 downstream 실행이 병목이다|최종 5개만 사용하지만 `predictor`/`driller`/`reviewer`가 8개 전체를 처리했다|`selector_lite`를 `questioner` 직후에 배치해 downstream 처리 질문 수 비교|
|H2|`jy_predictor`는 입력보다 출력 질문 수에 더 민감하다|예상 답변을 질문 수만큼 구조화 출력해야 하므로 constrained decoding 시간이 커진다|선별 전 8개 처리와 선별 후 5개 처리의 출력 토큰 및 시간 비교|
|H3|재시도 경로에서도 동일한 낭비가 반복된다|재시도 후에도 다시 전체 질문에 대해 downstream 노드가 실행될 수 있다|재시도 경로에도 `selector_lite`를 적용하고 노드별 usage 비교|
|H4|최종 selector는 품질 정렬에 필요하다|초기 선별만으로는 리뷰/점수 반영 후 최종 정렬을 대체하기 어렵다|최종 `selector`는 유지하고 실행 순서만 변경|

---

# 실험 설계

> 이 섹션에서는 무엇을 바꾸고, 무엇은 유지했는지 분리해서 기록한다.

### 변경 내용

|구분|AS-IS|TO-BE|
|---|---|---|
|초기 실행 순서|`questioner -> predictor -> driller -> reviewer -> scorer`|`questioner -> selector_lite -> predictor -> driller -> reviewer -> scorer`|
|재시도 실행 순서|`retry_questioner -> questioner -> predictor -> driller -> reviewer -> scorer`|`retry_questioner -> questioner -> selector_lite -> predictor -> driller -> reviewer -> scorer`|
|downstream 처리 질문 수|`questioner`가 생성한 8개 전체 처리|`selector_lite`가 선별한 5개 중심으로 처리|
|공통 선별 로직|최종 selector 중심|`_select_question_candidates` 공통 로직 추가|
|최종 selector|최종 단계에서만 선별/정렬|유지. 리뷰/점수 반영 후 다시 정렬|
|그래프 메타데이터|기존 실행 순서 문자열|`selector_lite` 포함 실행 순서로 갱신|

### 코드 변경 위치

|파일|위치|내용|
|---|---|---|
|`backend/ai/interview_graph_JY/nodes.py`|line 182|공통 선별 로직 `_select_question_candidates` 추가|
|`backend/ai/interview_graph_JY/nodes.py`|line 510|`selector_lite_node` 추가|
|`backend/ai/interview_graph_JY/runner.py`|line 53|실행 순서를 `questioner -> selector_lite -> predictor`로 변경|
|`backend/ai/interview_graph_JY/runner.py`|graph metadata|메타데이터 `graph` 문자열을 새 실행 순서로 갱신|

### 변인 통제

|항목|유지 / 변경|내용|
|---|---|---|
|모델|🟢 유지|`gpt-5-mini` 유지|
|프롬프트|🟢 유지|1차 개선에서 적용한 analyzer/questioner 출력 압축 유지|
|테스트 입력|🟢 유지|동일 계열 HR Copilot 입력|
|temperature|🟢 유지|기존 설정 유지|
|max tokens|🟢 유지|명시적 변경 없음|
|State 구조|🟢 유지|1차 개선의 `target_question_ids` 기반 부분 재처리 유지|
|실행 그래프|🔴 변경|`selector_lite`를 `questioner` 직후에 추가|
|실행 횟수|🟢 유지|변경 전후 각 1회|

### 설계 근거

- 최종적으로 사용할 질문이 5개라면, 예상 답변/꼬리질문/리뷰도 선별된 질문에 대해서만 생성하는 것이 효율적이다.
- `jy_predictor`는 질문마다 구조화된 예상 답변을 생성하므로 처리 질문 수를 줄이면 출력 토큰과 constrained decoding 시간이 함께 줄어들 가능성이 높다.
- 최종 `selector`는 제거하지 않고 유지해야 `reviewer`와 `scorer` 결과를 반영한 최종 정렬이 가능하다.
- `selector_lite`는 LLM 호출 없이 후보를 먼저 줄이는 경량 선별 노드로 두어 전체 LLM 호출 수를 늘리지 않는다.

---

# 실험 결과

### Before vs After

|지표|1차 개선 후 AS-IS|2차 개선 후 TO-BE|변화|
|---|---|---|---|
|전체 응답 시간|424.25s|345.62s|↓ 78.63s (-18.5%)|
|전체 LLM 호출 수|9회|9회|동일|
|입력 토큰|49,551|41,312|↓ 8,239 (-16.6%)|
|출력 토큰|27,723|24,318|↓ 3,405 (-12.3%)|
|전체 토큰|77,274|65,630|↓ 11,644 (-15.1%)|
|호출 비용|$0.0000|$0.0000|변화 없음|
|성공률|100%|100%|유지|
|에러 발생 횟수|0회|0회|유지|

### 노드별 상세 비교

|노드|1차 개선 시간|2차 개선 시간|1차 개선 총 토큰|2차 개선 총 토큰|해석|
|---|---|---|---|---|---|
|`jy_analyzer`|67.36s|47.44s|6,486|5,932|토큰과 시간 모두 감소|
|`jy_questioner`|62.59s|59.10s|8,311|8,344|토큰은 유사, 시간 소폭 감소|
|`jy_predictor`|69.45s|36.85s|8,521|6,551|선별 후 처리로 시간 크게 감소|
|`jy_driller`|37.80s|21.98s|8,415|5,870|처리 질문 수 감소 효과 확인|
|`jy_reviewer`|30.11s|22.24s|8,448|6,060|처리 질문 수 감소 효과 확인|
|`jy_questioner` (재시도)|41.47s|63.40s|10,339|10,748|재시도 questioner는 시간 증가|
|`jy_predictor` (재시도)|61.29s|39.34s|8,246|6,721|재시도 경로에서도 시간 감소|
|`jy_driller` (재시도)|34.52s|29.84s|10,281|8,265|토큰과 시간 모두 감소|
|`jy_reviewer` (재시도)|19.66s|25.42s|8,227|7,139|토큰은 감소했으나 시간은 증가|

### 실행 경로 구조

```text
LangGraph
├─ build_state
├─ jy_analyzer (47.44초)
├─ jy_questioner (59.10초)
├─ selector_lite
├─ jy_predictor (36.85초)
├─ jy_driller (21.98초)
├─ jy_reviewer (22.24초)
├─ scorer
└─ retry_questioner 재시도 경로
   ├─ jy_questioner (63.40초)
   ├─ selector_lite
   ├─ jy_predictor (39.34초)
   ├─ jy_driller (29.84초)
   ├─ jy_reviewer (25.42초)
   ├─ scorer
   ├─ selector
   └─ final_formatter
```

### LLM Usage 상세

|#|노드|모델|입력|출력|총 토큰|시간|비용|상태|
|---|---|---|---|---|---|---|---|---|
|1|`jy_analyzer`|gpt-5-mini|2,958|2,974|5,932|47.44초|$0.0000|성공|
|2|`jy_questioner`|gpt-5-mini|3,957|4,387|8,344|59.10초|$0.0000|성공|
|3|`jy_predictor`|gpt-5-mini|4,210|2,341|6,551|36.85초|$0.0000|성공|
|4|`jy_driller`|gpt-5-mini|4,012|1,858|5,870|21.98초|$0.0000|성공|
|5|`jy_reviewer`|gpt-5-mini|4,473|1,587|6,060|22.24초|$0.0000|성공|
|6|`jy_questioner`|gpt-5-mini|6,713|4,035|10,748|63.40초|$0.0000|성공|
|7|`jy_predictor`|gpt-5-mini|4,276|2,445|6,721|39.34초|$0.0000|성공|
|8|`jy_driller`|gpt-5-mini|5,706|2,559|8,265|29.84초|$0.0000|성공|
|9|`jy_reviewer`|gpt-5-mini|5,007|2,132|7,139|25.42초||성공|

### 결과 해석

**✅ 성공한 부분:**

- 전체 처리 시간 **18.5% 감소** (424.25s → 345.62s)
- 전체 토큰 **15.1% 감소** (77,274 → 65,630)
- 입력 토큰 **16.6% 감소** (49,551 → 41,312)
- 출력 토큰 **12.3% 감소** (27,723 → 24,318)
- `jy_predictor` 시간 크게 감소 (69.45s → 36.85s)
- 재시도 `jy_predictor` 시간도 감소 (61.29s → 39.34s)
- LLM 호출 수 9회 유지
- 안정성 유지 (성공률 100%, 에러 0회)

**❌ 실패한 부분:**

- 전체 처리 시간은 개선됐지만 여전히 345.62초로 절대 latency가 높다.
- 재시도 `jy_questioner` 시간은 증가했다 (41.47s → 63.40s).
- 재시도 `jy_reviewer`는 토큰 감소에도 시간이 증가했다 (19.66s → 25.42s).
- 비용 로그가 여전히 `$0.0000` 또는 공란으로 기록되어 비용 관측 신뢰성이 낮다.

**🔍 주요 발견:**

- `selector_lite`를 `questioner` 직후에 배치하는 구조 변경은 latency와 토큰 사용량을 동시에 줄였다.
- `jy_predictor` 병목은 프롬프트 길이뿐 아니라 처리 질문 수와 구조화 출력량의 영향을 크게 받았다.
- 1차 개선에서 확인한 "토큰 감소가 latency 개선으로 바로 이어지지 않는다"는 한계는, 실행 순서 개선을 함께 적용해야 완화된다.
- 최종 selector를 유지하면서도 upstream에 경량 selector를 추가하는 방식은 품질 정렬과 성능 개선을 동시에 노릴 수 있다.

---

## 최종 결정

- **반영 여부:** 반영
- **결정 이유:**
    - 전체 처리 시간 18.5% 감소로 1차 개선의 latency 악화 문제를 일부 해소했다.
    - 전체 토큰 15.1% 추가 감소로 비용 및 State 전달량 개선 효과를 확인했다.
    - `jy_predictor`와 재시도 `jy_predictor` 모두 큰 폭으로 개선되어 병목 원인 가설이 타당했다.
    - LLM 호출 수 증가 없이 구조 변경만으로 개선이 발생했다.
    - 최종 `selector`를 유지해 리뷰/점수 기반 최종 정렬 흐름도 보존했다.
    - 다만 절대 처리 시간은 여전히 높으므로 재시도 경로와 `questioner` 최적화는 추가 실험이 필요하다.

---

# 검증

- `uv run python -m compileall ai/interview_graph_JY` 통과
- `uv run python -c "from ai.interview_graph_JY.runner import _build_graph; _build_graph(); print('graph ok')"` 통과

---

# 회고

### 알게 된 점

- downstream LLM 노드의 latency는 입력 토큰뿐 아니라 처리 대상 개수와 구조화 출력 개수에 크게 좌우된다.
- 최종 산출물이 5개라면, 최종 단계까지 8개 전체를 유지하는 구조는 `predictor`/`driller`/`reviewer`에서 불필요한 출력 생성을 만든다.
- LLM 호출 수를 늘리지 않아도 LangGraph 노드 순서와 State 전달 범위를 조정하면 실질적인 latency 개선이 가능하다.
- `selector_lite`처럼 비LLM 경량 노드를 앞단에 추가하는 방식은 비용 증가 없이 downstream 부하를 줄이는 데 효과적이다.

### 예상과 달랐던 점

- `jy_predictor` 개선 폭이 가장 컸다. 단순 입력 토큰 감소보다 질문 수 선별이 더 직접적인 병목 완화 요인이었다.
- 재시도 `jy_questioner`는 2차 개선 이후 오히려 시간이 증가했다.
- 일부 노드는 토큰이 줄어도 시간이 증가해, 모델 응답 시간 변동성과 출력 제약의 영향이 여전히 존재했다.

### 추가로 확인해야 할 점

- 동일 입력으로 3~5회 반복 실행해 평균 latency와 분산 비교 필요
- `selector_lite`가 최종 질문 품질이나 다양성을 낮추지 않는지 정성 평가 필요
- 재시도 `jy_questioner`의 시간 증가 원인 분석 필요
- 재시도 경로에서 `target_question_ids`와 `selector_lite`가 기대한 범위만 처리하는지 로그 검증 필요
- 비용 로그 집계 방식 점검 ($0.0000 및 공란 기록 문제)
- 절대 latency를 줄이기 위해 `predictor`/`driller`/`reviewer` 병렬화 가능성 검토 필요

### 한 줄 정리

> LangGraph 기반 HR Copilot의 `interview_graph_JY`에서 최종 5개 질문만 사용할 예정임에도 `predictor`/`driller`/`reviewer`가 8개 전체 질문을 처리하던 구조를 병목으로 보고, `questioner` 직후 `selector_lite`를 추가해 downstream 처리 대상을 먼저 줄였다. 그 결과 1차 개선 대비 전체 처리 시간은 18.5%, 전체 토큰은 15.1% 추가 감소했으며, 특히 `jy_predictor` 시간이 69.45초에서 36.85초로 크게 줄어 구조 변경 효과를 확인했다.
