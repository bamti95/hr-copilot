# HR Copilot BS - API 문서

## 목차
1. [개요](#개요)
2. [인증](#인증)
3. [공통 규격](#공통-규격)
4. [API 엔드포인트](#api-엔드포인트)
   - [관리자 계정 관리](#1-관리자-계정-관리)
   - [서비스 사용자 관리](#2-서비스-사용자-관리)
   - [지원자 관리](#3-지원자-관리)
   - [문서 관리](#4-문서-관리)
   - [프롬프트 관리](#5-프롬프트-관리)
   - [면접 질문 관리](#6-면접-질문-관리)
   - [LLM 로그 관리](#7-llm-로그-관리)

---

## 개요

### 기본 정보
- **Base URL**: `https://api.hrcopilot.example.com`
- **Protocol**: HTTPS
- **Data Format**: JSON
- **Character Encoding**: UTF-8

---

## 인증

### 인증 방식
Bearer Token 기반 JWT 인증을 사용합니다.

### 인증 헤더
```
Authorization: Bearer {access_token}
```

---

## 공통 규격

### 응답 형식

#### 성공 응답
```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다.",
  "data": {
    // 응답 데이터
  }
}
```

#### 실패 응답
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

### 페이지네이션

목록 조회 API는 다음과 같은 페이지네이션을 지원합니다.

#### 요청 파라미터
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `sort`: 정렬 기준 (예: `created_at:desc`)

#### 응답 형식
```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 10,
      "total_items": 200,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 공통 에러 코드

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `AUTH_REQUIRED` | "인증이 필요합니다." | 인증 토큰이 없을 때 |
| **401** | `AUTH_INVALID` | "인증 정보가 유효하지 않습니다." | 토큰이 만료되었거나 유효하지 않을 때 |
| **403** | `FORBIDDEN` | "권한이 없습니다." | 접근 권한이 없을 때 |
| **404** | `NOT_FOUND` | "리소스를 찾을 수 없습니다." | 요청한 리소스가 존재하지 않을 때 |
| **400** | `VALIDATION_ERROR` | "입력값 검증에 실패했습니다." | 요청 데이터가 유효하지 않을 때 |
| **409** | `DUPLICATE_ENTRY` | "중복된 데이터입니다." | 고유 제약조건 위반 시 |
| **500** | `INTERNAL_ERROR` | "서버 내부 오류가 발생했습니다." | 서버 오류 발생 시 |

---

## API 엔드포인트

## 1. 관리자 계정 관리

### 1.1 관리자 등록
**FR-01-01: 관리자 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/managers`
- **Description:** 슈퍼 관리자 계정을 등록합니다. 비밀번호는 BCrypt 해시로 저장됩니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `login_id` | `string` | **필수** | 이메일 형식 | 관리자 로그인 ID |
| `password` | `string` | **필수** | 8자 이상 | 로그인 비밀번호 |
| `name` | `string` | **필수** | 2~50자 | 관리자 이름 |
| `email` | `string` | **필수** | 이메일 형식 | 관리자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 관리자 전화번호 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "관리자 등록이 완료되었습니다.",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "login_id": "admin@example.com",
    "name": "홍길동",
    "email": "admin@example.com",
    "phone": "010-1234-5678",
    "status": "ACTIVE",
    "created_at": "2024-04-14T10:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_LOGIN_ID` | "이미 사용 중인 로그인 ID입니다." | 중복된 login_id로 등록 시도 시 |
| **400** | `INVALID_PASSWORD` | "비밀번호는 8자 이상이어야 합니다." | 비밀번호 형식 미달 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

#### 데이터 제약 조건 (Validation)
1. **login_id**: 시스템 내 중복 불가 (Unique Constraint)
2. **password**: BCrypt 해시로 저장 필수
3. **email**: 이메일 형식 검증 필요

---

### 1.2 관리자 로그인
**FR-01-02: 관리자 로그인**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/auth/login`
- **Description:** login_id와 password로 관리자 인증을 수행하고 JWT 토큰을 발급합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `login_id` | `string` | **필수** | - | 관리자 로그인 ID |
| `password` | `string` | **필수** | - | 로그인 비밀번호 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "로그인이 완료되었습니다.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "manager": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "login_id": "admin@example.com",
      "name": "홍길동",
      "status": "ACTIVE",
      "last_login_at": "2024-04-14T10:30:00Z"
    }
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `INVALID_CREDENTIALS` | "로그인 정보가 일치하지 않습니다." | login_id 또는 password 불일치 시 |
| **403** | `ACCOUNT_INACTIVE` | "비활성화된 계정입니다." | status가 INACTIVE일 때 |
| **403** | `ACCOUNT_LOCKED` | "잠긴 계정입니다. 관리자에게 문의하세요." | status가 LOCK일 때 |

#### 데이터 제약 조건 (Validation)
1. **last_login_at**: 로그인 성공 시 자동 갱신
2. **status**: ACTIVE 상태만 로그인 가능

---

### 1.3 사용자 계정 요청 승인
**FR-01-04: 사용자 계정 요청 승인**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/approve`
- **Description:** REQUESTED 상태의 사용자 계정 요청을 승인합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 승인할 사용자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `role_type` | `string` | **필수** | VIEWER, EDITOR, ADMIN | 부여할 권한 |
| `approval_note` | `string` | 선택 | 최대 500자 | 승인 메모 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자 계정이 승인되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "김철수",
    "email": "user@example.com",
    "request_status": "APPROVED",
    "status": "ACTIVE",
    "role_type": "EDITOR",
    "approved_by": "550e8400-e29b-41d4-a716-446655440000",
    "approved_at": "2024-04-14T12:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_STATUS` | "승인 가능한 상태가 아닙니다." | request_status가 REQUESTED가 아닐 때 |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **request_status**: REQUESTED → APPROVED로 변경
2. **status**: ACTIVE로 설정
3. **approved_by**: 요청한 관리자 ID 자동 저장

---

### 1.4 사용자 계정 요청 반려
**FR-01-04: 사용자 계정 요청 승인 (반려)**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/reject`
- **Description:** REQUESTED 상태의 사용자 계정 요청을 반려합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 반려할 사용자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `rejection_reason` | `string` | **필수** | 최대 500자 | 반려 사유 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자 계정 요청이 반려되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "request_status": "REJECTED",
    "rejection_reason": "신청 정보가 불충분합니다.",
    "rejected_by": "550e8400-e29b-41d4-a716-446655440000",
    "rejected_at": "2024-04-14T12:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_STATUS` | "반려 가능한 상태가 아닙니다." | request_status가 REQUESTED가 아닐 때 |
| **400** | `REJECTION_REASON_REQUIRED` | "반려 사유는 필수입니다." | rejection_reason이 없을 때 |

---

## 2. 서비스 사용자 관리

### 2.1 사용자 계정 생성 요청
**FR-02-01: 사용자 계정 생성 요청 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/users/request`
- **Description:** 서비스 사용자 계정 생성을 요청합니다. 관리자 승인 후 활성화됩니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `requested_by_name` | `string` | **필수** | 2~50자 | 요청자 이름 |
| `requested_by_email` | `string` | **필수** | 이메일 형식 | 요청자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 요청자 전화번호 |
| `department` | `string` | 선택 | 최대 100자 | 소속 부서 |
| `request_note` | `string` | 선택 | 최대 500자 | 요청 사유 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "계정 생성 요청이 접수되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "requested_by_name": "김철수",
    "requested_by_email": "user@example.com",
    "phone": "010-9876-5432",
    "department": "인사팀",
    "request_status": "REQUESTED",
    "request_note": "채용 시스템 사용을 위해 계정이 필요합니다.",
    "created_at": "2024-04-14T11:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_EMAIL` | "이미 요청된 이메일입니다." | 중복된 이메일로 요청 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

#### 데이터 제약 조건 (Validation)
1. **request_status**: 자동으로 REQUESTED로 설정
2. **requested_by_email**: 중복 요청 불가

---

### 2.2 사용자 목록 조회
**FR-02-09: 사용자 목록 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/users`
- **Description:** 전체 사용자 목록을 조회합니다. (request_status 포함)

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |
| `request_status` | `string` | 선택 | - | REQUESTED, APPROVED, REJECTED |
| `status` | `string` | 선택 | - | ACTIVE, INACTIVE |
| `search` | `string` | 선택 | - | 이름, 이메일 검색 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "requested_by_name": "김철수",
        "requested_by_email": "user@example.com",
        "phone": "010-9876-5432",
        "department": "인사팀",
        "request_status": "APPROVED",
        "status": "ACTIVE",
        "role_type": "EDITOR",
        "created_at": "2024-04-14T11:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 100,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `AUTH_REQUIRED` | "인증이 필요합니다." | 인증 토큰이 없을 때 |

---

### 2.3 사용자 상세 조회
**FR-02-10: 사용자 상세 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/users/{user_id}`
- **Description:** 특정 사용자의 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 사용자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "requested_by_name": "김철수",
    "requested_by_email": "user@example.com",
    "phone": "010-9876-5432",
    "department": "인사팀",
    "request_status": "APPROVED",
    "status": "ACTIVE",
    "role_type": "EDITOR",
    "request_note": "채용 시스템 사용을 위해 계정이 필요합니다.",
    "approved_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-04-14T11:00:00Z",
    "updated_at": "2024-04-14T12:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |

---

### 2.4 사용자 정보 수정
**FR-02-11: 사용자 정보 수정**

#### API 기본 정보
- **Method:** `PUT`
- **Endpoint:** `/users/{user_id}`
- **Description:** 사용자의 이름, 이메일, 권한을 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 사용자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `requested_by_name` | `string` | 선택 | 2~50자 | 사용자 이름 |
| `requested_by_email` | `string` | 선택 | 이메일 형식 | 사용자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 전화번호 |
| `department` | `string` | 선택 | 최대 100자 | 소속 부서 |
| `role_type` | `string` | 선택 | VIEWER, EDITOR, ADMIN | 권한 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자 정보가 수정되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "requested_by_name": "김철수",
    "requested_by_email": "newemail@example.com",
    "phone": "010-9999-8888",
    "department": "채용팀",
    "role_type": "ADMIN",
    "updated_at": "2024-04-14T13:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |
| **400** | `DUPLICATE_EMAIL` | "이미 사용 중인 이메일입니다." | 중복된 이메일로 수정 시 |

---

### 2.5 사용자 상태 변경
**FR-02-12: 사용자 상태 관리**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/status`
- **Description:** 사용자의 상태를 ACTIVE 또는 INACTIVE로 변경합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 사용자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `status` | `string` | **필수** | ACTIVE, INACTIVE | 변경할 상태 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자 상태가 변경되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "INACTIVE",
    "updated_at": "2024-04-14T13:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태값입니다." | ACTIVE, INACTIVE 이외의 값일 때 |

#### 데이터 제약 조건 (Validation)
1. **INACTIVE 상태**: 시스템 로그인 불가

---

### 2.6 사용자 삭제
**FR-02-13: 사용자 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/users/{user_id}`
- **Description:** 사용자를 논리 삭제 처리합니다. (deleted_at, deleted_by 기록)

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 사용자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자가 삭제되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "deleted_at": "2024-04-14T14:00:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리적 삭제 대신 deleted_at, deleted_by 기록
2. **deleted_by**: 요청한 관리자 ID 자동 저장

---

## 3. 지원자 관리

### 3.1 지원자 등록
**FR-03-01: 지원자 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/candidates`
- **Description:** 지원자의 기본 정보를 등록합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `name` | `string` | **필수** | 2~50자 | 지원자 이름 |
| `email` | `string` | **필수** | 이메일 형식 | 지원자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 지원자 전화번호 |
| `birth_date` | `string` | 선택 | YYYY-MM-DD | 생년월일 |
| `position_applied` | `string` | 선택 | 최대 100자 | 지원 직무 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "지원자가 등록되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "이영희",
    "email": "candidate@example.com",
    "phone": "010-1111-2222",
    "birth_date": "1995-03-15",
    "position_applied": "백엔드 개발자",
    "apply_status": "APPLIED",
    "resume_doc_id": null,
    "portfolio_doc_id": null,
    "created_at": "2024-04-14T15:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_EMAIL` | "이미 등록된 이메일입니다." | 중복된 이메일로 등록 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |
| **400** | `INVALID_DATE` | "유효하지 않은 날짜 형식입니다." | birth_date 형식 오류 시 |

#### 데이터 제약 조건 (Validation)
1. **apply_status**: 자동으로 APPLIED로 설정
2. **email**: 중복 불가 권장

---

### 3.2 지원자 목록 조회
**FR-03-02: 지원자 목록 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/candidates`
- **Description:** 지원자 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |
| `apply_status` | `string` | 선택 | - | 지원 상태 필터 |
| `search` | `string` | 선택 | - | 이름, 이메일 검색 |
| `position_applied` | `string` | 선택 | - | 지원 직무 필터 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "이영희",
        "email": "candidate@example.com",
        "phone": "010-1111-2222",
        "position_applied": "백엔드 개발자",
        "apply_status": "APPLIED",
        "created_at": "2024-04-14T15:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 50,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 3.3 지원자 상세 조회
**FR-03-03: 지원자 상세 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/candidates/{candidate_id}`
- **Description:** 지원자의 상세 정보와 연결된 대표 문서 정보를 함께 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 지원자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "이영희",
    "email": "candidate@example.com",
    "phone": "010-1111-2222",
    "birth_date": "1995-03-15",
    "position_applied": "백엔드 개발자",
    "apply_status": "APPLIED",
    "resume_doc_id": "880e8400-e29b-41d4-a716-446655440003",
    "portfolio_doc_id": "990e8400-e29b-41d4-a716-446655440004",
    "documents": [
      {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "document_type": "RESUME",
        "title": "이영희_이력서.pdf",
        "extract_status": "READY"
      },
      {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "document_type": "PORTFOLIO",
        "title": "이영희_포트폴리오.pdf",
        "extract_status": "READY"
      }
    ],
    "created_at": "2024-04-14T15:00:00Z",
    "updated_at": "2024-04-14T15:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

---

### 3.4 지원자 정보 수정
**FR-03-06: 지원자 수정**

#### API 기본 정보
- **Method:** `PUT`
- **Endpoint:** `/candidates/{candidate_id}`
- **Description:** 지원자의 기본 정보 및 상태를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `name` | `string` | 선택 | 2~50자 | 지원자 이름 |
| `email` | `string` | 선택 | 이메일 형식 | 지원자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 지원자 전화번호 |
| `position_applied` | `string` | 선택 | 최대 100자 | 지원 직무 |
| `apply_status` | `string` | 선택 | 지원 상태값 | 지원 상태 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원자 정보가 수정되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "이영희",
    "email": "newemail@example.com",
    "phone": "010-3333-4444",
    "position_applied": "풀스택 개발자",
    "apply_status": "INTERVIEW_SCHEDULED",
    "updated_at": "2024-04-14T16:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

---

### 3.5 지원 상태 변경
**FR-03-04: 지원 상태 관리**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/candidates/{candidate_id}/status`
- **Description:** 지원자의 지원 상태를 변경합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `apply_status` | `string` | **필수** | APPLIED, DOCUMENT_REVIEW, INTERVIEW_SCHEDULED, INTERVIEW_COMPLETED, ACCEPTED, REJECTED | 변경할 상태 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원 상태가 변경되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "apply_status": "DOCUMENT_REVIEW",
    "updated_at": "2024-04-14T16:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태값입니다." | 정의되지 않은 상태값일 때 |

#### 데이터 제약 조건 (Validation)
1. **apply_status 가능한 값**: APPLIED, DOCUMENT_REVIEW, INTERVIEW_SCHEDULED, INTERVIEW_COMPLETED, ACCEPTED, REJECTED

---

### 3.6 대표 문서 연결
**FR-03-05: 대표 문서 연결**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/candidates/{candidate_id}/documents`
- **Description:** 지원자의 대표 이력서 및 포트폴리오 문서를 연결합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `resume_doc_id` | `string` | 선택 | UUID | 대표 이력서 문서 ID |
| `portfolio_doc_id` | `string` | 선택 | UUID | 대표 포트폴리오 문서 ID |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "대표 문서가 연결되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "resume_doc_id": "880e8400-e29b-41d4-a716-446655440003",
    "portfolio_doc_id": "990e8400-e29b-41d4-a716-446655440004",
    "updated_at": "2024-04-14T17:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |

#### 데이터 제약 조건 (Validation)
1. **document_id**: 해당 candidate_id와 연결된 문서만 설정 가능
2. **document_type**: RESUME, PORTFOLIO 타입 확인 필요

---

### 3.7 지원자 삭제
**FR-03-07: 지원자 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/candidates/{candidate_id}`
- **Description:** 지원자를 논리 삭제 처리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 지원자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원자가 삭제되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "deleted_at": "2024-04-14T17:30:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: deleted_at, deleted_by 기록

---

## 4. 문서 관리

### 4.1 문서 업로드
**FR-04-01: 문서 업로드**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/documents`
- **Description:** 지원자별 이력서 및 포트폴리오 파일을 업로드합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `multipart/form-data` | 파일 업로드 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Form Data
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `candidate_id` | `string` | **필수** | UUID | 지원자 ID |
| `document_type` | `string` | **필수** | RESUME, PORTFOLIO | 문서 타입 |
| `title` | `string` | **필수** | 최대 200자 | 문서 제목 |
| `file` | `file` | **필수** | PDF, DOCX, 최대 10MB | 업로드할 파일 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "문서가 업로드되었습니다.",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "document_type": "RESUME",
    "title": "이영희_이력서.pdf",
    "file_path": "/uploads/2024/04/14/880e8400-resume.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "extract_status": "PENDING",
    "created_at": "2024-04-14T18:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `FILE_TOO_LARGE` | "파일 크기는 10MB를 초과할 수 없습니다." | 파일 크기 초과 시 |
| **400** | `INVALID_FILE_TYPE` | "지원하지 않는 파일 형식입니다." | PDF, DOCX 외 형식일 때 |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **file_size**: 최대 10MB
2. **mime_type**: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document
3. **extract_status**: 자동으로 PENDING 설정 (백그라운드 텍스트 추출 시작)

---

### 4.2 문서 목록 조회
**FR-04-03: 문서 목록 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/documents`
- **Description:** 지원자별 또는 문서 타입별 문서 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `candidate_id` | `string` | 선택 | - | 지원자 ID 필터 |
| `document_type` | `string` | 선택 | - | RESUME, PORTFOLIO |
| `extract_status` | `string` | 선택 | - | PENDING, READY, FAILED |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
        "candidate_name": "이영희",
        "document_type": "RESUME",
        "title": "이영희_이력서.pdf",
        "file_size": 1024000,
        "extract_status": "READY",
        "created_at": "2024-04-14T18:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_items": 30,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 4.3 문서 상세 조회
**FR-04-04: 문서 상세 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/documents/{document_id}`
- **Description:** 문서의 상세 정보를 조회합니다. (제목, 파일 경로, 추출 텍스트, 추출 상태 포함)

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "candidate_name": "이영희",
    "document_type": "RESUME",
    "title": "이영희_이력서.pdf",
    "file_path": "/uploads/2024/04/14/880e8400-resume.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "extract_status": "READY",
    "extracted_text": "경력\n- ABC 회사 (2020-2023)\n  백엔드 개발자...",
    "extract_error": null,
    "created_at": "2024-04-14T18:00:00Z",
    "updated_at": "2024-04-14T18:05:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

---

### 4.4 문서 다운로드
**FR-04-04: 문서 다운로드**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/documents/{document_id}/download`
- **Description:** 원본 문서 파일을 다운로드합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition**: `attachment; filename="이영희_이력서.pdf"`

```
[Binary File Data]
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |
| **404** | `FILE_NOT_FOUND` | "파일을 찾을 수 없습니다." | 파일이 서버에 존재하지 않을 때 |

---

### 4.5 텍스트 추출 상태 조회
**FR-04-05: 텍스트 추출 상태 관리**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/documents/{document_id}/extract-status`
- **Description:** 문서의 텍스트 추출 상태를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "extract_status": "READY",
    "extracted_at": "2024-04-14T18:05:00Z",
    "extract_error": null
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **extract_status**: PENDING (대기 중), READY (완료), FAILED (실패)

---

### 4.6 텍스트 추출 재시도
**FR-04-06: 추출 텍스트 저장**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/documents/{document_id}/extract`
- **Description:** 텍스트 추출을 재시도합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "텍스트 추출이 시작되었습니다.",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "extract_status": "PENDING"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |
| **400** | `EXTRACTION_IN_PROGRESS` | "이미 추출이 진행 중입니다." | extract_status가 PENDING일 때 |

---

### 4.7 문서 삭제
**FR-04-07: 문서 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/documents/{document_id}`
- **Description:** 문서를 논리 삭제 처리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "문서가 삭제되었습니다.",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "deleted_at": "2024-04-14T19:00:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: deleted_at, deleted_by 기록

---

## 5. 프롬프트 관리

### 5.1 프롬프트 프로파일 등록
**FR-05-01: 프롬프트 프로파일 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/prompt-profiles`
- **Description:** LLM 분석 전략 프로파일을 생성합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `profile_key` | `string` | **필수** | 최대 100자, 영문+숫자+언더스코어 | 프로파일 고유 키 |
| `profile_name` | `string` | **필수** | 최대 200자 | 프로파일 이름 |
| `strategy_type` | `string` | **필수** | - | 분석 전략 유형 |
| `system_prompt` | `string` | **필수** | - | 시스템 프롬프트 |
| `user_prompt_template` | `string` | **필수** | - | 사용자 프롬프트 템플릿 |
| `output_schema` | `object` | 선택 | JSON Schema | LLM 응답 형식 스키마 |
| `is_active` | `boolean` | 선택 | - | 활성화 여부 (기본값: true) |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 등록되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "profile_key": "interview_question_generator_v1",
    "profile_name": "면접 질문 생성기 v1",
    "strategy_type": "INTERVIEW_QUESTION",
    "is_active": true,
    "created_at": "2024-04-14T19:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_PROFILE_KEY` | "이미 사용 중인 프로파일 키입니다." | 중복된 profile_key로 등록 시 |
| **400** | `INVALID_SCHEMA` | "유효하지 않은 JSON 스키마입니다." | output_schema 형식 오류 시 |

#### 데이터 제약 조건 (Validation)
1. **profile_key**: 시스템 내 중복 불가 (Unique Constraint)
2. **is_active**: 기본값 true

---

### 5.2 프롬프트 프로파일 목록 조회
**FR-05-05: 프롬프트 프로파일 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/prompt-profiles`
- **Description:** 등록된 프롬프트 프로파일 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `strategy_type` | `string` | 선택 | - | 전략 유형 필터 |
| `is_active` | `boolean` | 선택 | - | 활성 여부 필터 |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440005",
        "profile_key": "interview_question_generator_v1",
        "profile_name": "면접 질문 생성기 v1",
        "strategy_type": "INTERVIEW_QUESTION",
        "is_active": true,
        "created_at": "2024-04-14T19:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 5,
      "items_per_page": 20,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 5.3 프롬프트 프로파일 상세 조회
**FR-05-05: 프롬프트 프로파일 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/prompt-profiles/{profile_id}`
- **Description:** 프롬프트 프로파일의 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 프로파일 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "profile_key": "interview_question_generator_v1",
    "profile_name": "면접 질문 생성기 v1",
    "strategy_type": "INTERVIEW_QUESTION",
    "system_prompt": "당신은 전문 면접관입니다...",
    "user_prompt_template": "다음 이력서를 분석하여...",
    "output_schema": {
      "type": "object",
      "properties": {}
    },
    "is_active": true,
    "created_at": "2024-04-14T19:30:00Z",
    "updated_at": "2024-04-14T19:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 profile_id일 때 |

---

### 5.4 프롬프트 프로파일 수정
**FR-05-06: 프롬프트 프로파일 수정**

#### API 기본 정보
- **Method:** `PUT`
- **Endpoint:** `/prompt-profiles/{profile_id}`
- **Description:** 프롬프트 프로파일의 전략 유형, 출력 스키마, 활성 여부를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 프로파일 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `profile_name` | `string` | 선택 | 최대 200자 | 프로파일 이름 |
| `system_prompt` | `string` | 선택 | - | 시스템 프롬프트 |
| `user_prompt_template` | `string` | 선택 | - | 사용자 프롬프트 템플릿 |
| `output_schema` | `object` | 선택 | JSON Schema | LLM 응답 형식 스키마 |
| `is_active` | `boolean` | 선택 | - | 활성화 여부 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 수정되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "profile_name": "면접 질문 생성기 v1.1",
    "updated_at": "2024-04-14T20:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 profile_id일 때 |

---

### 5.5 프롬프트 프로파일 활성화 제어
**FR-05-04: 프로파일 활성화 제어**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/prompt-profiles/{profile_id}/status`
- **Description:** 프로파일의 활성화 여부를 제어합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 프로파일 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `is_active` | `boolean` | **필수** | - | 활성화 여부 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "프로파일 상태가 변경되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "is_active": false,
    "updated_at": "2024-04-14T20:30:00Z"
  }
}
```

---

### 5.6 프롬프트 프로파일 삭제
**FR-05-07: 프롬프트 프로파일 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/prompt-profiles/{profile_id}`
- **Description:** 프롬프트 프로파일을 논리 삭제 처리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 프로파일 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 삭제되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "deleted_at": "2024-04-14T21:00:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 profile_id일 때 |

---

## 6. 면접 질문 관리

### 6.1 면접 질문 생성 실행
**FR-06-01: 질문 저장**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/interview-questions/generate`
- **Description:** LLM을 이용하여 면접 질문을 생성하고 저장합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `candidate_id` | `string` | **필수** | UUID | 지원자 ID |
| `profile_id` | `string` | **필수** | UUID | 프롬프트 프로파일 ID |
| `question_count` | `integer` | 선택 | 1~20 | 생성할 질문 개수 (기본값: 10) |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "면접 질문 생성이 시작되었습니다.",
  "data": {
    "workflow_run_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "status": "PROCESSING",
    "created_at": "2024-04-14T21:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 profile_id일 때 |
| **400** | `NO_DOCUMENT_FOUND` | "지원자의 문서가 없습니다." | 추출된 문서가 없을 때 |

#### 데이터 제약 조건 (Validation)
1. **question_count**: 1~20 범위
2. **비동기 처리**: 결과는 workflow_run_id로 추적

---

### 6.2 면접 질문 목록 조회
**FR-06-05: 질문 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/interview-questions`
- **Description:** 생성된 면접 질문 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `candidate_id` | `string` | 선택 | - | 지원자 ID 필터 |
| `workflow_run_id` | `string` | 선택 | - | 실행 ID 필터 |
| `category` | `string` | 선택 | - | 질문 카테고리 필터 |
| `difficulty_level` | `string` | 선택 | - | EASY, MEDIUM, HARD |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "cc0e8400-e29b-41d4-a716-446655440007",
        "workflow_run_id": "bb0e8400-e29b-41d4-a716-446655440006",
        "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
        "category": "TECHNICAL",
        "question_text": "Spring Boot에서 트랜잭션 관리는 어떻게 수행하나요?",
        "expected_answer": "@Transactional 어노테이션을 사용하여...",
        "difficulty_level": "MEDIUM",
        "created_at": "2024-04-14T21:35:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 10,
      "items_per_page": 20,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 6.3 면접 질문 상세 조회
**FR-06-05: 질문 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 면접 질문의 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 질문 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "workflow_run_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "candidate_name": "이영희",
    "category": "TECHNICAL",
    "question_text": "Spring Boot에서 트랜잭션 관리는 어떻게 수행하나요?",
    "expected_answer": "@Transactional 어노테이션을 사용하여 선언적 트랜잭션 관리를 수행할 수 있습니다...",
    "difficulty_level": "MEDIUM",
    "created_at": "2024-04-14T21:35:00Z",
    "updated_at": "2024-04-14T21:35:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "질문을 찾을 수 없습니다." | 존재하지 않는 question_id일 때 |

---

### 6.4 면접 질문 수정
**FR-06-06: 질문 수정**

#### API 기본 정보
- **Method:** `PUT`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 면접 질문의 내용, 기대 답변, 난이도를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 질문 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `category` | `string` | 선택 | - | 질문 카테고리 |
| `question_text` | `string` | 선택 | 최대 1000자 | 질문 내용 |
| `expected_answer` | `string` | 선택 | 최대 2000자 | 기대 답변 |
| `difficulty_level` | `string` | 선택 | EASY, MEDIUM, HARD | 난이도 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "면접 질문이 수정되었습니다.",
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "question_text": "Spring Boot에서 트랜잭션 전파 속성에 대해 설명하세요.",
    "difficulty_level": "HARD",
    "updated_at": "2024-04-14T22:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "질문을 찾을 수 없습니다." | 존재하지 않는 question_id일 때 |

---

### 6.5 면접 질문 삭제
**FR-06-07: 질문 삭제**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 불필요한 면접 질문을 삭제합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 질문 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "면접 질문이 삭제되었습니다.",
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "deleted_at": "2024-04-14T22:30:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "질문을 찾을 수 없습니다." | 존재하지 않는 question_id일 때 |

---

### 6.6 Workflow 실행 상태 조회

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/workflow-runs/{workflow_run_id}`
- **Description:** 면접 질문 생성 워크플로우의 실행 상태를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `workflow_run_id` | `string` | **필수** | 워크플로우 실행 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "run_status": "COMPLETED",
    "started_at": "2024-04-14T21:30:00Z",
    "completed_at": "2024-04-14T21:35:00Z",
    "question_count": 10,
    "total_cost": 0.025
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `WORKFLOW_NOT_FOUND` | "워크플로우를 찾을 수 없습니다." | 존재하지 않는 workflow_run_id일 때 |

---

## 7. LLM 로그 관리

### 7.1 LLM 호출 로그 조회
**FR-07-07: 로그 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/llm-logs`
- **Description:** LLM 호출 로그를 기간별, 상태별, 모델별로 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `workflow_run_id` | `string` | 선택 | - | 워크플로우 실행 ID 필터 |
| `call_status` | `string` | 선택 | - | SUCCESS, FAIL |
| `model_name` | `string` | 선택 | - | 모델명 필터 |
| `start_date` | `string` | 선택 | - | 시작 날짜 (YYYY-MM-DD) |
| `end_date` | `string` | 선택 | - | 종료 날짜 (YYYY-MM-DD) |
| `page` | `integer` | 선택 | `1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | 페이지당 항목 수 (최대 100) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "dd0e8400-e29b-41d4-a716-446655440008",
        "workflow_run_id": "bb0e8400-e29b-41d4-a716-446655440006",
        "model_name": "gpt-4",
        "total_tokens": 2500,
        "cost_amount": 0.025,
        "call_status": "SUCCESS",
        "created_at": "2024-04-14T21:32:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 3,
      "items_per_page": 20,
      "has_next": false,
      "has_prev": false
    },
    "summary": {
      "total_calls": 3,
      "success_count": 3,
      "fail_count": 0,
      "total_tokens": 7500,
      "total_cost": 0.075
    }
  }
}
```

---

### 7.2 LLM 호출 로그 상세 조회
**FR-07-01 ~ FR-07-06: LLM 호출 관련 정보**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/llm-logs/{log_id}`
- **Description:** LLM 호출 로그의 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `log_id` | `string` | **필수** | 로그 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "dd0e8400-e29b-41d4-a716-446655440008",
    "workflow_run_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "model_name": "gpt-4",
    "prompt_text": "당신은 전문 면접관입니다...",
    "response_json": {
      "questions": [
        {
          "category": "TECHNICAL",
          "question_text": "...",
          "expected_answer": "...",
          "difficulty_level": "MEDIUM"
        }
      ]
    },
    "total_tokens": 2500,
    "cost_amount": 0.025,
    "call_status": "SUCCESS",
    "error_message": null,
    "created_at": "2024-04-14T21:32:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `LOG_NOT_FOUND` | "로그를 찾을 수 없습니다." | 존재하지 않는 log_id일 때 |

---

### 7.3 LLM 사용 통계 조회

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/llm-logs/statistics`
- **Description:** LLM 사용 통계를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `start_date` | `string` | **필수** | - | 시작 날짜 (YYYY-MM-DD) |
| `end_date` | `string` | **필수** | - | 종료 날짜 (YYYY-MM-DD) |
| `group_by` | `string` | 선택 | `model` | model, date, status |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-04-01",
      "end_date": "2024-04-30"
    },
    "statistics": [
      {
        "model_name": "gpt-4",
        "total_calls": 150,
        "success_count": 148,
        "fail_count": 2,
        "total_tokens": 375000,
        "total_cost": 3.75,
        "average_tokens_per_call": 2500
      },
      {
        "model_name": "gpt-3.5-turbo",
        "total_calls": 300,
        "success_count": 295,
        "fail_count": 5,
        "total_tokens": 450000,
        "total_cost": 0.90,
        "average_tokens_per_call": 1500
      }
    ],
    "total_summary": {
      "total_calls": 450,
      "success_count": 443,
      "fail_count": 7,
      "total_tokens": 825000,
      "total_cost": 4.65,
      "success_rate": 0.984
    }
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_DATE_RANGE` | "유효하지 않은 날짜 범위입니다." | start_date > end_date일 때 |

---

## 부록

### 상태 코드 정의

#### 관리자 상태 (`manager.status`)
- `ACTIVE`: 활성
- `INACTIVE`: 비활성
- `LOCK`: 잠금

#### 사용자 요청 상태 (`user.request_status`)
- `REQUESTED`: 요청됨
- `APPROVED`: 승인됨
- `REJECTED`: 반려됨

#### 사용자 상태 (`user.status`)
- `ACTIVE`: 활성
- `INACTIVE`: 비활성

#### 사용자 권한 (`user.role_type`)
- `VIEWER`: 조회 권한
- `EDITOR`: 편집 권한
- `ADMIN`: 관리자 권한

#### 지원 상태 (`candidate.apply_status`)
- `APPLIED`: 지원 완료
- `DOCUMENT_REVIEW`: 서류 검토 중
- `INTERVIEW_SCHEDULED`: 면접 예정
- `INTERVIEW_COMPLETED`: 면접 완료
- `ACCEPTED`: 합격
- `REJECTED`: 불합격

#### 문서 타입 (`document.document_type`)
- `RESUME`: 이력서
- `PORTFOLIO`: 포트폴리오

#### 추출 상태 (`document.extract_status`)
- `PENDING`: 추출 대기 중
- `READY`: 추출 완료
- `FAILED`: 추출 실패

#### 난이도 (`interview_question_item.difficulty_level`)
- `EASY`: 쉬움
- `MEDIUM`: 보통
- `HARD`: 어려움

#### LLM 호출 상태 (`llm_call_log.call_status`)
- `SUCCESS`: 성공
- `FAIL`: 실패

---

**최종 수정일**: 2024-04-14