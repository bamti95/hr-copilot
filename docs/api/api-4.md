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