# 현석 LangGraph AS-IS 분석

## 1. 문서 목적

본 문서는 HR Copilot의 기본 질문 생성 파이프라인인 `backend/ai/interview_graph` 기준으로 현재 LangGraph 구조, 각 노드의 역할, 질문 생성 및 재생성 흐름, LLM 사용량 기록 방식을 정리한다.

분석 대상 파일은 다음과 같다.

- `backend/ai/interview_graph/state.py`
- `backend/ai/interview_graph/schemas.py`
- `backend/ai/interview_graph/prompts.py`
- `backend/ai/interview_graph/nodes.py`
- `backend/ai/interview_graph/router.py`
- `backend/ai/interview_graph/runner.py`
- `backend/ai/interview_graph/llm_usage.py`

## 2. 전체 실행 흐름

현재 기본 LangGraph는 지원자 문서와 세션 정보를 입력받아 면접 질문, 예상 답변, 꼬리 질문, 리뷰, 점수를 생성한 뒤 최종 질문 목록을 반환한다.

```text
build_state
 -> analyzer
 -> questioner
 -> selector_lite
 -> predictor
 -> driller
 -> reviewer
 -> scorer
 -> route_after_scoring
    -> retry_questioner
    -> retry_driller
    -> selector
 -> final_formatter
```

실행 진입점은 `runner.py`의 `run_interview_question_graph()`이다. 이 함수는 `CandidateInterviewPrepInput`을 받아 LangGraph 초기 상태를 구성하고, 각 노드 실행 결과에서 `llm_usages`를 수집한 뒤 최종적으로 `QuestionGenerationResponse`를 반환한다.

## 3. 입력 데이터 흐름

세션 생성 후 질문 생성 백그라운드 작업이 실행되면 `SessionGenerationPayloadAssembler`가 다음 정보를 조립한다.

- 세션 정보: `session_id`, `manager_id`, `candidate_id`, `target_job`, `difficulty_level`, `prompt_profile_id`
- 지원자 정보: 이름, 이메일, 전화번호, 지원 직무, 상태
- 지원자 문서: 문서 ID, 문서 유형, 제목, 추출 텍스트
- 프롬프트 프로필: 시스템 프롬프트, 출력 스키마, 대상 직무

이 데이터는 `runner.py`에서 `AgentState` 초기값으로 변환된다.

## 4. State 구조

`state.py`는 LangGraph 실행 중 공유되는 상태를 정의한다.

### InputState

초기 입력 값이다.

- `session_id`
- `candidate_id`
- `candidate_name`
- `target_job`
- `difficulty_level`
- `prompt_profile`
- `documents`
- `additional_instruction`
- `human_action`
- `target_question_ids`

### WorkflowState

각 노드가 생성하는 중간 산출물이다.

- `candidate_context`
- `document_analysis`
- `questions`
- `answers`
- `follow_ups`
- `reviews`
- `scores`
- `review_summary`

### ControlState

재시도와 라우팅 제어에 사용된다.

- `retry_feedback`
- `retry_count`
- `max_retry_count`
- `questioner_retry_count`
- `driller_retry_count`
- `max_questioner_retry_count`
- `max_driller_retry_count`
- `node_warnings`

### ObservabilityState

LLM 호출 비용과 토큰 추적에 사용된다.

- `llm_usages`

### OutputState

최종 응답을 담는다.

- `final_response`

## 5. 노드별 역할

### 5.1 build_state

지원자 문서, 세션 정보, 직무 정보, 난이도 정보를 하나의 `candidate_context` 텍스트로 병합한다. 이후 노드들이 공통으로 참조할 수 있는 입력 문맥을 만드는 전처리 노드이다.

역할 비유: 접수 담당자

### 5.2 analyzer

지원자 문서와 채용 기준을 분석하여 다음 정보를 생성한다.

- 강점
- 약점
- 리스크
- 문서 근거
- 직무 적합성
- 면접에서 검증할 포인트

역할 비유: 서류 분석관

### 5.3 questioner

`analyzer` 결과를 기반으로 면접 질문 후보를 생성한다. 기본 생성 개수는 8개이다.

재생성 요청이 있는 경우 `target_question_ids` 개수에 맞춰 해당 질문만 다시 생성하도록 프롬프트 지시가 변경된다.

역할 비유: 면접 질문 설계자

### 5.4 selector_lite

토큰 절감을 위해 질문 후보 중 일부를 먼저 선별한다. 현재는 8개 질문 후보 중 5개를 선택한다.

이 노드는 LLM 호출 없이 내부 정렬 로직으로 동작한다. 문서 근거, 리스크 검증 여부, 카테고리 다양성 등을 기준으로 이후 고비용 노드에 넘길 질문을 줄인다.

역할 비유: 1차 편집자

### 5.5 predictor

선별된 질문에 대해 지원자가 실제로 답변할 가능성이 있는 예상 답변을 생성한다.

출력 항목은 다음과 같다.

- `question_id`
- `predicted_answer`
- `predicted_answer_basis`
- `answer_confidence`
- `answer_risk_points`

역할 비유: 지원자 답변 예측관

### 5.6 driller

각 질문과 예상 답변을 기반으로 꼬리 질문을 생성한다. 예상 답변의 모호함, 근거 부족, 과장 가능성 등을 검증하는 목적이다.

출력 항목은 다음과 같다.

- `question_id`
- `follow_up_question`
- `follow_up_basis`
- `drill_type`

역할 비유: 심층 면접관

### 5.7 reviewer

생성된 질문, 예상 답변, 꼬리 질문을 HR 기준으로 검토한다.

검토 기준은 다음과 같다.

- 직무 관련성
- 문서 근거
- 리스크 검증력
- 면접 활용성
- 공정성
- 중복 위험

결과는 `approved`, `needs_revision`, `rejected` 중 하나로 반환된다.

역할 비유: HR 품질 검수관

### 5.8 scorer

각 질문을 0~100점으로 정량 평가한다. 리뷰 결과와 질문 품질을 종합하여 점수, 사유, 품질 플래그를 생성한다.

추가로 `review_summary`를 만들어 라우터가 재시도 여부를 판단할 수 있게 한다.

주요 요약 항목은 다음과 같다.

- 승인 질문 수
- 반려 질문 수
- 평균 점수
- 낮은 점수 질문 ID
- 낮은 점수 질문 수
- 점수 분포
- 주요 품질 이슈
- 리뷰 상태별 개수
- 질문 재작성 대상 ID
- 꼬리 질문 이슈 대상 ID

역할 비유: 정량 평가관

### 5.9 route_after_scoring

`router.py`에 정의된 조건부 라우팅 함수이다. `scorer` 결과를 기준으로 다음 노드를 결정한다.

분기 결과는 다음 중 하나이다.

- `retry_questioner`
- `retry_driller`
- `selector`

판단 기준은 다음과 같다.

- 전체 재시도 횟수가 최대치에 도달했는지
- 꼬리 질문 품질 이슈가 있는지
- 낮은 점수 질문이 1~2개인지
- 낮은 점수 질문이 과반인지
- 승인 질문 수가 부족한지
- 반려 질문이 있는지
- 수정 필요 리뷰가 있는지

역할 비유: 편집장

### 5.10 retry_questioner

질문 재생성을 위한 제어 상태를 갱신한다. 낮은 점수 질문이 1~2개인 경우 전체 질문을 다시 만들지 않고 해당 질문 ID만 대상으로 재생성하도록 설정한다.

현재 기준은 다음과 같다.

- `LOW_SCORE_THRESHOLD = 80`
- `PARTIAL_RETRY_MAX_LOW_SCORE_COUNT = 2`

즉, 점수가 80점 미만인 질문이 1~2개이면 해당 질문만 부분 재생성한다.

역할 비유: 질문 수정 지시자

### 5.11 retry_driller

꼬리 질문 품질 이슈가 있을 때 `driller`를 다시 실행하기 위한 제어 상태를 갱신한다.

역할 비유: 꼬리 질문 수정 지시자

### 5.12 selector

리뷰와 점수 결과를 기반으로 최종 질문 5개를 선택한다.

선택 시 고려 요소는 다음과 같다.

- 리뷰 승인 여부
- 점수
- 문서 근거 존재 여부
- 리스크 검증 질문 여부
- 카테고리 다양성
- 중복 질문 제거

역할 비유: 최종 선별자

### 5.13 final_formatter

최종 질문, 예상 답변, 꼬리 질문, 리뷰, 점수를 API 응답 스키마인 `QuestionGenerationResponse`로 변환한다.

응답 상태는 다음 중 하나이다.

- `completed`
- `partial_completed`
- `failed`

다음 조건 중 하나라도 해당되면 `partial_completed`가 될 수 있다.

- 추출된 문서 텍스트가 없음
- 최종 질문 수가 5개 미만
- 승인 질문 수가 5개 미만
- 최대 재시도 횟수에 도달
- 노드 경고가 존재

역할 비유: 최종 응답 편집자

## 6. 질문 생성 및 재생성 방식

현재 기본 생성 방식은 다음과 같다.

```text
질문 후보 8개 생성
 -> selector_lite에서 5개 선별
 -> 5개에 대해서만 예상 답변, 꼬리 질문, 리뷰, 점수화 수행
 -> 품질 이슈에 따라 부분 재생성 또는 최종 선택
```

토큰 절감 관점에서 중요한 점은 `selector_lite`이다. 모든 질문 후보에 대해 고비용 노드인 `predictor`, `driller`, `reviewer`, `scorer`를 실행하지 않고, 먼저 5개로 줄인 뒤 후속 처리를 수행한다.

## 7. 낮은 점수 질문 부분 재생성

현재 로직에는 낮은 점수 질문만 부분 재생성하는 흐름이 포함되어 있다.

`scorer_node`는 점수가 80점 미만인 질문 ID를 `low_score_question_ids`로 수집한다.

```text
score < 80 -> low_score_question_ids에 포함
```

`retry_questioner`는 낮은 점수 질문 개수가 1~2개인 경우 다음 값을 설정한다.

```text
target_question_ids = low_score_question_ids
human_action = "regenerate_question"
```

이후 `questioner`는 전체 질문을 다시 생성하지 않고 대상 질문 개수만큼 새 질문을 만든다. 생성된 질문은 기존 질문 목록에서 같은 ID 위치에 교체된다.

따라서 현재는 낮은 점수 질문이 소수일 때 전체 질문을 다시 생성하지 않아 토큰 낭비를 줄이는 구조이다.

단, 이 판단은 전체 8개 후보가 아니라 `selector_lite`로 선별된 5개 질문을 기준으로 이루어진다.

## 8. 스키마 AS-IS

`schemas.py`는 LangGraph 각 노드의 구조화 출력 모델을 정의한다.

주요 모델은 다음과 같다.

- `DocumentAnalysisOutput`
- `QuestionCandidate`
- `QuestionerOutput`
- `PredictedAnswer`
- `PredictorOutput`
- `FollowUpQuestion`
- `DrillerOutput`
- `ReviewResult`
- `ReviewerOutput`
- `ScoreResult`
- `ScorerOutput`
- `InterviewQuestionItem`
- `QuestionGenerationResponse`

현재 `QuestionCandidate.category`와 `FollowUpQuestion.drill_type`은 영어 값과 한국어 값이 함께 허용되어 있다.

예시:

```text
category:
- TECH
- JOB_SKILL
- EXPERIENCE
- RISK
- CULTURE_FIT
- MOTIVATION
- COMMUNICATION
- OTHER
- 한국어 카테고리 값

drill_type:
- ROLE_VERIFICATION
- METRIC_VERIFICATION
- DECISION_REASONING
- FAILURE_RECOVERY
- COLLABORATION
- RISK_RESPONSE
- OTHER
- 한국어 드릴 타입 값
```

이 구조는 LLM 출력 호환성은 높지만, 데이터 표준화와 대시보드 집계에는 불리하다.

## 9. LLM 사용량 기록 AS-IS

`llm_usage.py`는 LLM 호출을 감싸면서 다음 값을 수집한다.

- 노드명
- 모델명
- 입력 토큰
- 출력 토큰
- 총 토큰
- 예상 비용
- 호출 상태
- 소요 시간
- 에러 메시지

현재 비용 계산 기준 모델은 다음과 같다.

```text
gpt-4o-mini
- input: $0.15 / 1M tokens
- output: $0.60 / 1M tokens

gpt-4o
- input: $2.50 / 1M tokens
- output: $10.00 / 1M tokens
```

각 노드의 LLM 호출은 `call_structured_output_with_usage()`를 통해 실행된다. 이 함수는 최대 2회까지 호출을 시도하며, 성공 또는 실패 사용량을 `llm_usages`에 기록한다.

`runner.py`는 그래프 실행 중 각 노드의 `llm_usages`를 수집한 뒤 `save_llm_call_logs()`로 DB에 저장한다.

저장 대상 모델은 `LlmCallLog`이며 주요 저장 필드는 다음과 같다.

- `manager_id`
- `candidate_id`
- `prompt_profile_id`
- `interview_sessions_id`
- `model_name`
- `node_name`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost`
- `currency`
- `elapsed_ms`
- `call_status`
- `error_message`

## 10. 관측 및 대시보드 AS-IS

백엔드에는 `/llm-usage/summary` API가 존재한다. 이 API는 LLM 사용량을 다음 기준으로 집계한다.

- 전체 사용량
- 노드별 사용량
- 세션별 사용량
- 최근 호출 목록

프론트엔드에는 `LlmUsageDashboard`가 존재하며, 관리자 사이드바에서 `/manager/llm-usage`로 접근할 수 있다.

현재 대시보드는 노드별 비용 비중과 세션별 사용량을 확인하는 기반을 제공한다.

## 11. AS-IS 장점

현재 구조의 장점은 다음과 같다.

- LangGraph 노드가 역할별로 분리되어 있어 흐름을 추적하기 쉽다.
- 구조화 출력 모델을 사용해 LLM 응답을 Pydantic 모델로 검증한다.
- `selector_lite`를 통해 비싼 후속 노드 실행 전에 질문 수를 줄인다.
- 낮은 점수 질문이 일부일 경우 전체 재생성 대신 부분 재생성을 수행한다.
- 노드별 토큰, 비용, 시간, 실패 여부를 DB에 기록한다.
- LLM 사용량 대시보드로 운영 비용을 관찰할 수 있다.
- 실패 시 fallback 응답을 생성해 그래프 전체 실패를 줄인다.

## 12. AS-IS 한계

현재 구조의 한계는 다음과 같다.

### 12.1 카테고리 표준화 부족

질문 카테고리와 꼬리 질문 유형이 영어와 한국어를 동시에 허용한다. 이로 인해 저장 데이터의 일관성이 떨어지고, 카테고리별 집계나 필터링이 복잡해진다.

### 12.2 평가 독립성 부족

질문 생성, 리뷰, 점수화가 같은 그래프 내부에서 순차적으로 수행된다. 현재 구조는 생성자가 만든 질문을 같은 파이프라인이 평가하는 형태이므로, 제3자 검수 관점이 약하다.

### 12.3 후보 질문 수와 최종 질문 수의 균형

현재는 8개를 생성하고 5개를 선별한다. 후보 풀이 크지 않아 다양성 확보에는 한계가 있을 수 있다.

### 12.4 재생성 기준의 범위

부분 재생성은 `selector_lite` 이후의 5개 질문을 기준으로 한다. 즉, 최초 생성된 8개 전체에 대한 품질 평가 결과가 아니라 선별된 질문에 대해서만 점수 기반 재생성이 일어난다.

### 12.5 동시 대량 처리 구조

현재 질문 생성은 FastAPI `BackgroundTasks` 기반으로 실행된다. 지원자 다수를 동시에 처리하는 상황에서는 별도 작업 큐와 worker 기반 구조가 더 적합하다.

### 12.6 비용 개선 전후 비교 체계 부족

노드별 사용량은 기록되지만, 파이프라인 버전별 AS-IS/TO-BE 비교, 절감률, 후보자 1명당 평균 비용, 재시도 비용 등 개선 효과를 직접 설명하는 지표는 아직 부족하다.

## 13. AS-IS 요약

현재 현석 LangGraph는 다음 특징을 가진다.

```text
8개 질문 후보 생성
 -> 5개 사전 선별
 -> 예상 답변 생성
 -> 꼬리 질문 생성
 -> HR 기준 리뷰
 -> 정량 점수화
 -> 낮은 점수 또는 품질 이슈에 따라 재시도
 -> 최종 5개 질문 반환
 -> 노드별 LLM 사용량 저장
```

현재 구조는 이미 비용 절감을 위한 `selector_lite`와 부분 재생성 로직을 포함하고 있다. 다만 향후 개선을 위해서는 카테고리 한국어 표준화, 외부 평가자 노드 추가, 질문 후보 10개 확대, 대량 세션 처리용 큐 구조, 비용 개선 전후 비교 지표 강화가 필요하다.
