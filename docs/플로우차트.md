# HR Copilot BS 시스템 시퀀스 다이어그램


## 1. 개요
본 시퀀스 다이어그램은 **HR Copilot BS**의 기능 요구사항 정의서(FR) 및 API 명세서를 바탕으로 관리자 승인, 지원자 관리, 문서 처리, 그리고 LLM 분석으로 이어지는 전체 시스템 흐름을 정의합니다.

## 2. 시스템 시퀀스 다이어그램 (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Manager as 관리자(Manager)
    actor User as 서비스 사용자(HR 담당자)

    participant Auth as JWT Auth
    participant API as FastAPI Router
    participant Account as 계정 관리 (FR-01, FR-02)
    participant Candidate as 지원자 관리 (FR-03)
    participant Document as 문서 관리 (FR-04)
    participant Prompt as 프롬프트 관리 (FR-05)
    participant Workflow as 분석 실행 (workflow_run)
    participant LLM as OpenAI (GPT-4)
    participant Question as 면접 질문 관리 (FR-06)
    participant Log as LLM 로그 관리 (FR-07)
    participant DB as PostgreSQL
    participant Storage as Object Storage (파일)

    %% 관리자 인증
    Manager->>API: 관리자 로그인 요청 (login_id, password)
    API->>Auth: 인증 요청
    Auth-->>API: JWT 토큰 발급
    API-->>Manager: 로그인 성공 및 토큰 반환
    API->>DB: last_login_at 업데이트

    %% 사용자 계정 요청 및 승인
    User->>API: 사용자 계정 생성 요청
    API->>Account: 요청 정보 저장
    Account->>DB: user(request_status=REQUESTED) 저장
    Manager->>API: 사용자 승인/반려
    API->>Account: 상태 변경 처리
    Account->>DB: request_status 및 status 업데이트

    %% 지원자 등록
    User->>API: 지원자 등록
    API->>Candidate: 지원자 정보 처리
    Candidate->>DB: candidate 저장

    %% 문서 업로드 및 텍스트 추출
    User->>API: 이력서/포트폴리오 업로드
    API->>Document: 문서 메타데이터 저장
    Document->>Storage: 파일 저장
    Document->>DB: document(extract_status=PENDING) 저장
    Document->>Document: 텍스트 추출 수행 (FR-04-06)
    Document->>DB: extracted_text 및 extract_status 업데이트

    %% 대표 문서 연결
    User->>API: 대표 문서 연결
    API->>Candidate: resume_doc_id / portfolio_doc_id 설정
    Candidate->>DB: candidate 업데이트

    %% 분석 전략 선택
    User->>API: 프롬프트 프로파일 선택
    API->>Prompt: prompt_profile 조회
    Prompt->>DB: 프롬프트 정보 반환

    %% 분석 실행 (Workflow)
    User->>API: 분석 실행 요청
    API->>Workflow: workflow_run 생성
    Workflow->>DB: workflow_run 저장

    %% LLM 호출
    Workflow->>LLM: 지원자 및 문서 기반 분석 요청
    LLM-->>Workflow: 분석 결과(JSON)

    %% 면접 질문 저장
    Workflow->>Question: 면접 질문 생성 결과 전달
    Question->>DB: interview_question_item 저장

    %% LLM 로그 기록
    Workflow->>Log: 호출 결과 및 비용 전달 (FR-07)
    Log->>DB: llm_call_log 저장

    %% 결과 반환
    API-->>User: 생성된 면접 질문 반환
```

## 3. 실무 설계 핵심 (Review)

- **데이터 무결성:** 모든 주요 변경 사항은 PostgreSQL DB에 즉시 반영되며, 파일 본체는 Object Storage에 저장하여 효율성을 높였습니다.
- **상태 기반 워크플로우:** `request_status`, `extract_status` 등 단계별 상태값을 통해 비동기 작업(텍스트 추출 등)의 진행 상황을 명확히 추적합니다.
- **Audit 관리:** 모든 DB 저장 시 `FR-08`에 정의된 공통 Audit 컬럼(`created_at`, `created_by` 등)이 자동으로 적용됩니다.

## 4. 트러블슈팅 포인트
- **텍스트 추출 지연:** `extract_status`가 `PENDING`에서 멈출 경우, 문서 처리 모듈의 로그를 확인하여 OCR 엔진의 정상 작동 여부를 점검해야 합니다.
- **로그 유실 방지:** `llm_call_log`는 LLM 응답 직후 저장되어야 하며, 비용 계산(`cost_amount`) 로직이 요구사항(FR-07-05)대로 수행되는지 모니터링이 필요합니다.