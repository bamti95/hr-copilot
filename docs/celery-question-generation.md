# 질문 생성 Celery 작업 큐 실행 가이드

1. Redis 준비: Memurai 사용

Windows 로컬에서는 Memurai Community를 사용

1-1. 다운로드
https://www.memurai.com/get-memurai
Memurai Community Edition 선택

실행 확인:

netstat -ano | findstr :6379

정상 예시:

TCP    127.0.0.1:6379    0.0.0.0:0    LISTENING


## 구조

면접 질문 생성은 FastAPI `BackgroundTasks`가 아니라 Celery task로 실행한다.

```text
FastAPI API
  -> InterviewSession 생성 / 상태 QUEUED
  -> Celery task enqueue
  -> Redis broker
  -> Celery worker
  -> QuestionGenerationService.generate_and_store_for_session()
  -> LangGraph 실행
  -> 질문 저장 + 상태 COMPLETED / PARTIAL_COMPLETED / FAILED
```

## 환경변수

`backend/.env`에 필요하면 아래 값을 추가한다. 값이 없으면 기본값을 사용한다.

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_DEFAULT_QUEUE=question-generation
CELERY_WORKER_CONCURRENCY=5
```

## 실행

Celery Worker 실행 (중요)

Windows에서는 반드시 solo pool 사용

```bash
uv run celery -A core.celery_app.celery_app worker ^
  --pool=solo ^
  --loglevel=info ^
  --queues=question-generation
```

정상 로그 예:

[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] ready.

이미 실행 중인 Redis가 있다면 `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`를 해당 주소로 맞춘다.

FastAPI:

```bash
cd backend
uv run uvicorn main:app --reload
```

Celery worker:

```bash
cd backend
uv run celery -A core.celery_app.celery_app worker --loglevel=info --queues=question-generation --concurrency=5
```

Windows 개발 환경에서 prefork 문제가 있으면 `solo` pool로 실행한다.

```powershell
cd backend
uv run celery -A core.celery_app.celery_app worker --pool=solo --loglevel=info --queues=question-generation
```

로컬 Redis 컨테이너를 중지/삭제할 때:

```bash
docker stop hr-copilot-redis
docker rm hr-copilot-redis
```

## 동시성 정책

`--concurrency=5`는 동시에 최대 5개의 세션 질문 생성 task를 처리한다는 뜻이다. 단, LangGraph 내부에서 `predictor`, `driller`, `reviewer`가 병렬 실행되므로 실제 OpenAI 동시 호출 수는 worker concurrency보다 클 수 있다.

예시:

```text
worker concurrency 5
그래프 내부 병렬 LLM 노드 3개
순간 OpenAI 호출 가능 수 = 최대 약 15개
```

OpenAI rate limit이나 DB 커넥션 풀이 작으면 worker concurrency를 2 또는 3으로 낮춰 운영한다. 여러 worker를 띄우면 전체 동시성은 worker별 concurrency의 합이다.

```text
worker 2대 * concurrency 5 = 최대 10개 session task 동시 처리
```

## 상태 전이

```text
QUEUED -> PROCESSING -> COMPLETED
QUEUED -> PROCESSING -> PARTIAL_COMPLETED
QUEUED -> PROCESSING -> FAILED
```

Celery task는 retry/backoff를 사용한다. 재시도 중에는 세션 상태를 바로 `FAILED`로 확정하지 않고, 최대 재시도 이후 `FAILED`로 업데이트한다.

## 중복 요청 정책

동일 세션의 상태가 `QUEUED` 또는 `PROCESSING`이면 재생성 task enqueue를 막고 `409 Conflict`를 반환한다. `COMPLETED`, `PARTIAL_COMPLETED`, `FAILED` 상태에서는 수동 재생성을 허용한다.
