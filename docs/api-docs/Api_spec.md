# HR Copilot — API 명세서 (API Specification)

> **Base URL**: `https://api.hr-copilot.com/v1`  
> **인증 방식**: Bearer Token (JWT)  
> **응답 형식**: JSON  
> **문자 인코딩**: UTF-8

---

## 목차

1. [인증 (Authentication)](#1-인증-authentication)
2. [관리자 관리 (Manager)](#2-관리자-관리-manager)
3. [지원자 관리 (Candidate)](#3-지원자-관리-candidate)
4. [문서 관리 (Document)](#4-문서-관리-document)
5. [프롬프트 프로파일 (Prompt Profile)](#5-프롬프트-프로파일-prompt-profile)
6. [면접 세션 (Interview Session)](#6-면접-세션-interview-session)
7. [면접 질문 (Interview Question)](#7-면접-질문-interview-question)
8. [LLM 호출 로그 (LLM Call Log)](#8-llm-호출-로그-llm-call-log)

---

## 공통 응답 구조

### 성공 응답
```json
{
  "success": true,
  "data": {},
  "message": "Success"
}
```

### 오류 응답
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

### 공통 HTTP 상태 코드
- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `500 Internal Server Error`: 서버 오류

---

## 1. 인증 (Authentication)

### 1.1 로그인

**Endpoint**: `POST /auth/login`

**설명**: 관리자 계정으로 로그인하여 JWT 토큰을 발급받습니다.

**Request Body**:
```json
{
  "login_id": "admin@example.com",
  "password": "password123"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "manager": {
      "id": 1,
      "login_id": "admin@example.com",
      "name": "홍길동",
      "email": "admin@example.com",
      "role_type": "HR_MANAGER",
      "status": "ACTIVE"
    }
  },
  "message": "로그인 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `INVALID_CREDENTIALS` | "로그인 정보가 일치하지 않습니다." | login_id 또는 password 불일치 시 |
| **403** | `ACCOUNT_INACTIVE` | "비활성화된 계정입니다." | status가 INACTIVE일 때 |

---

### 1.2 로그아웃

**Endpoint**: `POST /auth/logout`

**설명**: 현재 세션을 종료합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "success": true,
  "message": "로그아웃 성공"
}
```

---

### 1.3 토큰 갱신

**Endpoint**: `POST /auth/refresh`

**설명**: 만료된 토큰을 갱신합니다.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "message": "토큰 갱신 성공"
}
```

---

## 2. 관리자 관리 (Manager)

### 2.1 관리자 목록 조회

**Endpoint**: `GET /managers`

**설명**: 등록된 전체 관리자 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `status` (string, optional): 상태 필터 (ACTIVE, INACTIVE)
- `role_type` (string, optional): 권한 필터

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "managers": [
      {
        "id": 1,
        "login_id": "admin@example.com",
        "name": "홍길동",
        "email": "admin@example.com",
        "status": "ACTIVE",
        "role_type": "HR_MANAGER",
        "created_at": "2025-01-15T10:30:00Z",
        "created_by": null
      },
      {
        "id": 2,
        "login_id": "manager01",
        "name": "김철수",
        "email": "manager01@example.com",
        "status": "ACTIVE",
        "role_type": "HR_MANAGER",
        "created_at": "2025-02-01T14:20:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 45,
      "items_per_page": 20
    }
  },
  "message": "관리자 목록 조회 성공"
}
```

---

### 2.2 관리자 상세 조회

**Endpoint**: `GET /managers/{id}`

**설명**: 특정 관리자의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "admin@example.com",
    "name": "홍길동",
    "email": "admin@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-01-15T10:30:00Z",
    "created_by": null,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "관리자 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |

---

### 2.3 관리자 생성

**Endpoint**: `POST /managers`

**설명**: 새로운 관리자 계정을 생성합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "login_id": "newmanager",
  "password": "SecurePassword123!",
  "name": "이영희",
  "email": "newmanager@example.com",
  "role_type": "HR_MANAGER"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "login_id": "newmanager",
    "name": "이영희",
    "email": "newmanager@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-04-15T09:15:00Z",
    "created_by": 1
  },
  "message": "관리자 생성 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_LOGIN_ID` | "이미 존재하는 로그인 ID입니다." | 중복된 login_id로 등록 시도 시 |
| **400** | `INVALID_PASSWORD` | "비밀번호는 8자 이상이어야 합니다." | 비밀번호 형식 미달 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

---

### 2.4 관리자 수정

**Endpoint**: `PUT /managers/{id}`

**설명**: 관리자 정보를 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Request Body**:
```json
{
  "name": "이영희",
  "email": "updated@example.com",
  "role_type": "HR_MANAGER"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "login_id": "newmanager",
    "name": "이영희",
    "email": "updated@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-04-15T09:15:00Z",
    "created_by": 1
  },
  "message": "관리자 정보 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

---

### 2.5 관리자 상태 변경

**Endpoint**: `PATCH /managers/{id}/status`

**설명**: 관리자 계정의 활성/비활성 상태를 변경합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Request Body**:
```json
{
  "status": "INACTIVE"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "status": "INACTIVE"
  },
  "message": "관리자 상태 변경 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태값입니다." | 잘못된 status 값일 때 |

---

### 2.6 관리자 삭제 (논리 삭제)

**Endpoint**: `DELETE /managers/{id}`

**설명**: 관리자를 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "deleted_at": "2025-04-15T10:30:00Z",
    "deleted_by": 1
  },
  "message": "관리자 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |

---

## 3. 지원자 관리 (Candidate)

### 3.1 지원자 목록 조회

**Endpoint**: `GET /candidates`

**설명**: 등록된 지원자 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `apply_status` (string, optional): 지원 상태 필터 (APPLIED, SCREENING, INTERVIEW, ACCEPTED, REJECTED)
- `search` (string, optional): 이름/이메일 검색

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "candidates": [
      {
        "id": 1,
        "name": "김지원",
        "email": "jiwon.kim@example.com",
        "phone": "010-1234-5678",
        "birth_date": "1995-03-15",
        "apply_status": "SCREENING",
        "created_at": "2025-04-01T09:00:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "name": "박민수",
        "email": "minsu.park@example.com",
        "phone": "010-9876-5432",
        "birth_date": "1993-07-22",
        "apply_status": "INTERVIEW",
        "created_at": "2025-04-02T14:30:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 87,
      "items_per_page": 20
    }
  },
  "message": "지원자 목록 조회 성공"
}
```

---

### 3.2 지원자 상세 조회

**Endpoint**: `GET /candidates/{id}`

**설명**: 특정 지원자의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "김지원",
    "email": "jiwon.kim@example.com",
    "phone": "010-1234-5678",
    "birth_date": "1995-03-15",
    "apply_status": "SCREENING",
    "created_at": "2025-04-01T09:00:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "지원자 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |

---

### 3.3 지원자 등록

**Endpoint**: `POST /candidates`

**설명**: 새로운 지원자를 등록합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "name": "정수현",
  "email": "suhyun.jung@example.com",
  "phone": "010-5555-6666",
  "birth_date": "1997-11-08"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "정수현",
    "email": "suhyun.jung@example.com",
    "phone": "010-5555-6666",
    "birth_date": "1997-11-08",
    "apply_status": "APPLIED",
    "created_at": "2025-04-15T10:20:00Z",
    "created_by": 1
  },
  "message": "지원자 등록 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_EMAIL` | "이미 등록된 이메일입니다." | 중복된 email로 등록 시도 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |
| **400** | `INVALID_PHONE` | "유효하지 않은 전화번호 형식입니다." | 전화번호 형식 오류 시 |

---

### 3.4 지원자 정보 수정

**Endpoint**: `PUT /candidates/{id}`

**설명**: 지원자 정보를 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID

**Request Body**:
```json
{
  "name": "정수현",
  "email": "newsuhyun@example.com",
  "phone": "010-5555-7777",
  "birth_date": "1997-11-08"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "정수현",
    "email": "newsuhyun@example.com",
    "phone": "010-5555-7777",
    "birth_date": "1997-11-08",
    "apply_status": "APPLIED",
    "created_at": "2025-04-15T10:20:00Z",
    "created_by": 1
  },
  "message": "지원자 정보 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |
| **400** | `INVALID_PHONE` | "유효하지 않은 전화번호 형식입니다." | 전화번호 형식 오류 시 |

---

### 3.5 지원자 상태 변경

**Endpoint**: `PATCH /candidates/{id}/status`

**설명**: 지원자의 진행 상태를 변경합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID

**Request Body**:
```json
{
  "apply_status": "INTERVIEW"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "apply_status": "INTERVIEW"
  },
  "message": "지원자 상태 변경 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태값입니다." | 잘못된 apply_status 값일 때 |

---

### 3.6 지원자 삭제 (논리 삭제)

**Endpoint**: `DELETE /candidates/{id}`

**설명**: 지원자를 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "deleted_at": "2025-04-15T11:00:00Z",
    "deleted_by": 1
  },
  "message": "지원자 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 지원자입니다." | deleted_at이 NULL이 아닐 때 |

---

## 4. 문서 관리 (Document)

### 4.1 문서 목록 조회

**Endpoint**: `GET /documents`

**설명**: 등록된 문서 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `candidate_id` (integer, optional): 지원자 ID 필터
- `document_type` (string, optional): 문서 유형 필터 (RESUME, PORTFOLIO)
- `extract_status` (string, optional): 추출 상태 필터 (PENDING, SUCCESS, FAILED)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": 1,
        "document_type": "RESUME",
        "title": "김지원_이력서.pdf",
        "file_path": "/uploads/2025/04/resume_001.pdf",
        "candidate_id": 1,
        "extract_status": "SUCCESS",
        "created_at": "2025-04-01T09:15:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "document_type": "PORTFOLIO",
        "title": "김지원_포트폴리오.pdf",
        "file_path": "/uploads/2025/04/portfolio_001.pdf",
        "candidate_id": 1,
        "extract_status": "SUCCESS",
        "created_at": "2025-04-01T09:20:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 8,
      "total_items": 152,
      "items_per_page": 20
    }
  },
  "message": "문서 목록 조회 성공"
}
```

---

### 4.2 문서 상세 조회

**Endpoint**: `GET /documents/{id}`

**설명**: 특정 문서의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 문서 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "document_type": "RESUME",
    "title": "김지원_이력서.pdf",
    "file_path": "/uploads/2025/04/resume_001.pdf",
    "candidate_id": 1,
    "extracted_text": "이름: 김지원\n이메일: jiwon.kim@example.com\n...",
    "extract_status": "SUCCESS",
    "created_at": "2025-04-01T09:15:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "문서 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |

---

### 4.3 문서 업로드

**Endpoint**: `POST /documents`

**설명**: 새로운 문서를 업로드합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data)**:
- `file` (file, required): 업로드할 파일
- `candidate_id` (integer, required): 지원자 ID
- `document_type` (string, required): 문서 유형 (RESUME, PORTFOLIO)
- `title` (string, optional): 문서 제목 (미입력 시 파일명 사용)

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 15,
    "document_type": "RESUME",
    "title": "정수현_이력서.pdf",
    "file_path": "/uploads/2025/04/resume_015.pdf",
    "candidate_id": 10,
    "extract_status": "PENDING",
    "created_at": "2025-04-15T10:30:00Z",
    "created_by": 1
  },
  "message": "문서 업로드 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **400** | `INVALID_FILE_TYPE` | "허용되지 않는 파일 형식입니다." | PDF가 아닌 파일 업로드 시 |
| **400** | `FILE_TOO_LARGE` | "파일 크기가 제한을 초과했습니다." | 파일 크기가 최대 허용치를 초과할 때 |
| **400** | `INVALID_DOCUMENT_TYPE` | "유효하지 않은 문서 유형입니다." | document_type이 RESUME, PORTFOLIO가 아닐 때 |

---

### 4.4 문서 텍스트 추출 (비동기)

**Endpoint**: `POST /documents/{id}/extract`

**설명**: 업로드된 문서에서 텍스트를 추출합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 문서 ID

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "id": 15,
    "extract_status": "PROCESSING",
    "message": "텍스트 추출이 시작되었습니다."
  },
  "message": "텍스트 추출 요청 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |
| **400** | `ALREADY_EXTRACTED` | "이미 텍스트 추출이 완료되었습니다." | extract_status가 SUCCESS일 때 |
| **400** | `EXTRACTION_IN_PROGRESS` | "텍스트 추출이 진행 중입니다." | extract_status가 PROCESSING일 때 |

---

### 4.5 문서 추출 상태 조회

**Endpoint**: `GET /documents/{id}/extract-status`

**설명**: 문서 텍스트 추출 상태를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 문서 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 15,
    "extract_status": "SUCCESS",
    "extracted_text": "이름: 정수현\n학력: 서울대학교 컴퓨터공학과\n..."
  },
  "message": "추출 상태 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |

---

### 4.6 문서 삭제 (논리 삭제)

**Endpoint**: `DELETE /documents/{id}`

**설명**: 문서를 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 문서 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 15,
    "deleted_at": "2025-04-15T11:30:00Z",
    "deleted_by": 1
  },
  "message": "문서 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 문서입니다." | deleted_at이 NULL이 아닐 때 |

---

## 5. 프롬프트 프로파일 (Prompt Profile)

### 5.1 프롬프트 프로파일 목록 조회

**Endpoint**: `GET /prompt-profiles`

**설명**: 등록된 프롬프트 프로파일 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "prompt_profiles": [
      {
        "id": 1,
        "profile_key": "BACKEND_DEVELOPER",
        "system_prompt": "당신은 백엔드 개발자 채용을 위한 HR 전문가입니다...",
        "output_schema": "{\"questions\": [{\"category\": \"...\", \"question_text\": \"...\"}]}",
        "created_at": "2025-03-01T10:00:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "profile_key": "FRONTEND_DEVELOPER",
        "system_prompt": "당신은 프론트엔드 개발자 채용을 위한 HR 전문가입니다...",
        "output_schema": "{\"questions\": [{\"category\": \"...\", \"question_text\": \"...\"}]}",
        "created_at": "2025-03-05T14:30:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 5,
      "items_per_page": 20
    }
  },
  "message": "프롬프트 프로파일 목록 조회 성공"
}
```

---

### 5.2 프롬프트 프로파일 상세 조회

**Endpoint**: `GET /prompt-profiles/{id}`

**설명**: 특정 프롬프트 프로파일의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 프롬프트 프로파일 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "profile_key": "BACKEND_DEVELOPER",
    "system_prompt": "당신은 백엔드 개발자 채용을 위한 HR 전문가입니다. 지원자의 이력서를 분석하여 기술 역량, 프로젝트 경험, 문제 해결 능력을 평가하는 면접 질문을 생성하세요.",
    "output_schema": "{\"questions\": [{\"category\": \"string\", \"question_text\": \"string\", \"expected_answer\": \"string\", \"evaluation_guide\": \"string\"}]}",
    "created_at": "2025-03-01T10:00:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "프롬프트 프로파일 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프롬프트 프로파일을 찾을 수 없습니다." | 존재하지 않는 프로파일 ID일 때 |

---

### 5.3 프롬프트 프로파일 생성

**Endpoint**: `POST /prompt-profiles`

**설명**: 새로운 프롬프트 프로파일을 생성합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "profile_key": "DATA_SCIENTIST",
  "system_prompt": "당신은 데이터 사이언티스트 채용을 위한 HR 전문가입니다. 통계, 머신러닝, 데이터 분석 역량을 평가하는 질문을 생성하세요.",
  "output_schema": "{\"questions\": [{\"category\": \"string\", \"question_text\": \"string\", \"expected_answer\": \"string\"}]}"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 6,
    "profile_key": "DATA_SCIENTIST",
    "system_prompt": "당신은 데이터 사이언티스트 채용을 위한 HR 전문가입니다...",
    "output_schema": "{\"questions\": [{\"category\": \"string\", \"question_text\": \"string\", \"expected_answer\": \"string\"}]}",
    "created_at": "2025-04-15T11:00:00Z",
    "created_by": 1
  },
  "message": "프롬프트 프로파일 생성 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_PROFILE_KEY` | "이미 존재하는 프로파일 키입니다." | 중복된 profile_key로 등록 시도 시 |
| **400** | `INVALID_JSON_SCHEMA` | "유효하지 않은 JSON 스키마입니다." | output_schema가 유효한 JSON이 아닐 때 |

---

### 5.4 프롬프트 프로파일 수정

**Endpoint**: `PUT /prompt-profiles/{id}`

**설명**: 프롬프트 프로파일을 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 프롬프트 프로파일 ID

**Request Body**:
```json
{
  "system_prompt": "수정된 시스템 프롬프트 내용...",
  "output_schema": "{\"questions\": [{\"category\": \"string\", \"question_text\": \"string\"}]}"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 6,
    "profile_key": "DATA_SCIENTIST",
    "system_prompt": "수정된 시스템 프롬프트 내용...",
    "output_schema": "{\"questions\": [{\"category\": \"string\", \"question_text\": \"string\"}]}",
    "created_at": "2025-04-15T11:00:00Z",
    "created_by": 1
  },
  "message": "프롬프트 프로파일 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프롬프트 프로파일을 찾을 수 없습니다." | 존재하지 않는 프로파일 ID일 때 |
| **400** | `INVALID_JSON_SCHEMA` | "유효하지 않은 JSON 스키마입니다." | output_schema가 유효한 JSON이 아닐 때 |

---

### 5.5 프롬프트 프로파일 삭제 (논리 삭제)

**Endpoint**: `DELETE /prompt-profiles/{id}`

**설명**: 프롬프트 프로파일을 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 프롬프트 프로파일 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 6,
    "deleted_at": "2025-04-15T12:00:00Z",
    "deleted_by": 1
  },
  "message": "프롬프트 프로파일 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프롬프트 프로파일을 찾을 수 없습니다." | 존재하지 않는 프로파일 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 프로파일입니다." | deleted_at이 NULL이 아닐 때 |

---

## 6. 면접 세션 (Interview Session)

### 6.1 면접 세션 목록 조회

**Endpoint**: `GET /interview-sessions`

**설명**: 생성된 면접 세션 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `candidate_id` (integer, optional): 지원자 ID 필터
- `target_job` (string, optional): 목표 직무 필터

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "interview_sessions": [
      {
        "id": 1,
        "candidate_id": 1,
        "target_job": "BACKEND_DEVELOPER",
        "difficulty_level": "INTERMEDIATE",
        "created_at": "2025-04-05T10:00:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "candidate_id": 2,
        "target_job": "FRONTEND_DEVELOPER",
        "difficulty_level": "SENIOR",
        "created_at": "2025-04-06T14:30:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 45,
      "items_per_page": 20
    }
  },
  "message": "면접 세션 목록 조회 성공"
}
```

---

### 6.2 면접 세션 상세 조회

**Endpoint**: `GET /interview-sessions/{id}`

**설명**: 특정 면접 세션의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 세션 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "candidate_id": 1,
    "target_job": "BACKEND_DEVELOPER",
    "difficulty_level": "INTERMEDIATE",
    "created_at": "2025-04-05T10:00:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null,
    "candidate": {
      "id": 1,
      "name": "김지원",
      "email": "jiwon.kim@example.com"
    }
  },
  "message": "면접 세션 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |

---

### 6.3 면접 세션 생성

**Endpoint**: `POST /interview-sessions`

**설명**: 새로운 면접 세션을 생성합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "candidate_id": 10,
  "target_job": "DATA_SCIENTIST",
  "difficulty_level": "INTERMEDIATE"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 20,
    "candidate_id": 10,
    "target_job": "DATA_SCIENTIST",
    "difficulty_level": "INTERMEDIATE",
    "created_at": "2025-04-15T12:00:00Z",
    "created_by": 1
  },
  "message": "면접 세션 생성 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **400** | `INVALID_TARGET_JOB` | "유효하지 않은 목표 직무입니다." | target_job이 유효한 값이 아닐 때 |
| **400** | `INVALID_DIFFICULTY_LEVEL` | "유효하지 않은 난이도입니다." | difficulty_level이 JUNIOR, INTERMEDIATE, SENIOR가 아닐 때 |

---

### 6.4 면접 세션 수정

**Endpoint**: `PUT /interview-sessions/{id}`

**설명**: 면접 세션 정보를 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 세션 ID

**Request Body**:
```json
{
  "target_job": "DATA_SCIENTIST",
  "difficulty_level": "SENIOR"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 20,
    "candidate_id": 10,
    "target_job": "DATA_SCIENTIST",
    "difficulty_level": "SENIOR",
    "created_at": "2025-04-15T12:00:00Z",
    "created_by": 1
  },
  "message": "면접 세션 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |
| **400** | `INVALID_TARGET_JOB` | "유효하지 않은 목표 직무입니다." | target_job이 유효한 값이 아닐 때 |
| **400** | `INVALID_DIFFICULTY_LEVEL` | "유효하지 않은 난이도입니다." | difficulty_level이 JUNIOR, INTERMEDIATE, SENIOR가 아닐 때 |

---

### 6.5 면접 세션 삭제 (논리 삭제)

**Endpoint**: `DELETE /interview-sessions/{id}`

**설명**: 면접 세션을 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 세션 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 20,
    "deleted_at": "2025-04-15T13:00:00Z",
    "deleted_by": 1
  },
  "message": "면접 세션 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 세션입니다." | deleted_at이 NULL이 아닐 때 |

---

## 7. 면접 질문 (Interview Question)

### 7.1 면접 질문 목록 조회

**Endpoint**: `GET /interview-questions`

**설명**: 생성된 면접 질문 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `interview_sessions_id` (integer, optional): 면접 세션 ID 필터
- `category` (string, optional): 질문 카테고리 필터

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "interview_questions": [
      {
        "id": 1,
        "interview_sessions_id": 1,
        "category": "TECHNICAL",
        "question_text": "프로젝트에서 RESTful API를 설계할 때 어떤 원칙을 적용하셨나요?",
        "created_at": "2025-04-05T10:30:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "interview_sessions_id": 1,
        "category": "EXPERIENCE",
        "question_text": "데이터베이스 성능 최적화를 위해 어떤 전략을 사용하셨나요?",
        "created_at": "2025-04-05T10:30:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 4,
      "total_items": 68,
      "items_per_page": 20
    }
  },
  "message": "면접 질문 목록 조회 성공"
}
```

---

### 7.2 면접 질문 상세 조회

**Endpoint**: `GET /interview-questions/{id}`

**설명**: 특정 면접 질문의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 질문 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "interview_sessions_id": 1,
    "category": "TECHNICAL",
    "question_text": "프로젝트에서 RESTful API를 설계할 때 어떤 원칙을 적용하셨나요?",
    "expected_answer": "HTTP 메서드의 적절한 사용, 명확한 리소스 URI 설계, 상태 코드 활용 등",
    "follow_up_question": "API 버전 관리는 어떻게 하셨나요?",
    "evaluation_guide": "REST 원칙에 대한 이해도, 실무 적용 경험, 설계 사고 과정 평가",
    "question_rationale": "지원자의 이력서에 'RESTful API 설계 및 개발' 경험이 명시되어 있어, 실제 설계 원칙 적용 능력을 확인하기 위한 질문",
    "created_at": "2025-04-05T10:30:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "면접 질문 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "면접 질문을 찾을 수 없습니다." | 존재하지 않는 질문 ID일 때 |

---

### 7.3 면접 질문 생성 (AI 기반)

**Endpoint**: `POST /interview-questions/generate`

**설명**: AI를 활용하여 면접 질문을 자동 생성합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "interview_sessions_id": 20,
  "prompt_profile_id": 6,
  "document_id": 15,
  "question_count": 10
}
```

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "task_id": "gen_20250415_1200_abc123",
    "interview_sessions_id": 20,
    "status": "PROCESSING",
    "message": "면접 질문 생성이 시작되었습니다."
  },
  "message": "면접 질문 생성 요청 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 interview_sessions_id일 때 |
| **404** | `PROFILE_NOT_FOUND` | "프롬프트 프로파일을 찾을 수 없습니다." | 존재하지 않는 prompt_profile_id일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |
| **400** | `INVALID_QUESTION_COUNT` | "질문 개수는 1개 이상 20개 이하여야 합니다." | question_count가 유효 범위를 벗어날 때 |
| **400** | `EXTRACTION_NOT_COMPLETED` | "문서 텍스트 추출이 완료되지 않았습니다." | document의 extract_status가 SUCCESS가 아닐 때 |

---

### 7.4 면접 질문 생성 상태 조회

**Endpoint**: `GET /interview-questions/generate/{task_id}`

**설명**: AI 질문 생성 작업의 진행 상태를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `task_id` (string, required): 생성 작업 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "task_id": "gen_20250415_1200_abc123",
    "status": "COMPLETED",
    "generated_count": 10,
    "interview_sessions_id": 20,
    "created_questions": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  },
  "message": "질문 생성 완료"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `TASK_NOT_FOUND` | "생성 작업을 찾을 수 없습니다." | 존재하지 않는 task_id일 때 |

---

### 7.5 면접 질문 수정

**Endpoint**: `PUT /interview-questions/{id}`

**설명**: 생성된 면접 질문을 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 질문 ID

**Request Body**:
```json
{
  "category": "TECHNICAL",
  "question_text": "수정된 질문 내용",
  "expected_answer": "수정된 기대 답변",
  "follow_up_question": "수정된 꼬리 질문",
  "evaluation_guide": "수정된 평가 가이드"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "interview_sessions_id": 1,
    "category": "TECHNICAL",
    "question_text": "수정된 질문 내용",
    "expected_answer": "수정된 기대 답변",
    "follow_up_question": "수정된 꼬리 질문",
    "evaluation_guide": "수정된 평가 가이드",
    "question_rationale": "지원자의 이력서에 'RESTful API 설계 및 개발' 경험이 명시되어 있어, 실제 설계 원칙 적용 능력을 확인하기 위한 질문",
    "created_at": "2025-04-05T10:30:00Z",
    "created_by": 1
  },
  "message": "면접 질문 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "면접 질문을 찾을 수 없습니다." | 존재하지 않는 질문 ID일 때 |
| **400** | `INVALID_CATEGORY` | "유효하지 않은 카테고리입니다." | category가 유효한 값이 아닐 때 |

---

### 7.6 면접 질문 삭제 (논리 삭제)

**Endpoint**: `DELETE /interview-questions/{id}`

**설명**: 면접 질문을 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 면접 질문 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "deleted_at": "2025-04-15T14:00:00Z",
    "deleted_by": 1
  },
  "message": "면접 질문 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "면접 질문을 찾을 수 없습니다." | 존재하지 않는 질문 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 질문입니다." | deleted_at이 NULL이 아닐 때 |

---

## 8. LLM 호출 로그 (LLM Call Log)

### 8.1 LLM 호출 로그 목록 조회

**Endpoint**: `GET /llm-call-logs`

**설명**: LLM API 호출 이력을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `candidate_id` (integer, optional): 지원자 ID 필터
- `interview_sessions_id` (integer, optional): 면접 세션 ID 필터
- `call_status` (string, optional): 호출 상태 필터 (SUCCESS, FAILED)
- `start_date` (string, optional): 시작 날짜 (YYYY-MM-DD)
- `end_date` (string, optional): 종료 날짜 (YYYY-MM-DD)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "llm_call_logs": [
      {
        "id": 1,
        "candidate_id": 1,
        "document_id": 1,
        "prompt_profile_id": 1,
        "interview_sessions_id": 1,
        "model_name": "gpt-4",
        "total_tokens": 3500,
        "cost_amount": 0.105,
        "call_status": "SUCCESS",
        "call_time": 4500,
        "created_at": "2025-04-05T10:30:00Z",
        "created_by": 1
      },
      {
        "id": 2,
        "candidate_id": 2,
        "document_id": 3,
        "prompt_profile_id": 2,
        "interview_sessions_id": 2,
        "model_name": "gpt-4",
        "total_tokens": 4200,
        "cost_amount": 0.126,
        "call_status": "SUCCESS",
        "call_time": 5200,
        "created_at": "2025-04-06T14:45:00Z",
        "created_by": 1
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 6,
      "total_items": 112,
      "items_per_page": 20
    },
    "summary": {
      "total_calls": 112,
      "successful_calls": 108,
      "failed_calls": 4,
      "total_tokens": 385000,
      "total_cost": 11.55
    }
  },
  "message": "LLM 호출 로그 목록 조회 성공"
}
```

---

### 8.2 LLM 호출 로그 상세 조회

**Endpoint**: `GET /llm-call-logs/{id}`

**설명**: 특정 LLM 호출의 상세 로그를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): LLM 호출 로그 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "candidate_id": 1,
    "document_id": 1,
    "prompt_profile_id": 1,
    "interview_sessions_id": 1,
    "model_name": "gpt-4",
    "response_json": {
      "questions": [
        {
          "category": "TECHNICAL",
          "question_text": "RESTful API 설계 원칙에 대해 설명해주세요.",
          "expected_answer": "...",
          "evaluation_guide": "..."
        }
      ]
    },
    "total_tokens": 3500,
    "cost_amount": 0.105,
    "call_status": "SUCCESS",
    "call_time": 4500,
    "created_at": "2025-04-05T10:30:00Z",
    "created_by": 1,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "LLM 호출 로그 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `LOG_NOT_FOUND` | "LLM 호출 로그를 찾을 수 없습니다." | 존재하지 않는 로그 ID일 때 |

---

### 8.3 LLM 사용 통계 조회

**Endpoint**: `GET /llm-call-logs/statistics`

**설명**: LLM 사용량 및 비용 통계를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `start_date` (string, required): 시작 날짜 (YYYY-MM-DD)
- `end_date` (string, required): 종료 날짜 (YYYY-MM-DD)
- `group_by` (string, optional): 그룹화 기준 (daily, weekly, monthly)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2025-04-01",
      "end_date": "2025-04-15"
    },
    "total_calls": 156,
    "successful_calls": 150,
    "failed_calls": 6,
    "success_rate": 96.15,
    "total_tokens": 547000,
    "total_cost": 16.41,
    "average_call_time": 4800,
    "by_model": {
      "gpt-4": {
        "calls": 120,
        "tokens": 420000,
        "cost": 12.60
      },
      "gpt-3.5-turbo": {
        "calls": 36,
        "tokens": 127000,
        "cost": 3.81
      }
    },
    "daily_breakdown": [
      {
        "date": "2025-04-01",
        "calls": 12,
        "tokens": 42000,
        "cost": 1.26
      },
      {
        "date": "2025-04-02",
        "calls": 15,
        "tokens": 52500,
        "cost": 1.58
      }
    ]
  },
  "message": "LLM 사용 통계 조회 성공"
}
```

---

## 부록: 상태값 정의 (Enum Values)

### 관리자 상태 (Manager Status)
- `ACTIVE`: 활성
- `INACTIVE`: 비활성
- `LOCKED`: 잠금

### 관리자 권한 (Manager Role Type)
- `SUPER_ADMIN`: 최고 관리자
- `HR_MANAGER`: HR 관리자
- `VIEWER`: 조회 전용

### 지원자 상태 (Candidate Apply Status)
- `APPLIED`: 지원 완료
- `SCREENING`: 서류 심사 중
- `INTERVIEW`: 면접 진행 중
- `ACCEPTED`: 합격
- `REJECTED`: 불합격

### 문서 유형 (Document Type)
- `RESUME`: 이력서
- `PORTFOLIO`: 포트폴리오

### 문서 추출 상태 (Extract Status)
- `PENDING`: 대기 중
- `PROCESSING`: 처리 중
- `SUCCESS`: 성공
- `FAILED`: 실패

### 질문 카테고리 (Question Category)
- `TECHNICAL`: 기술 역량
- `EXPERIENCE`: 경험/프로젝트
- `PROBLEM_SOLVING`: 문제 해결
- `COMMUNICATION`: 의사소통
- `CULTURE_FIT`: 문화 적합성

### 난이도 (Difficulty Level)
- `JUNIOR`: 주니어
- `INTERMEDIATE`: 중급
- `SENIOR`: 시니어

### LLM 호출 상태 (Call Status)
- `SUCCESS`: 성공
- `FAILED`: 실패
- `TIMEOUT`: 타임아웃