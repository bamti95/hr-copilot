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
