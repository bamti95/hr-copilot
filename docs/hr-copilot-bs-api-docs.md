# 📘 HR Copilot BS — API 문서

> **Version**: 1.0  
> **Base URL**: `https://api.hr-copilot.example.com/v1`  
> **인증 방식**: Bearer Token (JWT)

---

## 📑 목차

1. [인증](#1-인증)
2. [FR-01: 관리자 계정/권한 관리](#fr-01-관리자-계정권한-관리)
3. [FR-02: 메뉴 및 권한 매핑](#fr-02-메뉴-및-권한-매핑)
4. [FR-03: 문서 관리](#fr-03-문서-관리)
5. [FR-04: 프롬프트 관리](#fr-04-프롬프트-관리)
6. [FR-05: LLM 실행](#fr-05-llm-실행)
7. [FR-06: 면접 결과 관리](#fr-06-면접-결과-관리)
8. [FR-07: 로그 및 통계](#fr-07-로그-및-통계)
9. [FR-08: RAG 처리](#fr-08-rag-처리)
10. [공통 응답 코드](#공통-응답-코드)
11. [에러 처리](#에러-처리)

---

## 1. 인증

### 로그인

**FR-01-02: 관리자 로그인**

```http
POST /auth/login
```

**Request Body**
```json
{
  "login_id": "admin@example.com",
  "password": "yourPassword123!"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "admin": {
      "admin_id": 1,
      "login_id": "admin@example.com",
      "username": "관리자",
      "status": "ACTIVE",
      "group_id": 1,
      "group_name": "슈퍼관리자"
    }
  }
}
```

**Error Responses**
- `401 Unauthorized`: 잘못된 인증 정보
- `403 Forbidden`: 계정 상태가 INACTIVE 또는 LOCK

---

## FR-01: 관리자 계정/권한 관리

### FR-01-01: 관리자 계정 등록

```http
POST /admins
```

**Request Body**
```json
{
  "login_id": "newadmin@example.com",
  "password": "SecurePass123!",
  "username": "홍길동",
  "email": "newadmin@example.com",
  "group_id": 2,
  "status": "ACTIVE"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "admin_id": 10,
    "login_id": "newadmin@example.com",
    "username": "홍길동",
    "email": "newadmin@example.com",
    "status": "ACTIVE",
    "group_id": 2,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-01-03: 관리자 상태 관리

```http
PATCH /admins/{admin_id}/status
```

**Request Body**
```json
{
  "status": "INACTIVE"
}
```

**가능한 상태값**
- `ACTIVE`: 활성
- `INACTIVE`: 비활성
- `LOCK`: 잠금

**Response**
```json
{
  "success": true,
  "data": {
    "admin_id": 10,
    "status": "INACTIVE",
    "updated_at": "2024-04-13T11:00:00Z"
  }
}
```

---

### FR-01-04: 권한 그룹 생성

```http
POST /permission-groups
```

**Request Body**
```json
{
  "group_key": "HR_MANAGER",
  "group_name": "인사 담당자",
  "description": "인사 관련 문서 및 분석 권한"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "group_id": 5,
    "group_key": "HR_MANAGER",
    "group_name": "인사 담당자",
    "description": "인사 관련 문서 및 분석 권한",
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-01-05: 권한 그룹 수정

```http
PUT /permission-groups/{group_id}
```

**Request Body**
```json
{
  "group_name": "인사 관리자",
  "description": "수정된 설명"
}
```

---

### 권한 그룹 삭제 (Soft Delete)

```http
DELETE /permission-groups/{group_id}
```

**Response**
```json
{
  "success": true,
  "message": "권한 그룹이 삭제되었습니다.",
  "data": {
    "group_id": 5,
    "deleted_at": "2024-04-13T12:00:00Z"
  }
}
```

---

## FR-02: 메뉴 및 권한 매핑

### FR-02-01: 관리자 메뉴 등록

```http
POST /menus
```

**Request Body**
```json
{
  "menu_key": "DOCUMENT_MGMT",
  "menu_name": "문서 관리",
  "parent_id": null,
  "menu_path": "/documents",
  "sort_no": 10,
  "is_visible": true
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "menu_id": 15,
    "menu_key": "DOCUMENT_MGMT",
    "menu_name": "문서 관리",
    "parent_id": null,
    "menu_path": "/documents",
    "sort_no": 10,
    "is_visible": true,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-02-03: 메뉴 트리 조회

```http
GET /menus/tree
```

**Response**
```json
{
  "success": true,
  "data": [
    {
      "menu_id": 1,
      "menu_key": "DASHBOARD",
      "menu_name": "대시보드",
      "menu_path": "/dashboard",
      "sort_no": 1,
      "children": []
    },
    {
      "menu_id": 2,
      "menu_key": "DOCUMENT",
      "menu_name": "문서 관리",
      "menu_path": "/documents",
      "sort_no": 2,
      "children": [
        {
          "menu_id": 3,
          "menu_key": "DOCUMENT_UPLOAD",
          "menu_name": "문서 업로드",
          "menu_path": "/documents/upload",
          "sort_no": 1,
          "children": []
        },
        {
          "menu_id": 4,
          "menu_key": "DOCUMENT_LIST",
          "menu_name": "문서 목록",
          "menu_path": "/documents/list",
          "sort_no": 2,
          "children": []
        }
      ]
    }
  ]
}
```

---

### FR-02-04: 그룹별 메뉴 권한 설정

```http
POST /menu-permissions
```

**Request Body**
```json
{
  "group_id": 2,
  "menu_id": 15,
  "can_read": true,
  "can_write": true,
  "can_delete": false
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "permission_id": 100,
    "group_id": 2,
    "menu_id": 15,
    "can_read": true,
    "can_write": true,
    "can_delete": false,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-02-05: 접근 가능 메뉴 조회

```http
GET /menus/accessible
```

**Headers**
```
Authorization: Bearer {access_token}
```

**Response**
```json
{
  "success": true,
  "data": [
    {
      "menu_id": 1,
      "menu_key": "DASHBOARD",
      "menu_name": "대시보드",
      "menu_path": "/dashboard",
      "permissions": {
        "can_read": true,
        "can_write": false,
        "can_delete": false
      }
    },
    {
      "menu_id": 2,
      "menu_key": "DOCUMENT_MGMT",
      "menu_name": "문서 관리",
      "menu_path": "/documents",
      "permissions": {
        "can_read": true,
        "can_write": true,
        "can_delete": false
      }
    }
  ]
}
```

---

## FR-03: 문서 관리

### FR-03-01: 문서 업로드

```http
POST /documents
```

**Request (multipart/form-data)**
```
file: [binary file]
document_type: RESUME
title: 홍길동_이력서
```

**문서 타입**
- `ROLE_PROFILE`: 직무 프로필
- `RESUME`: 이력서
- `PORTFOLIO`: 포트폴리오

**Response**
```json
{
  "success": true,
  "data": {
    "document_id": 1001,
    "document_type": "RESUME",
    "title": "홍길동_이력서",
    "file_name": "resume_20240413.pdf",
    "file_path": "/uploads/2024/04/13/abc123.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "extraction_status": "PENDING",
    "uploaded_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-03-02: 문서 목록 조회

```http
GET /documents?document_type=RESUME&page=1&limit=20
```

**Query Parameters**
- `document_type` (optional): ROLE_PROFILE | RESUME | PORTFOLIO
- `extraction_status` (optional): PENDING | READY | FAILED
- `page` (optional, default: 1)
- `limit` (optional, default: 20)

**Response**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "document_id": 1001,
        "document_type": "RESUME",
        "title": "홍길동_이력서",
        "file_name": "resume_20240413.pdf",
        "file_size": 2048576,
        "extraction_status": "READY",
        "uploaded_at": "2024-04-13T10:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 100,
      "items_per_page": 20
    }
  }
}
```

---

### FR-03-03: 문서 상세 조회

```http
GET /documents/{document_id}
```

**Response**
```json
{
  "success": true,
  "data": {
    "document_id": 1001,
    "document_type": "RESUME",
    "title": "홍길동_이력서",
    "file_name": "resume_20240413.pdf",
    "file_path": "/uploads/2024/04/13/abc123.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "extraction_status": "READY",
    "extracted_text": "이력서 내용 전체 텍스트...",
    "uploaded_at": "2024-04-13T10:30:00Z",
    "extracted_at": "2024-04-13T10:35:00Z"
  }
}
```

---

### FR-03-04: 문서 삭제 (Soft Delete)

```http
DELETE /documents/{document_id}
```

**Response**
```json
{
  "success": true,
  "message": "문서가 삭제되었습니다.",
  "data": {
    "document_id": 1001,
    "deleted_at": "2024-04-13T12:00:00Z"
  }
}
```

---

### FR-03-05: 텍스트 추출 상태 조회

```http
GET /documents/{document_id}/extraction-status
```

**Response**
```json
{
  "success": true,
  "data": {
    "document_id": 1001,
    "extraction_status": "READY",
    "extracted_at": "2024-04-13T10:35:00Z",
    "error_message": null
  }
}
```

**상태값**
- `PENDING`: 추출 대기
- `READY`: 추출 완료
- `FAILED`: 추출 실패

---

## FR-04: 프롬프트 관리

### FR-04-01: 프롬프트 템플릿 등록

```http
POST /prompt-templates
```

**Request Body**
```json
{
  "template_key": "RESUME_ANALYSIS_V1",
  "template_name": "이력서 분석 템플릿",
  "content": "다음 이력서를 분석하여 주요 경력과 역량을 추출하세요:\n\n{resume_text}",
  "version": "1.0",
  "is_active": true
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "template_id": 50,
    "template_key": "RESUME_ANALYSIS_V1",
    "template_name": "이력서 분석 템플릿",
    "content": "다음 이력서를 분석하여 주요 경력과 역량을 추출하세요:\n\n{resume_text}",
    "version": "1.0",
    "is_active": true,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-04-02: 템플릿 버전 관리

```http
GET /prompt-templates/{template_key}/versions
```

**Response**
```json
{
  "success": true,
  "data": [
    {
      "template_id": 50,
      "version": "1.0",
      "is_active": true,
      "created_at": "2024-04-13T10:30:00Z"
    },
    {
      "template_id": 51,
      "version": "1.1",
      "is_active": false,
      "created_at": "2024-04-10T09:00:00Z"
    }
  ]
}
```

---

### FR-04-03: 템플릿 활성/비활성

```http
PATCH /prompt-templates/{template_id}/activate
```

**Request Body**
```json
{
  "is_active": true
}
```

---

### FR-04-04: 프롬프트 프로파일 생성

```http
POST /prompt-profiles
```

**Request Body**
```json
{
  "profile_key": "GENERAL_INTERVIEW",
  "profile_name": "일반 면접 분석",
  "strategy_type": "GENERAL",
  "description": "일반적인 면접 질문 생성 프로파일"
}
```

**전략 유형**
- `GENERAL`: 일반 분석
- `DEEP_DIVE`: 심층 분석
- `RISK_FOCUS`: 리스크 중심 분석

**Response**
```json
{
  "success": true,
  "data": {
    "profile_id": 10,
    "profile_key": "GENERAL_INTERVIEW",
    "profile_name": "일반 면접 분석",
    "strategy_type": "GENERAL",
    "description": "일반적인 면접 질문 생성 프로파일",
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-04-05: 프로파일-템플릿 매핑

```http
POST /prompt-profiles/{profile_id}/templates
```

**Request Body**
```json
{
  "template_id": 50,
  "sort_no": 1
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "mapping_id": 100,
    "profile_id": 10,
    "template_id": 50,
    "sort_no": 1,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

## FR-05: LLM 실행

### FR-05-01: 분석 실행 생성

```http
POST /llm-executions
```

**Request Body**
```json
{
  "document_id": 1001,
  "profile_id": 10,
  "execution_type": "INTERVIEW_GENERATION"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "execution_id": 5001,
    "document_id": 1001,
    "profile_id": 10,
    "execution_type": "INTERVIEW_GENERATION",
    "status": "READY",
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-05-02: 프롬프트 조립 결과 조회

```http
GET /llm-executions/{execution_id}/assembled-prompt
```

**Response**
```json
{
  "success": true,
  "data": {
    "execution_id": 5001,
    "assembled_prompt": "다음 이력서를 분석하여...\n\n[이력서 내용]\n\n위 내용을 바탕으로...",
    "template_count": 3,
    "total_tokens": 1500
  }
}
```

---

### FR-05-03: LLM 실행

```http
POST /llm-executions/{execution_id}/run
```

**Request Body**
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "execution_id": 5001,
    "status": "RUNNING",
    "started_at": "2024-04-13T10:31:00Z"
  }
}
```

---

### FR-05-04: 실행 상태 조회

```http
GET /llm-executions/{execution_id}/status
```

**Response**
```json
{
  "success": true,
  "data": {
    "execution_id": 5001,
    "status": "SUCCESS",
    "started_at": "2024-04-13T10:31:00Z",
    "completed_at": "2024-04-13T10:31:45Z",
    "duration_ms": 45000
  }
}
```

**상태값**
- `READY`: 실행 대기
- `RUNNING`: 실행 중
- `SUCCESS`: 성공
- `FAIL`: 실패

---

### FR-05-05: 실행 결과 조회

```http
GET /llm-executions/{execution_id}/result
```

**Response**
```json
{
  "success": true,
  "data": {
    "execution_id": 5001,
    "status": "SUCCESS",
    "result_text": "LLM이 생성한 면접 질문 및 분석 결과...",
    "input_tokens": 1500,
    "output_tokens": 800,
    "total_tokens": 2300,
    "model_used": "gpt-4",
    "completed_at": "2024-04-13T10:31:45Z"
  }
}
```

---

## FR-06: 면접 결과 관리

### FR-06-01: 질문 세트 생성

```http
POST /interview-question-sets
```

**Request Body**
```json
{
  "execution_id": 5001,
  "title": "홍길동 면접 질문",
  "total_questions": 10
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "set_id": 2001,
    "execution_id": 5001,
    "title": "홍길동 면접 질문",
    "total_questions": 10,
    "created_at": "2024-04-13T10:32:00Z"
  }
}
```

---

### FR-06-02: 질문 항목 생성

```http
POST /interview-questions
```

**Request Body**
```json
{
  "set_id": 2001,
  "question_text": "프로젝트에서 가장 어려웠던 기술적 도전은 무엇이었나요?",
  "category": "COMPETENCY",
  "difficulty": "MEDIUM",
  "sort_no": 1
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "question_id": 10001,
    "set_id": 2001,
    "question_text": "프로젝트에서 가장 어려웠던 기술적 도전은 무엇이었나요?",
    "category": "COMPETENCY",
    "difficulty": "MEDIUM",
    "sort_no": 1,
    "created_at": "2024-04-13T10:32:00Z"
  }
}
```

---

### FR-06-03: 질문 카테고리별 조회

```http
GET /interview-questions?set_id=2001&category=COMPETENCY
```

**카테고리**
- `COMPETENCY`: 역량
- `RISK`: 리스크
- `EXPERIENCE`: 경험

**Response**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "question_id": 10001,
        "question_text": "프로젝트에서 가장 어려웠던 기술적 도전은 무엇이었나요?",
        "category": "COMPETENCY",
        "difficulty": "MEDIUM",
        "sort_no": 1
      }
    ],
    "total": 5
  }
}
```

---

### FR-06-04: 질문 난이도별 조회

```http
GET /interview-questions?set_id=2001&difficulty=HARD
```

**난이도**
- `EASY`: 쉬움
- `MEDIUM`: 보통
- `HARD`: 어려움

---

### FR-06-05: 질문 세트 조회

```http
GET /interview-question-sets/{set_id}
```

**Response**
```json
{
  "success": true,
  "data": {
    "set_id": 2001,
    "execution_id": 5001,
    "title": "홍길동 면접 질문",
    "total_questions": 10,
    "questions": [
      {
        "question_id": 10001,
        "question_text": "프로젝트에서 가장 어려웠던 기술적 도전은 무엇이었나요?",
        "category": "COMPETENCY",
        "difficulty": "MEDIUM",
        "sort_no": 1
      }
    ],
    "created_at": "2024-04-13T10:32:00Z"
  }
}
```

---

## FR-07: 로그 및 통계

### FR-07-01: LLM 호출 로그 저장

```http
POST /llm-call-logs
```

**Request Body**
```json
{
  "execution_id": 5001,
  "model": "gpt-4",
  "input_tokens": 1500,
  "output_tokens": 800,
  "total_tokens": 2300,
  "latency_ms": 45000,
  "status": "SUCCESS"
}
```

---

### FR-07-02: 토큰 사용량 조회

```http
GET /llm-call-logs/token-usage?start_date=2024-04-01&end_date=2024-04-13
```

**Response**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-04-01",
      "end_date": "2024-04-13"
    },
    "total_input_tokens": 150000,
    "total_output_tokens": 80000,
    "total_tokens": 230000,
    "total_calls": 100
  }
}
```

---

### FR-07-03: 비용 계산

```http
GET /llm-call-logs/cost-summary?start_date=2024-04-01&end_date=2024-04-13
```

**Response**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-04-01",
      "end_date": "2024-04-13"
    },
    "total_cost_usd": 125.50,
    "breakdown": [
      {
        "model": "gpt-4",
        "total_tokens": 230000,
        "cost_usd": 115.00
      },
      {
        "model": "gpt-3.5-turbo",
        "total_tokens": 50000,
        "cost_usd": 10.50
      }
    ]
  }
}
```

---

### FR-07-04: 성능 지표 수집

```http
GET /llm-call-logs/performance?start_date=2024-04-01&end_date=2024-04-13
```

**Response**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-04-01",
      "end_date": "2024-04-13"
    },
    "avg_latency_ms": 42000,
    "min_latency_ms": 15000,
    "max_latency_ms": 90000,
    "p50_latency_ms": 40000,
    "p95_latency_ms": 75000,
    "p99_latency_ms": 85000
  }
}
```

---

### FR-07-05: 실패 로그 조회

```http
GET /llm-call-logs/failures?start_date=2024-04-01&end_date=2024-04-13
```

**Response**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "log_id": 1001,
        "execution_id": 5002,
        "model": "gpt-4",
        "error_message": "API rate limit exceeded",
        "status": "FAIL",
        "created_at": "2024-04-13T08:30:00Z"
      }
    ],
    "total_failures": 5,
    "failure_rate": 0.05
  }
}
```

---

## FR-08: RAG 처리

### FR-08-01: 문서 청킹

```http
POST /rag/chunks
```

**Request Body**
```json
{
  "document_id": 1001,
  "chunk_size": 512,
  "overlap": 50
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "document_id": 1001,
    "chunks_created": 25,
    "chunks": [
      {
        "chunk_id": 5001,
        "chunk_text": "이력서 첫 번째 청크 내용...",
        "chunk_index": 0,
        "char_start": 0,
        "char_end": 512
      }
    ]
  }
}
```

---

### FR-08-02: 임베딩 생성

```http
POST /rag/embeddings
```

**Request Body**
```json
{
  "chunk_id": 5001,
  "model": "text-embedding-ada-002"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "embedding_id": 10001,
    "chunk_id": 5001,
    "embedding_model": "text-embedding-ada-002",
    "embedding_dim": 1536,
    "embedding_status": "READY",
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-08-03: 임베딩 상태 조회

```http
GET /rag/embeddings/{embedding_id}/status
```

**Response**
```json
{
  "success": true,
  "data": {
    "embedding_id": 10001,
    "embedding_status": "READY",
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

**상태값**
- `PENDING`: 생성 대기
- `READY`: 생성 완료
- `FAILED`: 생성 실패

---

### FR-08-04: 질문-근거 매핑

```http
POST /rag/question-evidences
```

**Request Body**
```json
{
  "question_id": 10001,
  "chunk_id": 5001,
  "similarity_score": 0.92
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "evidence_id": 20001,
    "question_id": 10001,
    "chunk_id": 5001,
    "similarity_score": 0.92,
    "created_at": "2024-04-13T10:30:00Z"
  }
}
```

---

### FR-08-05: 유사도 기반 근거 검색

```http
POST /rag/search-evidence
```

**Request Body**
```json
{
  "query_text": "프로젝트 관리 경험",
  "document_id": 1001,
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "query_text": "프로젝트 관리 경험",
    "results": [
      {
        "chunk_id": 5003,
        "chunk_text": "2020-2022년 ABC 프로젝트 관리자로...",
        "similarity_score": 0.92,
        "chunk_index": 2
      },
      {
        "chunk_id": 5007,
        "chunk_text": "10명 규모 팀 리딩 경험...",
        "similarity_score": 0.85,
        "chunk_index": 6
      }
    ],
    "total_results": 5
  }
}
```

---

## 공통 응답 코드

### 성공 응답

| Code | Description |
|:---|:---|
| 200 | OK - 성공 |
| 201 | Created - 생성 성공 |
| 204 | No Content - 삭제/수정 성공 (응답 본문 없음) |

### 에러 응답

| Code | Description |
|:---|:---|
| 400 | Bad Request - 잘못된 요청 |
| 401 | Unauthorized - 인증 실패 |
| 403 | Forbidden - 권한 없음 |
| 404 | Not Found - 리소스 없음 |
| 409 | Conflict - 중복 또는 충돌 |
| 422 | Unprocessable Entity - 유효성 검증 실패 |
| 429 | Too Many Requests - 요청 제한 초과 |
| 500 | Internal Server Error - 서버 오류 |
| 503 | Service Unavailable - 서비스 이용 불가 |

---

## 에러 처리

### 에러 응답 형식

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "요청 데이터가 유효하지 않습니다.",
    "details": {
      "field": "email",
      "reason": "올바른 이메일 형식이 아닙니다."
    }
  }
}
```

### 주요 에러 코드

| Error Code | Description |
|:---|:---|
| INVALID_REQUEST | 잘못된 요청 |
| UNAUTHORIZED | 인증 실패 |
| FORBIDDEN | 권한 없음 |
| NOT_FOUND | 리소스를 찾을 수 없음 |
| DUPLICATE_ENTRY | 중복 데이터 |
| VALIDATION_ERROR | 유효성 검증 실패 |
| EXTRACTION_FAILED | 텍스트 추출 실패 |
| LLM_EXECUTION_FAILED | LLM 실행 실패 |
| EMBEDDING_FAILED | 임베딩 생성 실패 |
| RATE_LIMIT_EXCEEDED | API 호출 제한 초과 |
| INTERNAL_ERROR | 내부 서버 오류 |

---

## 페이지네이션

모든 목록 조회 API는 다음 페이지네이션 파라미터를 지원합니다:

**Query Parameters**
- `page` (default: 1): 페이지 번호
- `limit` (default: 20, max: 100): 페이지당 항목 수

**Response Format**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 100,
      "items_per_page": 20
    }
  }
}
```

---

## 정렬 및 필터링

### 정렬

대부분의 목록 API는 `sort_by`와 `order` 파라미터를 지원합니다:

```http
GET /documents?sort_by=created_at&order=desc
```

- `sort_by`: 정렬 기준 필드
- `order`: `asc` (오름차순) | `desc` (내림차순)

### 필터링

각 리소스별 특화된 필터 파라미터를 제공합니다:

```http
GET /documents?document_type=RESUME&extraction_status=READY&start_date=2024-04-01
```

---

## Rate Limiting

API 호출은 다음 제한이 적용됩니다:

- **일반 API**: 1,000 requests/hour
- **LLM 실행 API**: 100 requests/hour
- **업로드 API**: 50 requests/hour

제한 초과 시 `429 Too Many Requests` 응답이 반환됩니다.

**Response Headers**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1713002400
```

---

## Webhooks (선택 사항)

특정 이벤트 발생 시 웹훅을 통해 알림을 받을 수 있습니다:

### 지원 이벤트

- `document.uploaded`: 문서 업로드 완료
- `document.extraction.completed`: 텍스트 추출 완료
- `document.extraction.failed`: 텍스트 추출 실패
- `llm.execution.completed`: LLM 실행 완료
- `llm.execution.failed`: LLM 실행 실패
- `embedding.completed`: 임베딩 생성 완료

### 웹훅 페이로드 예시

```json
{
  "event": "document.extraction.completed",
  "timestamp": "2024-04-13T10:35:00Z",
  "data": {
    "document_id": 1001,
    "extraction_status": "READY"
  }
}
```

---

## 변경 이력

### v1.0 (2024-04-13)
- 초기 API 문서 작성
- 전체 FR 모듈 API 정의
- 인증, 에러 처리, 페이지네이션 정의

