# HR Copilot 2차 MVP 고도화 기획안

## 1. 기획 목적

2차 MVP의 목적은 HR 담당자가 대량 지원자를 빠르게 등록하고, AI 분석/질문 생성 작업을 안정적으로 실행하며, 최종 면접 대상자를 선별할 수 있는 업무 흐름을 만드는 것입니다.

1차 MVP가 개별 지원자/개별 세션 중심이었다면, 2차 MVP는 다음 방향으로 고도화합니다.

```text
개별 처리
→ 대량 등록
→ 안정적인 작업 큐
→ AI 분석 일괄 처리
→ 면접 대상자 선별
```

## 2. 2차 MVP 핵심 목표

| 목표 | 설명 |
|---|---|
| 지원자 등록 효율화 | Excel/CSV 기반 다중 지원자 등록 |
| AI 작업 안정화 | BackgroundTasks를 실제 작업 큐 구조로 고도화 |
| 대량 처리 가능화 | 문서 분석/질문 생성 작업을 job 단위로 관리 |
| HR 의사결정 지원 | 서류 합격자 기반 면접 대상자 추천/선별 |
| 운영 가시성 확보 | 작업 상태, 실패, 재시도, 진행률 확인 |

## 3. 2차 MVP 우선순위

## Priority 1. 지원자 일괄 등록

### 3.1 문제 정의

현재 지원자는 한 명씩 등록해야 합니다. 채용 공고 하나에 수십 명 이상의 지원자가 들어오는 상황에서는 HR 담당자의 반복 입력 비용이 큽니다.

### 3.2 목표

CSV/Excel 업로드를 통해 여러 지원자를 한 번에 등록합니다.

최소 목표:

- Excel/CSV 업로드
- 필수 컬럼 검증
- 중복 이메일 검증
- 미리보기/오류 표시
- 정상 row만 등록

### 3.3 사용자 흐름

```text
지원자 일괄 등록 화면 진입
→ 템플릿 다운로드
→ Excel/CSV 업로드
→ 시스템 검증
→ 미리보기 확인
→ 정상 row만 등록
→ 결과 확인
```

### 3.4 주요 기능

| 기능 | 설명 | MVP 포함 |
|---|---|---|
| 템플릿 다운로드 | 지원자 등록용 Excel 템플릿 제공 | Y |
| 파일 업로드 | CSV/Excel 파일 업로드 | Y |
| 필수 컬럼 검증 | 이름, 이메일, 연락처, 직무, 지원 상태 확인 | Y |
| 중복 검증 | 파일 내부 중복, DB 기존 이메일 중복 확인 | Y |
| 미리보기 | 등록 전 row별 상태 확인 | Y |
| 정상 row 등록 | 오류 row 제외 후 등록 | Y |
| 오류 다운로드 | 실패 row Excel 다운로드 | N |
| 문서 ZIP 매핑 | 문서 파일 자동 매핑 | N |

### 3.5 API 설계

```http
GET /candidates/bulk/template
POST /candidates/bulk/preview
POST /candidates/bulk/import
GET /candidates/bulk/jobs/{job_id}
```

### 3.6 성공 기준

- HR 담당자가 100명 규모의 지원자 목록을 한 번에 업로드할 수 있다.
- 오류 row와 정상 row가 명확히 분리된다.
- 정상 row만 등록할 수 있다.
- 등록 결과가 성공/실패 수치로 표시된다.

## Priority 2. 작업 큐 고도화

### 4.1 문제 정의

현재 질문 생성은 FastAPI `BackgroundTasks` 기반입니다. 이는 응답 이후 같은 서버 프로세스에서 작업을 실행하는 방식으로, 실제 운영 큐로는 한계가 있습니다.

현재 한계:

- 서버 재시작 시 작업 유실 가능
- 작업 재시도 정책 없음
- 동일 세션 중복 실행 방지 부족
- worker 수 제어 없음
- 대량 작업 처리에 취약
- 작업 상태 추적이 세션 중심으로 제한됨

### 4.2 목표

AI 작업을 job 단위로 관리하고, 큐/워커 구조를 도입합니다.

권장 구조:

```text
FastAPI
→ ai_job 생성
→ Redis/Celery 큐 등록
→ Worker 실행
→ 상태 업데이트
→ 프론트 진행률 표시
```

### 4.3 MVP 범위

2차 MVP에서는 완전한 분산 큐까지 한 번에 가지 않고, 다음 단계로 나누는 것을 권장합니다.

1단계:

- `ai_job` 테이블 도입
- 작업 상태를 job 단위로 저장
- 동일 session 중복 실행 방지
- 실패 상태/에러 메시지 기록

2단계:

- Celery + Redis 도입
- worker concurrency 설정
- 실패 재시도
- 작업 취소

### 4.4 ai_job 모델 초안

```text
id
job_type
status
target_type
target_id
parent_job_id
graph_impl
priority
attempt_count
max_attempts
error_message
requested_by
started_at
completed_at
created_at
updated_at
deleted_at
```

### 4.5 job_type

| job_type | 설명 |
|---|---|
| BULK_CANDIDATE_IMPORT | 지원자 일괄 등록 |
| DOCUMENT_ANALYSIS | 문서 분석 |
| QUESTION_GENERATION | 면접 질문 생성 |
| QUESTION_REGENERATION | 선택 질문 재생성 |
| CANDIDATE_RANKING | 면접 대상자 랭킹 산정 |

### 4.6 status

```text
QUEUED
RUNNING
SUCCESS
PARTIAL_SUCCESS
FAILED
RETRYING
CANCELLED
```

### 4.7 동시성 정책

| 정책 | 설명 |
|---|---|
| 동일 세션 중복 방지 | 같은 session_id의 QUESTION_GENERATION이 QUEUED/RUNNING이면 새 작업 차단 |
| worker concurrency 제한 | OpenAI API rate limit을 고려해 worker 수 제한 |
| job timeout | 일정 시간 초과 시 FAILED 처리 |
| retry backoff | 실패 시 지수 백오프로 재시도 |
| priority | HR 수동 실행 작업을 batch 작업보다 우선 처리 |

### 4.8 성공 기준

- 질문 생성 작업이 job으로 기록된다.
- 같은 세션에 중복 질문 생성 작업이 등록되지 않는다.
- 실패 작업의 에러 메시지를 확인할 수 있다.
- 작업 상태가 `QUEUED → RUNNING → SUCCESS/FAILED`로 추적된다.

## Priority 3. 문서 분석/질문 생성 일괄 처리

### 5.1 문제 정의

지원자 일괄 등록이 가능해지면 후속 AI 작업도 대량으로 실행되어야 합니다. 개별 세션마다 수동으로 분석/질문 생성을 누르는 방식은 대량 채용에 맞지 않습니다.

### 5.2 목표

지원자 일괄 등록 후 선택 옵션에 따라 문서 분석과 면접 질문 생성을 자동으로 큐에 등록합니다.

### 5.3 처리 흐름

```text
지원자 일괄 등록 성공
→ candidate 생성
→ document 저장
→ DOCUMENT_ANALYSIS job 등록
→ 문서 분석 성공
→ interview_session 생성
→ QUESTION_GENERATION job 등록
→ 질문 생성 완료
```

### 5.4 MVP 범위

MVP 포함:

- 등록 성공 지원자에 대해 문서 분석 job 생성
- 문서 분석 성공 시 상태 업데이트
- 질문 생성은 수동 또는 옵션 기반으로 등록
- job 결과 화면에서 성공/실패 확인

MVP 제외:

- 문서 분석 실패 자동 복구
- 직무별 프롬프트 자동 추천
- 문서 품질 평가

### 5.5 성공 기준

- 일괄 등록 후 여러 문서 분석 작업이 자동 생성된다.
- 각 작업의 성공/실패 상태를 확인할 수 있다.
- 실패한 작업만 재실행할 수 있다.

## Priority 4. 최종 면접 대상자 선별

### 6.1 문제 정의

현재 시스템은 지원자별 질문 생성과 분석을 제공하지만, HR 담당자가 최종적으로 누구를 면접에 올릴지 결정하는 화면은 부족합니다.

### 6.2 목표

서류 합격자만 대상으로 AI 분석 결과와 질문 품질 점수를 활용해 면접 대상자 추천 랭킹을 제공합니다.

### 6.3 대상 범위

면접 대상자 선별은 전체 지원자가 아니라 **서류 합격자**만 대상으로 합니다.

예:

```text
candidate.apply_status = DOCUMENT_PASSED
```

또는 현재 시스템 상태값에 맞춰 다음과 같은 상태를 사용할 수 있습니다.

```text
DOCUMENT_PASSED
SCREENING_PASSED
INTERVIEW_READY
```

### 6.4 랭킹 산식 MVP

```text
최종 추천 점수 =
문서 분석 완료 점수
+ 질문 생성 완료 점수
+ 질문 평균 점수
+ approved 질문 비율
- rejected 질문 감점
- 낮은 score 감점
- 리스크 태그 감점
```

예시:

| 항목 | 배점 |
|---|---:|
| 문서 분석 완료 | 10 |
| 질문 생성 완료 | 10 |
| 질문 평균 점수 | 40 |
| approved 비율 | 20 |
| 리스크 감점 | -10 |
| rejected 감점 | -10 |

### 6.5 화면 구성

```text
[면접 대상자 선별]

상단 필터
- 직무
- 지원 상태
- 분석 완료 여부
- 질문 생성 상태

요약 카드
- 서류 합격자 수
- 면접 추천 수
- 검토 필요 수
- 분석/질문 생성 미완료 수

랭킹 테이블
- 순위
- 지원자
- 직무
- 추천 점수
- 질문 평균 점수
- approved 비율
- 리스크
- 추천 사유
- 액션
```

액션:

- 면접 대상 확정
- 보류
- 제외
- 분석 리포트 보기
- 질문 보기

### 6.6 상태 설계

최종 선별 상태는 candidate 또는 별도 screening result로 관리하는 것을 권장합니다.

```text
INTERVIEW_RECOMMENDED
INTERVIEW_CONFIRMED
INTERVIEW_HOLD
INTERVIEW_REJECTED
```

MVP에서는 candidate 상태값 확장으로 시작할 수 있고, 이력이 중요해지면 별도 테이블을 둡니다.

### 6.7 성공 기준

- 서류 합격자만 필터링된다.
- 추천 점수 기준으로 정렬된다.
- HR 담당자가 최종 면접 대상자를 확정할 수 있다.
- 확정/보류/제외 상태가 저장된다.

### 6.8 질문 생성 전 면접자 선별 그래프 설계

현재 지원자 관리 화면의 상단 액션 영역에는 `신규 등록`, `단체 지원자 등록`, `문서 일괄등록`, `분석 세션 생성` 버튼이 배치되어 있습니다. 2차 MVP에서는 이 영역에 `면접자 선별` 버튼을 추가하여, 질문 생성 전에 지원자와 문서 정보를 기반으로 면접 대상 후보를 먼저 추리는 흐름을 제공합니다.

권장 흐름은 다음과 같습니다.

```text
지원자 목록 조회
→ 지원자 선택 또는 검색/필터 조건 설정
→ 면접자 선별 버튼 클릭
→ 지원자 기본정보 + 문서 추출 정보 payload 조립
→ 서류검토 담당관 프롬프트 프로필 주입
→ screening_graph 실행
→ 후보자별 추천/보류/제외 결과 저장
→ HR 담당자가 면접 대상 확정
→ 확정자 기준 분석 세션 생성
→ 질문 생성 graph 실행
```

#### 6.8.1 화면 동작

| 상황 | 동작 |
|---|---|
| 선택된 지원자가 있는 경우 | 선택된 지원자를 선별 대상으로 사용 |
| 선택된 지원자가 없는 경우 | 현재 검색/필터 조건의 지원자를 대상으로 실행할지 확인 |
| 지원 직무 필터가 없는 경우 | 선별 실행 모달에서 target_job을 필수 선택 |
| 선별 프롬프트 프로필이 없는 경우 | 서류검토용 프롬프트 프로필 선택 또는 생성 유도 |
| 선별 완료 후 | 결과 모달 또는 결과 패널에서 점수, 추천 여부, 추천 사유, 리스크 표시 |
| HR 확정 후 | 후보자 상태를 면접 대상 상태로 변경하거나 분석 세션 생성 플로우로 연결 |

버튼 배치는 다음과 같이 구성합니다.

```text
검색 | 신규 등록 | 단체 지원자 등록 | 문서 일괄등록 | 면접자 선별 | 분석 세션 생성
```

#### 6.8.2 입력 payload 조립

면접자 선별 실행 시 각 지원자별로 다음 데이터를 조립합니다.

```json
{
  "candidate": {
    "candidate_id": 88,
    "name": "정지훈",
    "email": "jhoon94@naver.com",
    "phone": "010-2987-1472",
    "birth_date": "1994-01-01",
    "job_position": "SALES",
    "apply_status": "APPLIED"
  },
  "documents": [
    {
      "document_id": 1001,
      "document_type": "RESUME",
      "title": "정지훈_이력서.pdf",
      "extract_status": "COMPLETED",
      "extracted_text": "..."
    },
    {
      "document_id": 1002,
      "document_type": "PORTFOLIO",
      "title": "정지훈_포트폴리오.pdf",
      "extract_status": "COMPLETED",
      "extracted_text": "..."
    }
  ],
  "target_job": "SALES",
  "prompt_profile": {
    "id": 3,
    "profile_key": "SCREENING_SALES_REVIEWER",
    "system_prompt": "당신은 서류검토 담당관입니다...",
    "output_schema": {}
  },
  "screening_policy": {
    "recommend_threshold": 75,
    "hold_threshold": 55,
    "temperature": 0
  }
}
```

문서 텍스트는 토큰 사용량을 제어하기 위해 문서 타입별 우선순위를 둡니다.

| 문서 유형 | 처리 방식 |
|---|---|
| 이력서 | 가장 높은 우선순위로 포함 |
| 경력기술서 | 직무 적합도 판단 근거로 우선 포함 |
| 포트폴리오 | 프로젝트/성과 중심으로 포함 |
| 추출 실패 문서 | 본문 대신 파일명, 문서 유형, 실패 상태만 전달 |
| 문서 없음 | 리스크 요인으로 payload에 명시 |

#### 6.8.3 프롬프트 프로필 전략

기존 `prompt_profile` 구조를 재사용하되 질문 생성용 프로필과 구분하기 위해 선별 전용 profile_key를 사용합니다.

```text
SCREENING_DEFAULT
SCREENING_HR
SCREENING_SALES
SCREENING_AI_DEV_DATA
SCREENING_MARKETING
SCREENING_STRATEGY
```

예시 system prompt:

```text
당신은 채용 서류검토 담당관입니다.

지원자의 기본정보, 지원 직무, 제출 문서의 추출 내용을 검토하여
해당 직무의 면접 대상자로 추천할지 판단하세요.

판단 기준:
- 지원 직무와 경험/역량의 관련성
- 문서에서 확인 가능한 근거
- 경력/프로젝트/성과의 구체성
- 면접에서 검증해야 할 리스크
- 문서 누락 또는 추출 실패로 인한 판단 제한

주의:
- 문서에 없는 사실을 추정하지 마세요.
- 추천 사유는 반드시 문서 근거 기반으로 작성하세요.
- 자동 합격/불합격이 아니라 HR 검토를 돕는 추천 결과를 반환하세요.
```

RAG 기반 채용 공고/직무 지식 주입은 후속 고도화 항목으로 둡니다. 2차 MVP에서는 프롬프트 프로필에 직무별 인재상과 검토 기준을 명시하고, `temperature=0`으로 고정하여 결과 일관성을 우선합니다.

#### 6.8.4 screening_graph 구성

질문 생성 그래프와 목적이 다르므로 `backend/ai/interview_graph`를 직접 확장하기보다 별도 그래프로 분리합니다.

```text
backend/ai/screening_graph/
  state.py
  schemas.py
  prompts.py
  nodes.py
  runner.py
```

MVP 노드는 다음과 같이 구성합니다.

| 노드 | 역할 |
|---|---|
| build_state | 후보자 기본정보, 문서, 프롬프트 프로필 입력 정리 |
| document_compactor | 문서 타입별 핵심 텍스트 압축, 누락/추출 실패 표시 |
| screening_evaluator | LLM으로 직무 적합도, 추천 여부, 근거 산출 |
| screening_reviewer | 문서 근거 부족, 환각 위험, 판단 제한 사항 검증 |
| final_formatter | 점수, 추천 상태, 사유, 리스크, 면접 검증 포인트를 최종 JSON으로 정리 |

다중 지원자 선별은 한 번의 LLM 호출에 모든 지원자를 넣지 않고, 배치 실행 단위와 후보자별 그래프 실행 단위를 분리합니다.

```text
screening_run 생성
→ candidate_id별 payload 조립
→ candidate별 screening_graph 실행
→ candidate_screening_result 저장
→ screening_run summary 집계
```

이 방식은 토큰 초과, 일부 후보 실패, 재실행, 결과 검토를 다루기 쉽습니다.

#### 6.8.5 출력 스키마

```json
{
  "candidate_id": 88,
  "recommendation": "RECOMMEND",
  "score": 82,
  "confidence": 0.78,
  "summary": "영업 직무와 관련된 고객 대응 및 성과 경험이 확인됩니다.",
  "fit_reasons": [
    "지원 직무와 유관한 영업 경험 보유",
    "정량 성과가 일부 문서에서 확인됨"
  ],
  "risk_factors": [
    "최근 경력 공백 여부 추가 확인 필요"
  ],
  "missing_evidence": [
    "포트폴리오 문서 없음"
  ],
  "interview_focus": [
    "실제 영업 성과 산정 방식",
    "고객 갈등 대응 경험"
  ],
  "suggested_next_action": "INTERVIEW"
}
```

#### 6.8.6 데이터 모델 초안

```text
candidate_screening_run
- id
- status
- target_job
- prompt_profile_id
- requested_by
- candidate_count
- recommend_count
- hold_count
- reject_count
- request_payload
- summary_payload
- error_message
- created_at
- completed_at
```

```text
candidate_screening_result
- id
- run_id
- candidate_id
- score
- recommendation
- confidence
- suggested_next_action
- summary
- fit_reasons
- risk_factors
- missing_evidence
- interview_focus
- payload_snapshot
- raw_output
- decision_status
- decided_by
- decided_at
- created_at
```

`recommendation` 값:

```text
RECOMMEND
HOLD
REJECT
```

`decision_status` 값:

```text
PENDING
CONFIRMED
HELD
EXCLUDED
```

#### 6.8.7 API 설계

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/v1/candidates/screening-runs` | 면접자 선별 실행 시작 |
| GET | `/api/v1/candidates/screening-runs/{run_id}` | 선별 실행 상태 및 요약 조회 |
| GET | `/api/v1/candidates/screening-runs/{run_id}/results` | 후보자별 선별 결과 조회 |
| PATCH | `/api/v1/candidates/screening-results/{result_id}/decision` | 단일 후보 확정/보류/제외 |
| POST | `/api/v1/candidates/screening-runs/{run_id}/confirm-interviews` | 추천 후보 일괄 면접 확정 |
| POST | `/api/v1/candidates/screening-runs/{run_id}/create-sessions` | 확정 후보 면접 세션 생성 |

#### 6.8.8 MVP 구현 범위

| 기능 | MVP 포함 |
|---|---|
| 지원자 관리 화면 내 면접자 선별 버튼 | Y |
| 선택 지원자 또는 현재 필터 기반 선별 실행 | Y |
| 지원자 기본정보 + 문서 추출 정보 payload 조립 | Y |
| 선별 전용 프롬프트 프로필 선택 | Y |
| screening_graph 후보자별 실행 | Y |
| 후보자별 점수, 추천 사유, 리스크 저장 | Y |
| HR 수동 확정/보류/제외 | Y |
| 확정자 분석 세션 생성 연결 | Y |
| RAG 기반 채용 공고 지식 주입 | N |
| 후보자 간 직접 비교 평가 | N |
| Celery/Redis 기반 선별 작업 큐 | N |

## Priority 5. 운영 가시성 개선

### 7.1 문제 정의

대량 작업이 많아질수록 HR 담당자와 관리자는 현재 어떤 작업이 진행 중인지 알아야 합니다.

### 7.2 목표

job 상태와 실패 원인을 한 화면에서 확인할 수 있도록 합니다.

### 7.3 화면 구성

```text
[작업 현황]

필터
- 작업 유형
- 상태
- 요청자
- 생성일

테이블
- job id
- 작업 유형
- 대상
- 상태
- 진행률
- 실패 사유
- 요청자
- 시작 시간
- 종료 시간
- 액션
```

액션:

- 재시도
- 취소
- 상세 보기
- 실패 로그 보기

### 7.4 성공 기준

- AI 작업 상태를 job 단위로 볼 수 있다.
- 실패 작업을 재시도할 수 있다.
- 오래 걸리는 작업을 식별할 수 있다.

## 8. 2차 MVP 개발 순서

권장 순서는 다음과 같습니다.

```text
1. 지원자 일괄 등록 preview API
2. 지원자 일괄 등록 import API
3. 일괄 등록 프론트 화면
4. 면접자 선별 버튼 및 실행 모달
5. 지원자/문서 기반 screening payload 조립
6. screening_graph 및 선별 결과 저장
7. 선별 결과 확정/보류/제외 화면
8. 확정자 기반 분석 세션 생성 연결
9. ai_job 테이블 및 job 상태 관리 도입
10. 질문 생성 중복 실행 방지
11. 문서 분석 job 연동
12. 질문 생성 job 연동
13. 작업 현황 화면
14. Celery/Redis worker 전환
```

이 순서를 권장하는 이유는, 면접자 선별 기능이 질문 생성 전에 지원자 풀을 줄여 LLM 사용량과 불필요한 세션 생성을 줄일 수 있기 때문입니다. 다만 MVP 단계에서는 선별 실행을 단순 BackgroundTasks 또는 동기 실행에 가깝게 시작하고, 이후 `ai_job` 기반 작업 상태 관리와 Celery/Redis worker 전환으로 안정성을 높입니다.

## 9. MVP에서 제외할 항목

2차 MVP에서 제외하고 후속 고도화로 넘기는 항목:

- 완전 자동 최종 합격/불합격 결정
- 면접 일정 캘린더 연동
- 이메일/SMS 발송 자동화
- 외부 ATS 연동
- 고급 통계 리포트
- 프롬프트 자동 튜닝
- 후보자 간 LLM 기반 직접 비교 평가
- 조직별 권한/승인 워크플로우

## 10. 최종 범위 요약

2차 MVP의 핵심 범위는 다음 네 가지입니다.

```text
1. 지원자 일괄 등록
2. 질문 생성 전 면접자 선별
3. AI 작업 큐 고도화
4. 문서 분석/질문 생성 일괄 처리
```

우선순위는 `일괄 등록 → 면접자 선별 → 분석 세션 생성/질문 생성 → 작업 큐 고도화` 순서가 MVP 가치 검증에 적합합니다. 운영 안정화 단계에서는 `ai_job → 작업 현황 → Celery/Redis worker` 순서로 고도화합니다.

## 11. 기대 효과

- HR 담당자의 반복 입력 작업 감소
- 대량 지원자 처리 시간 단축
- AI 작업 실패/중복 실행 감소
- 면접 대상자 선별 기준 정량화
- 시스템 운영 상태 가시성 향상
- 향후 ATS/캘린더/알림 연동을 위한 기반 확보
