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

### 3.7 지원자 통계 조회

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