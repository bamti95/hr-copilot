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