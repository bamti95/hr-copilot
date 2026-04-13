# 🔁 HR Copilot BS — 시스템 시퀀스 다이어그램

> **목적:** 관리자 인증부터 문서 분석 및 면접 질문 확정까지의 시스템 간 상호작용을 시간 순서대로 표현

---

## 1. 📊 시퀀스 다이어그램 (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 관리자
    participant CMS as Admin CMS (Frontend)
    participant API as Backend API (FastAPI)
    participant DB as PostgreSQL
    participant Storage as Object Storage
    participant OCR as OCR/Parser
    participant EMB as Embedding Service
    participant LLM as LLM API (OpenAI)

    %% =========================
    %% 1. 인증 및 권한 검증
    %% =========================
    Admin->>CMS: 로그인 요청 (ID/PW)
    CMS->>API: 인증 요청
    API->>DB: 관리자 계정 조회
    DB-->>API: 계정 정보 반환
    API-->>CMS: JWT 토큰 발급
    CMS-->>Admin: 로그인 성공

    %% =========================
    %% 2. 문서 업로드
    %% =========================
    Admin->>CMS: 문서 업로드 (JD/Resume/Portfolio)
    CMS->>API: 파일 업로드 요청
    API->>Storage: 파일 저장
    Storage-->>API: 파일 경로 반환
    API->>DB: document 메타데이터 저장 (extract_status='PENDING')
    API-->>CMS: 업로드 완료 응답

    %% =========================
    %% 3. 비동기 전처리 (OCR → Chunking → Embedding)
    %% =========================
    Note over API: Background Task 시작
    API->>OCR: 텍스트 추출 요청
    OCR-->>API: extracted_text 반환
    API->>DB: extracted_text 업데이트 (status='READY')

    API->>DB: document_chunk 저장 (청킹)
    API->>EMB: 임베딩 생성 요청
    EMB-->>API: 벡터 반환
    API->>DB: chunk_embedding 저장

    %% =========================
    %% 4. 분석 실행 요청
    %% =========================
    Admin->>CMS: 분석 실행 요청
    CMS->>API: workflow_run 생성 요청
    API->>DB: prompt_profile 조회
    API->>DB: prompt_template 조회 및 조립
    API->>DB: workflow_run 저장 (run_status='RUNNING')

    %% =========================
    %% 5. LLM 호출 및 로그 저장
    %% =========================
    API->>LLM: 분석 요청 (assembled_prompt + RAG context)
    LLM-->>API: 분석 결과(JSON)

    API->>DB: llm_call_log 저장 (토큰 사용량, 비용, latency)
    
    %% =========================
    %% 6. 결과 파싱 및 저장 (트랜잭션)
    %% =========================
    Note over API,DB: DB Transaction 시작
    API->>DB: interview_question_set 저장
    API->>DB: interview_question_item 저장
    API->>DB: question_chunk_mapping 저장
    API->>DB: workflow_run 상태 업데이트 (SUCCESS)
    Note over API,DB: Transaction Commit

    %% =========================
    %% 7. 결과 조회 및 사용자 확정
    %% =========================
    CMS->>API: 분석 결과 조회 요청
    API->>DB: 질문 세트 및 항목 조회
    DB-->>API: 결과 반환
    API-->>CMS: 결과 전달
    CMS-->>Admin: 질문 세트 표시

    Admin->>CMS: 질문 수정 및 확정
    CMS->>API: 최종 질문 세트 저장 요청
    API->>DB: 질문 세트 업데이트 (확정 상태)
    API-->>CMS: 저장 완료 응답

    %% =========================
    %% 8. 다운로드
    %% =========================
    Admin->>CMS: 질문지 다운로드 요청
    CMS->>API: 파일 생성 요청
    API-->>CMS: PDF/문서 파일 반환
    CMS-->>Admin: 다운로드 제공
```

---

## 2. 📌 다이어그램 참여자(Participants) 설명

| 참여자 | 설명 |
|--------|------|
| **관리자 (Admin)** | 시스템을 사용하는 HR 담당자 |
| **Admin CMS** | 관리자용 프론트엔드 인터페이스 |
| **Backend API** | FastAPI 기반 비즈니스 로직 처리 |
| **PostgreSQL** | 서비스 데이터 저장소 |
| **Object Storage** | 업로드된 문서 파일 저장 |
| **OCR/Parser** | 문서에서 텍스트를 추출하는 서비스 |
| **Embedding Service** | 텍스트를 벡터로 변환 |
| **LLM API** | 면접 질문 생성을 위한 AI 모델 |

---

## 3. 📌 주요 특징

### ✅ 3.1 End-to-End 프로세스 반영
- 인증 → 문서 업로드 → 전처리 → LLM 분석 → 결과 저장 → 사용자 확정까지 전체 흐름을 포함합니다.

### ✅ 3.2 비동기 처리 표현
- `Note over API: Background Task 시작`을 통해 OCR 및 임베딩이 비동기적으로 수행됨을 명확히 표현했습니다.

### ✅ 3.3 데이터 무결성 보장
- 결과 저장 시 `Transaction Commit`을 명시하여 데이터 정합성을 확보했습니다.

### ✅ 3.4 운영 관점의 로그 관리
- `llm_call_log`에 토큰 사용량, 비용, 지연 시간 등을 기록하여 FR-07 요구사항을 충족합니다.

### ✅ 3.5 사용자 개입 단계
- AI가 생성한 질문을 관리자가 **검토·수정·확정**하는 단계가 포함되어 실무 활용성을 높였습니다.

---

## 4. 📌 확장 가능성

향후 다음과 같은 요소를 추가하여 확장할 수 있습니다.

| 확장 항목 | 설명 |
|-----------|------|
| Message Queue | 대규모 트래픽 대응을 위한 비동기 처리 고도화 |
| Multi-Tenant | 기업별 데이터 분리 |
| Analytics Dashboard | 채용 데이터 분석 및 시각화 |
| Candidate Feedback | 면접 평가 및 피드백 저장 |

---

## ✅ 한줄 정의
> **"HR Copilot BS의 시퀀스 다이어그램은 관리자 인증부터 AI 기반 면접 질문 생성 및 확정까지의 시스템 간 상호작용을 시간 흐름에 따라 표현한 것이다."**
