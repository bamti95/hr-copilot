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

### 3.7 지원자 문서 업로드

**Endpoint**: `POST /candidates/{id}/documents`

**설명**: 지원자의 문서(이력서, 자기소개서 등)를 업로드합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID

**Request Body** (multipart/form-data):
- `document_types` (array[string], required): 문서 유형 목록 (RESUME, COVER_LETTER, PORTFOLIO, CERTIFICATE, ETC)
- `files` (array[file], required): 업로드할 파일 목록 (document_types와 1:1 대응)

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "uploaded_documents": [
      {
        "id": 1,
        "candidate_id": 10,
        "document_type": "RESUME",
        "file_name": "김지원_이력서.pdf",
        "file_path": "/uploads/candidates/10/resume_20250415.pdf",
        "file_size": 245678,
        "uploaded_at": "2025-04-15T10:30:00Z",
        "uploaded_by": 1
      },
      {
        "id": 2,
        "candidate_id": 10,
        "document_type": "COVER_LETTER",
        "file_name": "김지원_자기소개서.pdf",
        "file_path": "/uploads/candidates/10/cover_20250415.pdf",
        "file_size": 123456,
        "uploaded_at": "2025-04-15T10:30:00Z",
        "uploaded_by": 1
      }
    ]
  },
  "message": "지원자 문서 업로드 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **400** | `INVALID_DOCUMENT_TYPE` | "유효하지 않은 문서 유형입니다." | 잘못된 document_type 값일 때 |
| **400** | `FILE_COUNT_MISMATCH` | "문서 유형과 파일 개수가 일치하지 않습니다." | document_types와 files 배열 길이가 다를 때 |
| **400** | `FILE_TOO_LARGE` | "파일 크기가 너무 큽니다." | 파일 크기 제한 초과 시 |
| **400** | `INVALID_FILE_TYPE` | "지원하지 않는 파일 형식입니다." | 허용되지 않은 파일 확장자일 때 |

---

### 3.8 지원자 문서 다운로드

**Endpoint**: `GET /candidates/{id}/documents/{document_id}/download`

**설명**: 지원자의 특정 문서를 다운로드합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID
- `document_id` (integer, required): 문서 ID

**Response (200)**:
- Content-Type: application/octet-stream (또는 파일의 MIME 타입)
- Content-Disposition: attachment; filename="원본파일명.확장자"
- 파일 바이너리 데이터

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |
| **404** | `FILE_NOT_FOUND` | "파일을 찾을 수 없습니다." | 실제 파일이 서버에 없을 때 |

---

### 3.9 지원자 문서 삭제

**Endpoint**: `DELETE /candidates/{id}/documents/{document_id}`

**설명**: 지원자의 특정 문서를 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID
- `document_id` (integer, required): 문서 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {Headers:
  
  Authorization: Bearer {access_token}
  Content-Type: multipart/form-data
  Path Parameters:
  
  id (integer, required): 지원자 ID
  document_id (integer, required): 문서 ID
  Request Body (multipart/form-data):
  
  document_type (string, required): 문서 유형 (RESUME, COVER_LETTER, PORTFOLIO, CERTIFICATE, ETC)
  file (file, required): 교체할 파일
  Response (200):
  
  {
    "success": true,
    "data": {
      "id": 1,
      "candidate_id": 10,
      "document_type": "RESUME",
      "file_name": "김지원_이력서_v2.pdf",
      "file_path": "/uploads/candidates/10/resume_20250415_v2.pdf",
      "file_size": 267890,
      "uploaded_at": "2025-04-15T12:00:00Z",
      "uploaded_by": 1
    },
    "message": "지원자 문서 교체 성공"
  }
  에러 응답 (Error Response)
  상태 코드	에러 코드	메시지	발생 상황
  404	CANDIDATE_NOT_FOUND	"지원자를 찾을 수 없습니다."	존재하지 않는 지원자 ID일 때
  404	DOCUMENT_NOT_FOUND	"문서를 찾을 수 없습니다."	존재하지 않는 문서 ID일 때
  400	INVALID_DOCUMENT_TYPE	"유효하지 않은 문서 유형입니다."	잘못된 document_type 값일 때
  400	FILE_TOO_LARGE	"파일 크기가 너무 큽니다."	파일 크기 제한 초과 시
  400	INVALID_FILE_TYPE	"지원하지 않는 파일 형식입니다."	허용되지 않은 파일 확장자일 때
    "id": 1,
    "candidate_id": 10,
    "deleted_at": "2025-04-15T11:30:00Z",
    "deleted_by": 1
  },
  "message": "지원자 문서 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |
| **400** | `ALREADY_DELETED` | "이미 삭제된 문서입니다." | deleted_at이 NULL이 아닐 때 |

---

### 3.10 지원자 문서 교체

**Endpoint**: `PUT /candidates/{id}/documents/{document_id}`

**설명**: 지원자의 특정 문서를 새 파일로 교체합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Path Parameters**:
- `id` (integer, required): 지원자 ID
- `document_id` (integer, required): 문서 ID

**Request Body** (multipart/form-data):
- `document_type` (string, required): 문서 유형 (RESUME, COVER_LETTER, PORTFOLIO, CERTIFICATE, ETC)
- `file` (file, required): 교체할 파일

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "candidate_id": 10,
    "document_type": "RESUME",
    "file_name": "김지원_이력서_v2.pdf",
    "file_path": "/uploads/candidates/10/resume_20250415_v2.pdf",
    "file_size": 267890,
    "uploaded_at": "2025-04-15T12:00:00Z",
    "uploaded_by": 1
  },
  "message": "지원자 문서 교체 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `CANDIDATE_NOT_FOUND` | "지원자를 찾을 수 없습니다." | 존재하지 않는 지원자 ID일 때 |
| **404** | `DOCUMENT_NOT_FOUND` | "문서를 찾을 수 없습니다." | 존재하지 않는 문서 ID일 때 |
| **400** | `INVALID_DOCUMENT_TYPE` | "유효하지 않은 문서 유형입니다." | 잘못된 document_type 값일 때 |
| **400** | `FILE_TOO_LARGE` | "파일 크기가 너무 큽니다." | 파일 크기 제한 초과 시 |
| **400** | `INVALID_FILE_TYPE` | "지원하지 않는 파일 형식입니다." | 허용되지 않은 파일 확장자일 때 |

---

### 3.11 지원자 통계 조회

**Endpoint**: `GET /candidates/statistics`

**설명**: 논리 삭제되지 않은 지원자의 전체 인원, 지원 상태별 인원, 직무별 인원을 집계합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**: 없음 (전체 스냅샷)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "total_candidates": 87,
    "by_apply_status": [
      { "apply_status": "APPLIED", "count": 12 },
      { "apply_status": "SCREENING", "count": 30 },
      { "apply_status": "INTERVIEW", "count": 25 },
      { "apply_status": "ACCEPTED", "count": 10 },
      { "apply_status": "REJECTED", "count": 10 }
    ],
    "by_target_job": [
      { "target_job": "BACKEND_DEVELOPER", "count": 18 },
      { "target_job": "FRONTEND_DEVELOPER", "count": 14 }
    ],
    "active_without_interview_session_count": 22
  },
  "message": "지원자 통계 조회 성공"
}
```

**Response 필드 설명**:
- `total_candidates`: 논리 삭제되지 않은 전체 지원자 수
- `by_apply_status`: 지원 상태별 인원 집계
- `by_target_job`: 면접 세션의 `target_job` 기준 지원자 수 (지원자 ID 중복 제거)
- `active_without_interview_session_count`: 활성 지원자 중 삭제되지 않은 면접 세션이 없는 인원

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰일 때 |