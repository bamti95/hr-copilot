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
- **Description:** login_id와 password로 관리자 인증을 수행하고 JWT 토큰을 발급합니다. 계정 상태를 확인합니다.

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

#### 데이터 제약 조건 (Validation)
1. **last_login_at**: 로그인 성공 시 자동 갱신 (FR-01-03)
2. **status**: ACTIVE 상태만 로그인 가능

---

### 1.3 사용자 계정 요청 승인
**FR-01-04: 사용자 계정 요청 승인**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/approve`
- **Description:** request_status가 REQUESTED인 사용자 계정 요청을 검토 후 승인 처리합니다.

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
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
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
3. **role_type**: 설정 필수 (FR-01-05)
4. **created_by**: 계정을 생성한 관리자 ID 저장 (FR-01-05)
5. **approved_by**: 요청한 관리자 ID 자동 저장 (FR-01-06)

---

### 1.4 사용자 계정 요청 반려
**FR-01-04: 사용자 계정 요청 승인 (반려)**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/reject`
- **Description:** request_status가 REQUESTED인 사용자 계정 요청을 반려 처리합니다.

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
| `rejection_note` | `string` | 선택 | 최대 500자 | 반려 사유 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자 계정 요청이 반려되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "김철수",
    "email": "user@example.com",
    "request_status": "REJECTED",
    "rejected_at": "2024-04-14T12:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_STATUS` | "반려 가능한 상태가 아닙니다." | request_status가 REQUESTED가 아닐 때 |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **request_status**: REQUESTED → REJECTED로 변경

---

## 2. 서비스 사용자 관리

### 2.1 사용자 계정 생성 요청 등록
**FR-02-01: 사용자 계정 생성 요청 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/users/request`
- **Description:** 요청자 정보와 요청 사유를 저장하여 계정 생성을 요청합니다.

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
| `request_note` | `string` | 선택 | 최대 500자 | 요청 사유 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "계정 생성 요청이 등록되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "requested_by_name": "김철수",
    "requested_by_email": "user@example.com",
    "request_note": "HR 업무를 위한 계정 요청드립니다.",
    "request_status": "REQUESTED",
    "created_at": "2024-04-14T11:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |
| **409** | `DUPLICATE_REQUEST` | "이미 요청한 이메일입니다." | 동일 이메일로 중복 요청 시 |

#### 데이터 제약 조건 (Validation)
1. **request_status**: REQUESTED 상태로 저장 (FR-02-02)
2. **requested_by_email**: 이메일 형식 검증 필요

---

### 2.2 사용자 목록 조회
**FR-02-09: 사용자 목록 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/users`
- **Description:** 전체 사용자 목록을 조회합니다. request_status 포함.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |
| `request_status` | `string` | 선택 | 필터: REQUESTED, APPROVED, REJECTED |
| `status` | `string` | 선택 | 필터: ACTIVE, INACTIVE |

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
        "request_status": "APPROVED",
        "status": "ACTIVE",
        "role_type": "EDITOR",
        "approved_by": "550e8400-e29b-41d4-a716-446655440000",
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
| `user_id` | `string` | **필수** | 조회할 사용자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "requested_by_name": "김철수",
    "requested_by_email": "user@example.com",
    "request_note": "HR 업무를 위한 계정 요청드립니다.",
    "request_status": "APPROVED",
    "status": "ACTIVE",
    "role_type": "EDITOR",
    "approved_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-04-14T11:00:00Z",
    "approved_at": "2024-04-14T12:00:00Z"
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
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}`
- **Description:** 이름, 이메일, 권한(role_type)을 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 수정할 사용자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `requested_by_name` | `string` | 선택 | 2~50자 | 사용자 이름 |
| `requested_by_email` | `string` | 선택 | 이메일 형식 | 사용자 이메일 |
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
    "requested_by_email": "updated@example.com",
    "role_type": "ADMIN",
    "updated_at": "2024-04-14T13:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

---

### 2.5 사용자 상태 관리
**FR-02-12: 사용자 상태 관리**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/users/{user_id}/status`
- **Description:** 사용자의 status를 ACTIVE / INACTIVE로 변경합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 상태 변경할 사용자 ID (UUID) |

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
    "updated_at": "2024-04-14T14:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태 값입니다." | status 값이 ACTIVE/INACTIVE가 아닐 때 |

#### 데이터 제약 조건 (Validation)
1. **INACTIVE 상태**: 사용자는 로그인 불가 처리 (FR-02-14)

---

### 2.6 사용자 삭제
**FR-02-13: 사용자 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/users/{user_id}`
- **Description:** 사용자를 논리 삭제 처리합니다. deleted_at, deleted_by를 기록합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 관리자 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `user_id` | `string` | **필수** | 삭제할 사용자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "사용자가 삭제되었습니다.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "deleted_at": "2024-04-14T15:00:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `USER_NOT_FOUND` | "사용자를 찾을 수 없습니다." | 존재하지 않는 user_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리 삭제 대신 deleted_at, deleted_by 기록 (FR-08-02)

---

## 3. 지원자 관리

### 3.1 지원자 등록
**FR-03-01: 지원자 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/candidates`
- **Description:** 이름, 이메일, 전화번호, 생년월일 등 지원자 기본 정보를 등록합니다.

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
| `apply_status` | `string` | 선택 | 상태값 | 지원 상태 (기본값: APPLIED) |

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
    "phone": "010-9876-5432",
    "birth_date": "1995-05-20",
    "apply_status": "APPLIED",
    "created_at": "2024-04-14T16:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |
| **409** | `DUPLICATE_CANDIDATE` | "이미 등록된 지원자입니다." | 동일 이메일로 중복 등록 시 |

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
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |
| `apply_status` | `string` | 선택 | 필터: 지원 상태 |

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
        "phone": "010-9876-5432",
        "apply_status": "APPLIED",
        "created_at": "2024-04-14T16:00:00Z"
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
- **Description:** 지원자 기본 정보와 연결된 대표 문서 정보를 함께 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 조회할 지원자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "이영희",
    "email": "candidate@example.com",
    "phone": "010-9876-5432",
    "birth_date": "1995-05-20",
    "apply_status": "APPLIED",
    "resume_doc_id": "880e8400-e29b-41d4-a716-446655440003",
    "portfolio_doc_id": "990e8400-e29b-41d4-a716-446655440004",
    "resume_document": {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "title": "이영희_이력서.pdf",
      "document_type": "RESUME",
      "extract_status": "READY"
    },
    "portfolio_document": {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "title": "이영희_포트폴리오.pdf",
      "document_type": "PORTFOLIO",
      "extract_status": "READY"
    },
    "created_at": "2024-04-14T16:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

---

### 3.4 지원자 수정
**FR-03-06: 지원자 수정**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/candidates/{candidate_id}`
- **Description:** 지원자 기본 정보 및 상태를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 수정할 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `name` | `string` | 선택 | 2~50자 | 지원자 이름 |
| `email` | `string` | 선택 | 이메일 형식 | 지원자 이메일 |
| `phone` | `string` | 선택 | 전화번호 형식 | 지원자 전화번호 |
| `birth_date` | `string` | 선택 | YYYY-MM-DD | 생년월일 |
| `apply_status` | `string` | 선택 | 상태값 | 지원 상태 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원자 정보가 수정되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "이영희",
    "email": "updated@example.com",
    "apply_status": "INTERVIEWING",
    "updated_at": "2024-04-14T17:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

---

### 3.5 지원 상태 관리
**FR-03-04: 지원 상태 관리**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/candidates/{candidate_id}/status`
- **Description:** apply_status 값을 기준으로 지원 진행 상태를 관리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 상태 변경할 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `apply_status` | `string` | **필수** | 상태값 | 변경할 지원 상태 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원 상태가 변경되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "apply_status": "PASSED",
    "updated_at": "2024-04-14T18:00:00Z"
  }
}
```

---

### 3.6 대표 문서 연결
**FR-03-05: 대표 문서 연결**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/candidates/{candidate_id}/documents`
- **Description:** resume_doc_id, portfolio_doc_id를 통해 대표 문서를 연결합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 문서 연결할 지원자 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `resume_doc_id` | `string` | 선택 | 이력서 문서 ID (UUID) |
| `portfolio_doc_id` | `string` | 선택 | 포트폴리오 문서 ID (UUID) |

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
    "updated_at": "2024-04-14T19:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

---

### 3.7 지원자 삭제
**FR-03-07: 지원자 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/candidates/{candidate_id}`
- **Description:** 지원자를 논리 삭제 처리합니다. Audit 컬럼 기반.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | **필수** | 삭제할 지원자 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "지원자가 삭제되었습니다.",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "deleted_at": "2024-04-14T20:00:00Z",
    "deleted_by": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리 삭제 대신 deleted_at, deleted_by 기록 (FR-08-02)

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

##### B. Request Body (Form Data)
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `candidate_id` | `string` | **필수** | UUID | 지원자 ID |
| `document_type` | `string` | **필수** | RESUME, PORTFOLIO | 문서 타입 |
| `title` | `string` | **필수** | 최대 200자 | 문서 제목 |
| `file` | `file` | **필수** | PDF, DOCX (최대 10MB) | 업로드 파일 |

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
    "file_path": "/uploads/2024/04/14/880e8400-e29b-41d4-a716-446655440003.pdf",
    "extract_status": "PENDING",
    "created_at": "2024-04-14T21:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `INVALID_FILE_TYPE` | "지원하지 않는 파일 형식입니다." | PDF, DOCX 외 파일 업로드 시 |
| **400** | `FILE_TOO_LARGE` | "파일 크기가 10MB를 초과합니다." | 파일 크기 초과 시 |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **extract_status**: PENDING 상태로 초기화 (FR-04-05)
2. **document_type**: RESUME / PORTFOLIO 구분 (FR-04-02)

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
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | 선택 | 필터: 지원자 ID |
| `document_type` | `string` | 선택 | 필터: RESUME, PORTFOLIO |
| `extract_status` | `string` | 선택 | 필터: PENDING, READY, FAILED |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |

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
        "document_type": "RESUME",
        "title": "이영희_이력서.pdf",
        "file_path": "/uploads/2024/04/14/880e8400-e29b-41d4-a716-446655440003.pdf",
        "extract_status": "READY",
        "created_at": "2024-04-14T21:00:00Z"
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
- **Description:** 제목, 파일 경로, 추출 텍스트, 추출 상태를 포함한 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 조회할 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "document_type": "RESUME",
    "title": "이영희_이력서.pdf",
    "file_path": "/uploads/2024/04/14/880e8400-e29b-41d4-a716-446655440003.pdf",
    "extract_status": "READY",
    "extracted_text": "이름: 이영희\n이메일: candidate@example.com\n...",
    "created_at": "2024-04-14T21:00:00Z",
    "updated_at": "2024-04-14T21:05:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

---

### 4.4 추출 텍스트 저장
**FR-04-06: 추출 텍스트 저장**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/documents/{document_id}/extract`
- **Description:** 문서 파싱/OCR 결과를 extracted_text에 저장하고 extract_status를 READY로 변경합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 텍스트 저장할 문서 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `extracted_text` | `string` | **필수** | 추출된 텍스트 |
| `extract_status` | `string` | **필수** | READY, FAILED |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "텍스트 추출이 완료되었습니다.",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "extract_status": "READY",
    "extracted_text": "이름: 이영희\n이메일: candidate@example.com\n...",
    "updated_at": "2024-04-14T21:05:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **extract_status**: PENDING / READY / FAILED 상태로 관리 (FR-04-05)

---

### 4.5 문서 삭제
**FR-04-07: 문서 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/documents/{document_id}`
- **Description:** 문서를 논리 삭제 처리합니다. deleted_at / deleted_by를 활용.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `document_id` | `string` | **필수** | 삭제할 문서 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "문서가 삭제되었습니다.",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "deleted_at": "2024-04-14T22:00:00Z",
    "deleted_by": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리 삭제 대신 deleted_at, deleted_by 기록 (FR-08-02)

---

## 5. 프롬프트 관리

### 5.1 프롬프트 프로파일 등록
**FR-05-01: 프롬프트 프로파일 등록**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/prompt-profiles`
- **Description:** profile_key 기반의 분석 전략 프로파일을 생성합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `profile_key` | `string` | **필수** | 고유값 | 프로파일 식별 키 |
| `strategy_type` | `string` | **필수** | 분석 전략 타입 | 분석 전략 유형 |
| `output_schema` | `object` | 선택 | JSON Schema | LLM 응답 형식 정의 |
| `is_active` | `boolean` | 선택 | 기본값: true | 활성화 여부 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 등록되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "profile_key": "technical_interview_v1",
    "strategy_type": "TECHNICAL_DEPTH",
    "output_schema": {
      "type": "object",
      "properties": {
        "questions": {
          "type": "array"
        }
      }
    },
    "is_active": true,
    "created_at": "2024-04-14T23:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **409** | `DUPLICATE_PROFILE_KEY` | "이미 존재하는 프로파일 키입니다." | 중복된 profile_key 등록 시 |

#### 데이터 제약 조건 (Validation)
1. **profile_key**: 시스템 내 중복 불가
2. **strategy_type**: 분석 전략 구분 (FR-05-02)
3. **output_schema**: LLM 응답 형식 정의 (FR-05-03)

---

### 5.2 프롬프트 프로파일 목록 조회
**FR-05-05: 프롬프트 프로파일 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/prompt-profiles`
- **Description:** 등록된 프로파일 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `is_active` | `boolean` | 선택 | 필터: 활성화 여부 |
| `strategy_type` | `string` | 선택 | 필터: 전략 유형 |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440005",
        "profile_key": "technical_interview_v1",
        "strategy_type": "TECHNICAL_DEPTH",
        "is_active": true,
        "created_at": "2024-04-14T23:00:00Z"
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
- **Description:** 프로파일 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 조회할 프로파일 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "profile_key": "technical_interview_v1",
    "strategy_type": "TECHNICAL_DEPTH",
    "output_schema": {
      "type": "object",
      "properties": {
        "questions": {
          "type": "array"
        }
      }
    },
    "is_active": true,
    "created_at": "2024-04-14T23:00:00Z"
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
- **Method:** `PATCH`
- **Endpoint:** `/prompt-profiles/{profile_id}`
- **Description:** 전략 유형, 출력 스키마, 활성 여부를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 수정할 프로파일 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `strategy_type` | `string` | 선택 | 분석 전략 유형 |
| `output_schema` | `object` | 선택 | LLM 응답 형식 정의 |
| `is_active` | `boolean` | 선택 | 활성화 여부 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 수정되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "strategy_type": "BEHAVIORAL",
    "is_active": false,
    "updated_at": "2024-04-15T00:00:00Z"
  }
}
```

#### 데이터 제약 조건 (Validation)
1. **is_active**: 사용 가능 여부 제어 (FR-05-04)

---

### 5.5 프롬프트 프로파일 삭제
**FR-05-07: 프롬프트 프로파일 삭제 처리**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/prompt-profiles/{profile_id}`
- **Description:** 프로파일을 논리 삭제 처리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `profile_id` | `string` | **필수** | 삭제할 프로파일 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "프롬프트 프로파일이 삭제되었습니다.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "deleted_at": "2024-04-15T01:00:00Z",
    "deleted_by": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리 삭제 대신 deleted_at, deleted_by 기록 (FR-08-02)

---

## 6. 면접 질문 관리

### 6.1 질문 저장
**FR-06-01: 질문 저장**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/interview-questions`
- **Description:** 생성된 면접 질문을 question_text, candidate_id, prompt_profile_id, source_document_id 기준으로 저장합니다.

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
| `prompt_profile_id` | `string` | **필수** | UUID | 프롬프트 프로파일 ID |
| `source_document_id` | `string` | **필수** | UUID | 출처 문서 ID |
| `question_text` | `string` | **필수** | 최대 1000자 | 면접 질문 내용 |
| `category` | `string` | 선택 | 질문 유형 | 질문 카테고리 |
| `expected_answer` | `string` | 선택 | 최대 2000자 | 기대 답변 |
| `difficulty_level` | `string` | 선택 | EASY, MEDIUM, HARD | 난이도 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "면접 질문이 저장되었습니다.",
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "source_document_id": "880e8400-e29b-41d4-a716-446655440003",
    "question_text": "파이썬의 GIL에 대해 설명해주세요.",
    "category": "TECHNICAL",
    "expected_answer": "GIL(Global Interpreter Lock)은...",
    "difficulty_level": "MEDIUM",
    "created_at": "2024-04-15T02:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 prompt_profile_id일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 source_document_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **category**: 질문 유형 구분 (FR-06-02)
2. **expected_answer**: 질문별 기대 답변 저장 (FR-06-03)
3. **difficulty_level**: EASY / MEDIUM / HARD 관리 (FR-06-04)

---

### 6.2 질문 목록 조회
**FR-06-05: 질문 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/interview-questions`
- **Description:** 생성된 질문 목록을 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | 선택 | 필터: 지원자 ID |
| `prompt_profile_id` | `string` | 선택 | 필터: 프롬프트 프로파일 ID |
| `category` | `string` | 선택 | 필터: 질문 카테고리 |
| `difficulty_level` | `string` | 선택 | 필터: 난이도 |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "bb0e8400-e29b-41d4-a716-446655440006",
        "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
        "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
        "source_document_id": "880e8400-e29b-41d4-a716-446655440003",
        "question_text": "파이썬의 GIL에 대해 설명해주세요.",
        "category": "TECHNICAL",
        "difficulty_level": "MEDIUM",
        "created_at": "2024-04-15T02:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_items": 25,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 6.3 질문 상세 조회
**FR-06-05: 질문 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 질문 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 조회할 질문 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "source_document_id": "880e8400-e29b-41d4-a716-446655440003",
    "question_text": "파이썬의 GIL에 대해 설명해주세요.",
    "category": "TECHNICAL",
    "expected_answer": "GIL(Global Interpreter Lock)은 파이썬 인터프리터가 한 번에 하나의 스레드만 실행하도록 제한하는 메커니즘입니다...",
    "difficulty_level": "MEDIUM",
    "created_at": "2024-04-15T02:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "질문을 찾을 수 없습니다." | 존재하지 않는 question_id일 때 |

---

### 6.4 질문 수정
**FR-06-06: 질문 수정**

#### API 기본 정보
- **Method:** `PATCH`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 질문 내용, 기대 답변, 난이도를 수정합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Content-Type` | `string` | **필수** | `application/json` | 요청 본문의 데이터 형식 |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 수정할 질문 ID (UUID) |

##### C. Request Body
| 변수명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `question_text` | `string` | 선택 | 최대 1000자 | 면접 질문 내용 |
| `category` | `string` | 선택 | 질문 유형 | 질문 카테고리 |
| `expected_answer` | `string` | 선택 | 최대 2000자 | 기대 답변 |
| `difficulty_level` | `string` | 선택 | EASY, MEDIUM, HARD | 난이도 |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "질문이 수정되었습니다.",
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "question_text": "파이썬의 GIL과 멀티스레딩의 한계에 대해 설명해주세요.",
    "difficulty_level": "HARD",
    "updated_at": "2024-04-15T03:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `QUESTION_NOT_FOUND` | "질문을 찾을 수 없습니다." | 존재하지 않는 question_id일 때 |

---

### 6.5 질문 삭제
**FR-06-07: 질문 삭제**

#### API 기본 정보
- **Method:** `DELETE`
- **Endpoint:** `/interview-questions/{question_id}`
- **Description:** 불필요한 질문을 삭제 또는 비활성 처리합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `question_id` | `string` | **필수** | 삭제할 질문 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "message": "질문이 삭제되었습니다.",
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "deleted_at": "2024-04-15T04:00:00Z",
    "deleted_by": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

#### 데이터 제약 조건 (Validation)
1. **논리 삭제**: 물리 삭제 대신 deleted_at, deleted_by 기록 (FR-08-02)

---

## 7. LLM 로그 관리

### 7.1 LLM 호출 로그 저장
**FR-07-01: LLM 호출 로그 저장**

#### API 기본 정보
- **Method:** `POST`
- **Endpoint:** `/llm-logs`
- **Description:** LLM 호출 시 candidate_id, document_id, prompt_profile_id 기준으로 이력을 저장합니다. "지원자 + 문서 + 프롬프트 조합" 기준.

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
| `document_id` | `string` | **필수** | UUID | 문서 ID |
| `prompt_profile_id` | `string` | **필수** | UUID | 프롬프트 프로파일 ID |
| `model_name` | `string` | **필수** | 모델명 | 사용한 모델명 |
| `response_json` | `object` | **필수** | JSON | 구조화된 응답 데이터 |
| `total_tokens` | `integer` | **필수** | 양수 | 사용한 토큰 수 |
| `cost_amount` | `number` | **필수** | 양수 | 호출 비용 |
| `call_status` | `string` | **필수** | SUCCESS, FAIL | 호출 상태 |

#### Response
- **Status Code**: `201 Created`

```json
{
  "success": true,
  "message": "LLM 호출 로그가 저장되었습니다.",
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "document_id": "880e8400-e29b-41d4-a716-446655440003",
    "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "model_name": "gpt-4",
    "response_json": {
      "questions": [
        {
          "text": "파이썬의 GIL에 대해 설명해주세요.",
          "category": "TECHNICAL"
        }
      ]
    },
    "total_tokens": 1250,
    "cost_amount": 0.025,
    "call_status": "SUCCESS",
    "created_at": "2024-04-15T05:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 candidate_id일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 document_id일 때 |
| **404** | `PROFILE_NOT_FOUND` | "프로파일을 찾을 수 없습니다." | 존재하지 않는 prompt_profile_id일 때 |

#### 데이터 제약 조건 (Validation)
1. **model_name**: 사용한 모델명 기록 (FR-07-02)
2. **response_json**: 구조화된 응답 데이터 저장 (FR-07-03)
3. **total_tokens**: 사용량 분석 (FR-07-04)
4. **cost_amount**: 호출 비용 저장 (FR-07-05)
5. **call_status**: SUCCESS / FAIL 관리 (FR-07-06)

---

### 7.2 LLM 로그 목록 조회
**FR-07-07: 로그 조회**

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/llm-logs`
- **Description:** 기간별, 상태별, 모델별 호출 로그를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Query Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `candidate_id` | `string` | 선택 | 필터: 지원자 ID |
| `model_name` | `string` | 선택 | 필터: 모델명 |
| `call_status` | `string` | 선택 | 필터: SUCCESS, FAIL |
| `start_date` | `string` | 선택 | 필터: 시작일 (YYYY-MM-DD) |
| `end_date` | `string` | 선택 | 필터: 종료일 (YYYY-MM-DD) |
| `page` | `integer` | 선택 | 페이지 번호 (기본값: 1) |
| `limit` | `integer` | 선택 | 페이지당 항목 수 (기본값: 20) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "cc0e8400-e29b-41d4-a716-446655440007",
        "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
        "document_id": "880e8400-e29b-41d4-a716-446655440003",
        "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
        "model_name": "gpt-4",
        "total_tokens": 1250,
        "cost_amount": 0.025,
        "call_status": "SUCCESS",
        "created_at": "2024-04-15T05:00:00Z"
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

### 7.3 LLM 로그 상세 조회

#### API 기본 정보
- **Method:** `GET`
- **Endpoint:** `/llm-logs/{log_id}`
- **Description:** LLM 호출 로그 상세 정보를 조회합니다.

#### Request

##### A. Headers
| 필드명 | 타입 | 필수 여부 | 값/예시 | 설명 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | `string` | **필수** | `Bearer {token}` | 인증 토큰 |

##### B. Path Parameters
| 변수명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `log_id` | `string` | **필수** | 조회할 로그 ID (UUID) |

#### Response
- **Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "cc0e8400-e29b-41d4-a716-446655440007",
    "candidate_id": "770e8400-e29b-41d4-a716-446655440002",
    "document_id": "880e8400-e29b-41d4-a716-446655440003",
    "prompt_profile_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "model_name": "gpt-4",
    "response_json": {
      "questions": [
        {
          "text": "파이썬의 GIL에 대해 설명해주세요.",
          "category": "TECHNICAL",
          "difficulty": "MEDIUM"
        }
      ]
    },
    "total_tokens": 1250,
    "cost_amount": 0.025,
    "call_status": "SUCCESS",
    "created_at": "2024-04-15T05:00:00Z"
  }
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `LOG_NOT_FOUND` | "로그를 찾을 수 없습니다." | 존재하지 않는 log_id일 때 |

---

## 부록

### A. 상태값 정의

#### A.1 관리자 상태 (manager.status)
| 값 | 설명 |
| :--- | :--- |
| `ACTIVE` | 활성 상태 |
| `INACTIVE` | 비활성 상태 |

#### A.2 사용자 요청 상태 (user.request_status)
| 값 | 설명 |
| :--- | :--- |
| `REQUESTED` | 요청됨 |
| `APPROVED` | 승인됨 |
| `REJECTED` | 반려됨 |

#### A.3 사용자 상태 (user.status)
| 값 | 설명 |
| :--- | :--- |
| `ACTIVE` | 활성 상태 (로그인 가능) |
| `INACTIVE` | 비활성 상태 (로그인 불가) |

#### A.4 지원 상태 (candidate.apply_status)
| 값 | 설명 |
| :--- | :--- |
| `APPLIED` | 지원 완료 |
| `SCREENING` | 서류 심사 중 |
| `INTERVIEWING` | 면접 진행 중 |
| `PASSED` | 합격 |
| `FAILED` | 불합격 |

#### A.5 문서 타입 (document.document_type)
| 값 | 설명 |
| :--- | :--- |
| `RESUME` | 이력서 |
| `PORTFOLIO` | 포트폴리오 |

#### A.6 추출 상태 (document.extract_status)
| 값 | 설명 |
| :--- | :--- |
| `PENDING` | 추출 대기 중 |
| `READY` | 추출 완료 |
| `FAILED` | 추출 실패 |

#### A.7 난이도 (interview_question_item.difficulty_level)
| 값 | 설명 |
| :--- | :--- |
| `EASY` | 쉬움 |
| `MEDIUM` | 보통 |
| `HARD` | 어려움 |

#### A.8 LLM 호출 상태 (llm_call_log.call_status)
| 값 | 설명 |
| :--- | :--- |
| `SUCCESS` | 성공 |
| `FAIL` | 실패 |

---

### B. 데이터 흐름 (Data Flow)

```
1. 관리자/사용자 계정 생성 및 로그인
   └─> manager / user

2. 지원자 등록
   └─> candidate

3. 문서 업로드 및 텍스트 추출
   └─> document
       └─> extract_status: PENDING → READY

4. 프롬프트 프로파일 선택
   └─> prompt_profile

5. LLM 호출 및 응답 로그 기록
   └─> llm_call_log (candidate + document + prompt_profile)

6. 면접 질문 저장
   └─> interview_question_item (candidate + prompt_profile + source_document)
```

---

### C. 참조 무결성 (Foreign Key Constraints)

| 테이블 | FK 컬럼 | 참조 테이블 | 참조 컬럼 |
| :--- | :--- | :--- | :--- |
| `user` | `approved_by` | `manager` | `id` |
| `user` | `created_by` | `manager` | `id` |
| `candidate` | `resume_doc_id` | `document` | `id` |
| `candidate` | `portfolio_doc_id` | `document` | `id` |
| `document` | `candidate_id` | `candidate` | `id` |
| `interview_question_item` | `candidate_id` | `candidate` | `id` |
| `interview_question_item` | `prompt_profile_id` | `prompt_profile` | `id` |
| `interview_question_item` | `source_document_id` | `document` | `id` |
| `llm_call_log` | `candidate_id` | `candidate` | `id` |
| `llm_call_log` | `document_id` | `document` | `id` |
| `llm_call_log` | `prompt_profile_id` | `prompt_profile` | `id` |

---

### D. Audit 컬럼 (공통 적용)

모든 테이블에 공통으로 적용되는 Audit 컬럼:

| 컬럼명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `created_at` | `timestamp` | 생성 일시 |
| `created_by` | `uuid` | 생성자 ID |
| `deleted_at` | `timestamp` | 삭제 일시 (논리 삭제) |
| `deleted_by` | `uuid` | 삭제자 ID (논리 삭제) |

**논리 삭제 정책 (FR-08-02)**:
- 삭제 시 물리 삭제 대신 `deleted_at`, `deleted_by`를 기록
- 조회 시 `deleted_at IS NULL` 조건으로 필터링

