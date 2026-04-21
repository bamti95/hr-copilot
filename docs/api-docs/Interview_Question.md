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