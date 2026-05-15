# 채용공고 컴플라이언스 점검 API 문서

## 목차
- [채용공고 관리](#채용공고-관리)
- [채용공고 분석](#채용공고-분석)
- [분석 리포트 관리](#분석-리포트-관리)
- [비동기 작업 관리](#비동기-작업-관리)
- [RAG 지식문서 관리](#rag-지식문서-관리)
- [AI 호출 로그](#ai-호출-로그)
- [채용공고 RAG 실험 관리](#채용공고-rag-실험-관리)
- [참고 코드](#참고-코드)

---

## 채용공고 관리

### 1. 채용공고 등록

**Method**: `POST`

**URL**: `/api/v1/job-postings`

**Description**: 새로운 채용공고를 등록합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "title": "백엔드 개발자 채용",
  "company_name": "테크컴퍼니",
  "content": "Python/Django 백엔드 개발자를 모집합니다...",
  "position": "백엔드 개발자",
  "requirements": "Python 3년 이상 경력",
  "employment_type": "정규직"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "백엔드 개발자 채용",
    "company_name": "테크컴퍼니",
    "content": "Python/Django 백엔드 개발자를 모집합니다...",
    "position": "백엔드 개발자",
    "status": "DRAFT",
    "created_at": "2025-05-14T10:30:00Z",
    "created_by": 1
  },
  "message": "채용공고 등록 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 요청 데이터입니다." | 필수 필드 누락 또는 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 2. 채용공고 목록 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings`

**Description**: 채용공고 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (default: 0, minimum: 0)
- `size` (integer, optional): 페이지 크기 (default: 10, minimum: 1, maximum: 100)
- `keyword` (string, optional): 검색 키워드

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "title": "백엔드 개발자 채용",
        "company_name": "테크컴퍼니",
        "position": "백엔드 개발자",
        "status": "ACTIVE",
        "created_at": "2025-05-14T10:30:00Z"
      }
    ],
    "total": 50,
    "page": 0,
    "size": 10
  },
  "message": "채용공고 목록 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 3. 채용공고 상세 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/{posting_id}`

**Description**: 특정 채용공고의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `posting_id` (integer, required): 채용공고 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "백엔드 개발자 채용",
    "company_name": "테크컴퍼니",
    "content": "Python/Django 백엔드 개발자를 모집합니다...",
    "position": "백엔드 개발자",
    "requirements": "Python 3년 이상 경력",
    "employment_type": "정규직",
    "status": "ACTIVE",
    "created_at": "2025-05-14T10:30:00Z",
    "created_by": 1,
    "updated_at": "2025-05-14T11:00:00Z"
  },
  "message": "채용공고 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_POSTING_NOT_FOUND` | "존재하지 않는 채용공고입니다." | 존재하지 않는 채용공고 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## 채용공고 분석

### 4. 채용공고 텍스트 분석

**Method**: `POST`

**URL**: `/api/v1/job-postings/analyze-text`

**Description**: 채용공고 텍스트를 분석합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "text": "우리 회사는 젊고 패기 넘치는 20대 남성 개발자를 찾습니다...",
  "analysis_type": "FULL"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "analysis_id": "abc-123-def",
    "compliance_score": 65,
    "violations": [
      {
        "type": "AGE_DISCRIMINATION",
        "severity": "HIGH",
        "description": "연령 차별적 표현이 포함되어 있습니다.",
        "matched_text": "20대",
        "suggestion": "연령 제한 없이 '경력 X년 이상' 등으로 수정하세요."
      },
      {
        "type": "GENDER_DISCRIMINATION",
        "severity": "HIGH",
        "description": "성별 차별적 표현이 포함되어 있습니다.",
        "matched_text": "남성",
        "suggestion": "성별 표현을 삭제하고 중립적인 표현을 사용하세요."
      }
    ],
    "recommendations": [
      "법적 리스크가 높은 표현들을 수정해주세요.",
      "성별, 연령 제한 없이 능력 중심으로 재작성을 권장합니다."
    ],
    "analyzed_at": "2025-05-14T10:30:00Z"
  },
  "message": "채용공고 분석 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "분석할 텍스트가 비어있습니다." | 빈 텍스트 전송 시 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `ANALYSIS_FAILED` | "분석 중 오류가 발생했습니다." | AI 분석 실패 |

---

### 5. 채용공고 텍스트 분석 비동기 작업 시작

**Method**: `POST`

**URL**: `/api/v1/job-postings/analyze-text/jobs`

**Description**: 채용공고 텍스트 분석 비동기 작업을 시작합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "text": "우리 회사는 젊고 패기 넘치는 20대 남성 개발자를 찾습니다...",
  "analysis_type": "FULL"
}
```

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "job_id": 456,
    "status": "PENDING",
    "created_at": "2025-05-14T10:30:00Z"
  },
  "message": "분석 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "분석할 텍스트가 비어있습니다." | 빈 텍스트 전송 시 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 6. 채용공고 파일 분석

**Method**: `POST`

**URL**: `/api/v1/job-postings/analyze-file`

**Description**: 채용공고 파일을 분석합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body** (multipart/form-data):
- `file` (file, required): 분석할 채용공고 파일 (PDF, DOCX, TXT 등)
- `analysis_type` (string, optional): 분석 유형 (default: "FULL")

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "analysis_id": "xyz-789-abc",
    "file_name": "job_posting.pdf",
    "compliance_score": 72,
    "violations": [
      {
        "type": "AGE_DISCRIMINATION",
        "severity": "HIGH",
        "description": "연령 차별적 표현이 포함되어 있습니다.",
        "matched_text": "신입~경력 3년",
        "page": 1,
        "suggestion": "경력 제한만 명시하고 신입 표현을 제거하세요."
      }
    ],
    "recommendations": [
      "나이 대신 경력으로 요구사항을 명시하세요."
    ],
    "analyzed_at": "2025-05-14T10:35:00Z"
  },
  "message": "파일 분석 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "지원하지 않는 파일 형식입니다." | 잘못된 파일 형식 |
| 413 | `FILE_TOO_LARGE` | "파일 크기가 너무 큽니다." | 파일 크기 초과 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `ANALYSIS_FAILED` | "파일 분석 중 오류가 발생했습니다." | 파일 분석 실패 |

---

### 7. 채용공고 파일 분석 비동기 작업 시작

**Method**: `POST`

**URL**: `/api/v1/job-postings/analyze-file/jobs`

**Description**: 채용공고 파일 분석 비동기 작업을 시작합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body** (multipart/form-data):
- `file` (file, required): 분석할 채용공고 파일
- `analysis_type` (string, optional): 분석 유형 (default: "FULL")

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "job_id": 789,
    "status": "PENDING",
    "file_name": "job_posting.pdf",
    "created_at": "2025-05-14T10:40:00Z"
  },
  "message": "파일 분석 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "지원하지 않는 파일 형식입니다." | 잘못된 파일 형식 |
| 413 | `FILE_TOO_LARGE` | "파일 크기가 너무 큽니다." | 파일 크기 초과 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## 분석 리포트 관리

### 8. 기존 채용공고 재분석

**Method**: `POST`

**URL**: `/api/v1/job-postings/{posting_id}/analysis-reports`

**Description**: 기존 채용공고를 재분석합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `posting_id` (integer, required): 채용공고 ID

**Query Parameters**:
- `analysis_type` (string, optional): 분석 유형 (default: "FULL")

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "report_id": 1001,
    "posting_id": 123,
    "analysis_type": "FULL",
    "compliance_score": 85,
    "violations": [],
    "recommendations": [
      "현재 채용공고는 법적 리스크가 낮습니다."
    ],
    "created_at": "2025-05-14T10:45:00Z"
  },
  "message": "재분석 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_POSTING_NOT_FOUND` | "존재하지 않는 채용공고입니다." | 존재하지 않는 채용공고 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `ANALYSIS_FAILED` | "재분석 중 오류가 발생했습니다." | 분석 실패 |

---

### 9. 기존 채용공고 재분석 비동기 작업 시작

**Method**: `POST`

**URL**: `/api/v1/job-postings/{posting_id}/analysis-reports/jobs`

**Description**: 기존 채용공고 재분석 비동기 작업을 시작합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `posting_id` (integer, required): 채용공고 ID

**Query Parameters**:
- `analysis_type` (string, optional): 분석 유형 (default: "FULL")

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "job_id": 890,
    "posting_id": 123,
    "status": "PENDING",
    "created_at": "2025-05-14T10:50:00Z"
  },
  "message": "재분석 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_POSTING_NOT_FOUND` | "존재하지 않는 채용공고입니다." | 존재하지 않는 채용공고 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 10. 채용공고 분석 리포트 목록 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/{posting_id}/analysis-reports`

**Description**: 채용공고의 분석 리포트 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `posting_id` (integer, required): 채용공고 ID

**Query Parameters**:
- `limit` (integer, optional): 조회할 최대 개수 (default: 20, minimum: 1, maximum: 100)

**Response (200)**:
```json
{
  "success": true,
  "data": [
    {
      "report_id": 1001,
      "posting_id": 123,
      "analysis_type": "FULL",
      "compliance_score": 85,
      "violation_count": 0,
      "created_at": "2025-05-14T10:45:00Z"
    },
    {
      "report_id": 1000,
      "posting_id": 123,
      "analysis_type": "FULL",
      "compliance_score": 72,
      "violation_count": 2,
      "created_at": "2025-05-14T09:30:00Z"
    }
  ],
  "message": "분석 리포트 목록 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_POSTING_NOT_FOUND` | "존재하지 않는 채용공고입니다." | 존재하지 않는 채용공고 ID |
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 11. 채용공고 분석 리포트 상세 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/analysis-reports/{report_id}`

**Description**: 채용공고 분석 리포트의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `report_id` (integer, required): 분석 리포트 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "report_id": 1001,
    "posting_id": 123,
    "analysis_type": "FULL",
    "compliance_score": 85,
    "violations": [
      {
        "type": "MINOR_ISSUE",
        "severity": "LOW",
        "description": "일부 표현이 모호합니다.",
        "matched_text": "젊은 인재",
        "suggestion": "구체적인 경력 요구사항으로 대체하세요."
      }
    ],
    "recommendations": [
      "전반적으로 법적 리스크가 낮으나 일부 표현 개선을 권장합니다."
    ],
    "created_at": "2025-05-14T10:45:00Z"
  },
  "message": "분석 리포트 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `REPORT_NOT_FOUND` | "존재하지 않는 분석 리포트입니다." | 존재하지 않는 리포트 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## 비동기 작업 관리

### 12. 실행 중인 채용공고 분석 작업 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/analysis-jobs/active`

**Description**: 실행 중인 채용공고 분석 작업을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `posting_id` (integer, optional): 특정 채용공고의 작업만 조회

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "job_id": 890,
    "posting_id": 123,
    "status": "PROCESSING",
    "progress": 65,
    "created_at": "2025-05-14T10:50:00Z",
    "started_at": "2025-05-14T10:50:30Z"
  },
  "message": "실행 중인 작업 조회 성공"
}
```

**Response (200) - 실행 중인 작업 없음**:
```json
{
  "success": true,
  "data": null,
  "message": "실행 중인 작업이 없습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 13. 채용공고 분석 비동기 작업 상태 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/analysis-jobs/{job_id}`

**Description**: 채용공고 분석 비동기 작업의 상태를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `job_id` (integer, required): 작업 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "job_id": 890,
    "posting_id": 123,
    "status": "COMPLETED",
    "progress": 100,
    "result": {
      "report_id": 1002,
      "compliance_score": 88
    },
    "created_at": "2025-05-14T10:50:00Z",
    "started_at": "2025-05-14T10:50:30Z",
    "completed_at": "2025-05-14T10:52:00Z"
  },
  "message": "작업 상태 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_NOT_FOUND` | "존재하지 않는 작업입니다." | 존재하지 않는 작업 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## RAG 지식문서 관리

### 14. RAG 지식문서 업로드

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/upload`

**Description**: RAG 시스템에 사용할 지식문서를 업로드합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body** (multipart/form-data):
- `file` (file, required): 업로드할 지식문서 파일
- `title` (string, required): 문서 제목
- `description` (string, optional): 문서 설명
- `source_type` (string, optional): 문서 유형 (예: "법률", "가이드라인")

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "source_id": 501,
    "title": "고용평등법 가이드",
    "file_name": "employment_equality_guide.pdf",
    "source_type": "법률",
    "status": "UPLOADED",
    "file_size": 2048576,
    "created_at": "2025-05-14T11:00:00Z"
  },
  "message": "지식문서 업로드 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "지원하지 않는 파일 형식입니다." | 잘못된 파일 형식 |
| 413 | `FILE_TOO_LARGE` | "파일 크기가 너무 큽니다." | 파일 크기 초과 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 15. RAG 지식문서 목록 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/knowledge-sources`

**Description**: RAG 지식문서 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (default: 0, minimum: 0)
- `size` (integer, optional): 페이지 크기 (default: 10, minimum: 1, maximum: 100)
- `source_type` (string, optional): 문서 유형 필터
- `keyword` (string, optional): 검색 키워드

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "source_id": 501,
        "title": "고용평등법 가이드",
        "file_name": "employment_equality_guide.pdf",
        "source_type": "법률",
        "status": "INDEXED",
        "chunk_count": 150,
        "created_at": "2025-05-14T11:00:00Z"
      }
    ],
    "total": 25,
    "page": 0,
    "size": 10
  },
  "message": "지식문서 목록 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 16. RAG 지식문서 인덱싱

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/{source_id}/index`

**Description**: RAG 지식문서를 인덱싱합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `source_id` (integer, required): 지식문서 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "source_id": 501,
    "status": "INDEXED",
    "chunk_count": 150,
    "indexed_at": "2025-05-14T11:05:00Z"
  },
  "message": "지식문서 인덱싱 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `SOURCE_NOT_FOUND` | "존재하지 않는 지식문서입니다." | 존재하지 않는 문서 ID |
| 400 | `ALREADY_INDEXED` | "이미 인덱싱된 문서입니다." | 중복 인덱싱 시도 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `INDEXING_FAILED` | "인덱싱 중 오류가 발생했습니다." | 인덱싱 실패 |

---

### 17. RAG 지식문서 인덱싱 비동기 작업 시작

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/{source_id}/index/jobs`

**Description**: RAG 지식문서 인덱싱 비동기 작업을 시작합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `source_id` (integer, required): 지식문서 ID

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "job_id": 991,
    "source_id": 501,
    "status": "PENDING",
    "created_at": "2025-05-14T11:10:00Z"
  },
  "message": "인덱싱 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `SOURCE_NOT_FOUND` | "존재하지 않는 지식문서입니다." | 존재하지 않는 문서 ID |
| 400 | `ALREADY_INDEXING` | "이미 인덱싱 작업이 진행 중입니다." | 중복 작업 시도 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 18. 실행 중인 RAG 인덱싱 작업 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/knowledge-index-jobs/active`

**Description**: 실행 중인 RAG 지식문서 인덱싱 작업을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "job_id": 991,
    "source_id": 501,
    "status": "PROCESSING",
    "progress": 45,
    "created_at": "2025-05-14T11:10:00Z",
    "started_at": "2025-05-14T11:10:30Z"
  },
  "message": "실행 중인 인덱싱 작업 조회 성공"
}
```

**Response (200) - 실행 중인 작업 없음**:
```json
{
  "success": true,
  "data": null,
  "message": "실행 중인 인덱싱 작업이 없습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 19. RAG 인덱싱 비동기 작업 상태 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/knowledge-index-jobs/{job_id}`

**Description**: RAG 지식문서 인덱싱 비동기 작업의 상태를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `job_id` (integer, required): 작업 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "job_id": 991,
    "source_id": 501,
    "status": "COMPLETED",
    "progress": 100,
    "result": {
      "chunk_count": 150,
      "indexed_at": "2025-05-14T11:15:00Z"
    },
    "created_at": "2025-05-14T11:10:00Z",
    "started_at": "2025-05-14T11:10:30Z",
    "completed_at": "2025-05-14T11:15:00Z"
  },
  "message": "인덱싱 작업 상태 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_NOT_FOUND` | "존재하지 않는 작업입니다." | 존재하지 않는 작업 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 20. RAG 지식문서 청크 목록 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/knowledge-sources/{source_id}/chunks`

**Description**: RAG 지식문서의 청크 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `source_id` (integer, required): 지식문서 ID

**Query Parameters**:
- `limit` (integer, optional): 조회할 최대 개수 (default: 100, minimum: 1, maximum: 1000)

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "chunks": [
      {
        "chunk_id": 10001,
        "source_id": 501,
        "content": "고용평등법 제7조에 따르면...",
        "chunk_index": 0,
        "metadata": {
          "page": 1,
          "section": "제7조"
        },
        "created_at": "2025-05-14T11:15:00Z"
      },
      {
        "chunk_id": 10002,
        "source_id": 501,
        "content": "사업주는 근로자 모집 시...",
        "chunk_index": 1,
        "metadata": {
          "page": 2,
          "section": "제8조"
        },
        "created_at": "2025-05-14T11:15:00Z"
      }
    ],
    "total": 150
  },
  "message": "청크 목록 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `SOURCE_NOT_FOUND` | "존재하지 않는 지식문서입니다." | 존재하지 않는 문서 ID |
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 21. RAG 기반지식 하이브리드 검색

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/search`

**Description**: RAG 시스템에서 하이브리드 검색을 수행합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": "연령 차별 금지 조항",
  "top_k": 5,
  "source_types": ["법률", "가이드라인"],
  "min_score": 0.7
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "chunk_id": 10001,
        "source_id": 501,
        "source_title": "고용평등법 가이드",
        "content": "고용평등법 제7조에 따르면 사업주는 근로자 모집·채용 시 합리적인 이유 없이 연령을 이유로 차별하여서는 아니 된다.",
        "score": 0.92,
        "metadata": {
          "page": 1,
          "section": "제7조"
        }
      },
      {
        "chunk_id": 10015,
        "source_id": 502,
        "source_title": "채용공고 작성 가이드",
        "content": "채용공고 작성 시 '젊은', '신입~경력 N년' 등의 표현은 연령 차별로 간주될 수 있으니 주의해야 합니다.",
        "score": 0.85,
        "metadata": {
          "page": 3,
          "section": "주의사항"
        }
      }
    ],
    "total": 5,
    "query": "연령 차별 금지 조항"
  },
  "message": "검색 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "검색어가 비어있습니다." | 빈 검색어 전송 시 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `SEARCH_FAILED` | "검색 중 오류가 발생했습니다." | 검색 실패 |

---

### 22. 샘플 법률문서 일괄 적재

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/seed-source-data`

**Description**: 샘플 법률문서를 일괄 적재합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "total_seeded": 15,
    "sources": [
      {
        "source_id": 601,
        "title": "고용평등법",
        "status": "UPLOADED"
      },
      {
        "source_id": 602,
        "title": "근로기준법",
        "status": "UPLOADED"
      }
    ],
    "completed_at": "2025-05-14T11:30:00Z"
  },
  "message": "샘플 법률문서 일괄 적재 완료"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |
| 500 | `SEED_FAILED` | "샘플 데이터 적재 중 오류가 발생했습니다." | 적재 실패 |

---

### 23. 샘플 법률문서 일괄 적재 비동기 작업 시작

**Method**: `POST`

**URL**: `/api/v1/job-postings/knowledge-sources/seed-source-data/jobs`

**Description**: 샘플 법률문서 일괄 적재 비동기 작업을 시작합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "job_id": 1050,
    "status": "PENDING",
    "created_at": "2025-05-14T11:35:00Z"
  },
  "message": "샘플 데이터 적재 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## AI 호출 로그

### 24. 분석 리포트별 AI 호출 로그 조회

**Method**: `GET`

**URL**: `/api/v1/llm-logs/job-posting-analysis-reports/{report_id}`

**Description**: 특정 분석 리포트의 AI 호출 로그를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `report_id` (integer, required): 분석 리포트 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "log_id": 5001,
        "report_id": 1001,
        "model": "claude-3-opus",
        "prompt_tokens": 1500,
        "completion_tokens": 800,
        "total_tokens": 2300,
        "latency_ms": 3200,
        "status": "SUCCESS",
        "created_at": "2025-05-14T10:45:30Z"
      },
      {
        "log_id": 5002,
        "report_id": 1001,
        "model": "claude-3-sonnet",
        "prompt_tokens": 1200,
        "completion_tokens": 600,
        "total_tokens": 1800,
        "latency_ms": 2100,
        "status": "SUCCESS",
        "created_at": "2025-05-14T10:45:45Z"
      }
    ],
    "total": 2
  },
  "message": "AI 호출 로그 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `REPORT_NOT_FOUND` | "존재하지 않는 분석 리포트입니다." | 존재하지 않는 리포트 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 25. 채용공고별 AI 호출 로그 조회

**Method**: `GET`

**URL**: `/api/v1/llm-logs/job-postings/{job_posting_id}`

**Description**: 특정 채용공고의 AI 호출 로그를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `job_posting_id` (integer, required): 채용공고 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "log_id": 5010,
        "job_posting_id": 123,
        "report_id": 1001,
        "model": "claude-3-opus",
        "prompt_tokens": 1500,
        "completion_tokens": 800,
        "total_tokens": 2300,
        "latency_ms": 3200,
        "status": "SUCCESS",
        "created_at": "2025-05-14T10:45:30Z"
      }
    ],
    "total": 1
  },
  "message": "AI 호출 로그 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_POSTING_NOT_FOUND` | "존재하지 않는 채용공고입니다." | 존재하지 않는 채용공고 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## 채용공고 RAG 실험 관리

### 26. 채용공고 RAG 실험 run 등록

**Method**: `POST`

**URL**: `/api/v1/job-postings/experiments`

**Description**: 채용공고 RAG 실험 run을 등록합니다.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "title": "RAG 성능 개선 실험 v1.0",
  "description": "하이브리드 검색 파라미터 튜닝 실험",
  "dataset_name": "job_posting_risk_50",
  "dataset_version": "v1.0",
  "experiment_type": "RAG_EVAL",
  "config_snapshot": {
    "top_k": 5,
    "min_score": 0.7,
    "retrieval_method": "hybrid"
  }
}
```

**Response (201)**:
```json
{
  "id": 1,
  "title": "RAG 성능 개선 실험 v1.0",
  "description": "하이브리드 검색 파라미터 튜닝 실험",
  "dataset_name": "job_posting_risk_50",
  "dataset_version": "v1.0",
  "experiment_type": "RAG_EVAL",
  "status": "PENDING",
  "total_cases": 50,
  "completed_cases": 0,
  "failed_cases": 0,
  "retrieval_recall_at_5": 0,
  "macro_f1": 0,
  "high_risk_recall": 0,
  "source_omission_rate": 0,
  "avg_latency_ms": 0,
  "config_snapshot": {
    "top_k": 5,
    "min_score": 0.7,
    "retrieval_method": "hybrid"
  },
  "summary_metrics": {},
  "result_summary": {},
  "ai_job_id": 1001,
  "requested_by": 1,
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-05-15T07:56:19.709Z",
  "updated_at": "2026-05-15T07:56:19.709Z"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 요청 데이터입니다." | 필수 필드 누락 또는 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 27. 채용공고 RAG 실험 run 목록 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/experiments`

**Description**: 채용공고 RAG 실험 run 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (default: 0, minimum: 0)
- `size` (integer, optional): 페이지 크기 (default: 10, minimum: 1, maximum: 100)

**Response (200)**:
```json
{
  "items": [
    {
      "id": 1,
      "title": "RAG 성능 개선 실험 v1.0",
      "description": "하이브리드 검색 파라미터 튜닝 실험",
      "dataset_name": "job_posting_risk_50",
      "dataset_version": "v1.0",
      "experiment_type": "RAG_EVAL",
      "status": "COMPLETED",
      "total_cases": 50,
      "completed_cases": 50,
      "failed_cases": 0,
      "retrieval_recall_at_5": 0.92,
      "macro_f1": 0.87,
      "high_risk_recall": 0.95,
      "source_omission_rate": 0.04,
      "avg_latency_ms": 1250,
      "config_snapshot": {
        "top_k": 5,
        "min_score": 0.7
      },
      "summary_metrics": {
        "precision": 0.89,
        "recall": 0.85
      },
      "result_summary": {
        "total_passed": 45,
        "total_failed": 5
      },
      "ai_job_id": 1001,
      "requested_by": 1,
      "started_at": "2026-05-15T07:56:49.014Z",
      "completed_at": "2026-05-15T08:10:30.014Z",
      "created_at": "2026-05-15T07:56:19.709Z",
      "updated_at": "2026-05-15T08:10:30.014Z"
    }
  ],
  "total_count": 15,
  "total_pages": 2
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 28. 채용공고 RAG 실험 run 상세 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/experiments/{run_id}`

**Description**: 채용공고 RAG 실험 run의 상세 정보와 케이스 결과를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `run_id` (integer, required): 실험 run ID

**Query Parameters**:
- `case_limit` (integer, optional): 조회할 최대 케이스 개수 (default: 200, minimum: 1, maximum: 500)

**Response (200)**:
```json
{
  "run": {
    "id": 1,
    "title": "RAG 성능 개선 실험 v1.0",
    "description": "하이브리드 검색 파라미터 튜닝 실험",
    "dataset_name": "job_posting_risk_50",
    "dataset_version": "v1.0",
    "experiment_type": "RAG_EVAL",
    "status": "COMPLETED",
    "total_cases": 50,
    "completed_cases": 50,
    "failed_cases": 0,
    "retrieval_recall_at_5": 0.92,
    "macro_f1": 0.87,
    "high_risk_recall": 0.95,
    "source_omission_rate": 0.04,
    "avg_latency_ms": 1250,
    "config_snapshot": {
      "top_k": 5,
      "min_score": 0.7
    },
    "summary_metrics": {
      "precision": 0.89,
      "recall": 0.85
    },
    "result_summary": {
      "total_passed": 45,
      "total_failed": 5
    },
    "ai_job_id": 1001,
    "requested_by": 1,
    "started_at": "2026-05-15T07:56:49.014Z",
    "completed_at": "2026-05-15T08:10:30.014Z",
    "created_at": "2026-05-15T07:56:19.709Z",
    "updated_at": "2026-05-15T08:10:30.014Z"
  },
  "case_results": [
    {
      "id": 1,
      "case_id": "case_001",
      "case_index": 0,
      "job_group": "IT개발",
      "status": "PASSED",
      "expected_label": "HIGH_RISK",
      "predicted_label": "HIGH_RISK",
      "expected_risk_types": ["AGE_DISCRIMINATION", "GENDER_DISCRIMINATION"],
      "predicted_risk_types": ["AGE_DISCRIMINATION", "GENDER_DISCRIMINATION"],
      "retrieval_hit_at_5": true,
      "source_omitted": false,
      "latency_ms": 1200,
      "error_message": null,
      "evaluation_payload": {
        "query": "20대 남성 개발자",
        "retrieved_chunks": 5
      },
      "report_payload": {
        "compliance_score": 45,
        "violations_count": 2
      }
    },
    {
      "id": 2,
      "case_id": "case_002",
      "case_index": 1,
      "job_group": "영업마케팅",
      "status": "FAILED",
      "expected_label": "LOW_RISK",
      "predicted_label": "MEDIUM_RISK",
      "expected_risk_types": [],
      "predicted_risk_types": ["MINOR_ISSUE"],
      "retrieval_hit_at_5": true,
      "source_omitted": false,
      "latency_ms": 1100,
      "error_message": null,
      "evaluation_payload": {
        "query": "경력 3년 이상",
        "retrieved_chunks": 5
      },
      "report_payload": {
        "compliance_score": 75,
        "violations_count": 1
      }
    }
  ]
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `EXPERIMENT_NOT_FOUND` | "존재하지 않는 실험입니다." | 존재하지 않는 실험 ID |
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 29. 채용공고 RAG 실험 run 실행

**Method**: `POST`

**URL**: `/api/v1/job-postings/experiments/{run_id}/jobs`

**Description**: 채용공고 RAG 실험 run을 실행합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `run_id` (integer, required): 실험 run ID

**Response (202)**:
```json
{
  "job_id": 1001,
  "status": "PENDING",
  "job_type": "RAG_EXPERIMENT",
  "target_type": "EXPERIMENT_RUN",
  "target_id": 1,
  "progress": 0,
  "current_step": "INITIALIZING",
  "error_message": null,
  "request_payload": {
    "run_id": 1,
    "dataset_name": "job_posting_risk_50"
  },
  "result_payload": {},
  "message": "실험 run 작업이 시작되었습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `EXPERIMENT_NOT_FOUND` | "존재하지 않는 실험입니다." | 존재하지 않는 실험 ID |
| 400 | `ALREADY_RUNNING` | "이미 실행 중인 실험입니다." | 중복 실행 시도 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 30. 실행 중인 채용공고 RAG 실험 활성 작업 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/experiment-jobs/active`

**Description**: 현재 실행 중인 채용공고 RAG 실험 활성 작업을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `run_id` (integer, optional): 특정 실험 run의 작업만 조회

**Response (200)**:
```json
{
  "job_id": 1001,
  "status": "PROCESSING",
  "job_type": "RAG_EXPERIMENT",
  "target_type": "EXPERIMENT_RUN",
  "target_id": 1,
  "progress": 65,
  "current_step": "EVALUATING_CASES",
  "error_message": null,
  "request_payload": {
    "run_id": 1,
    "dataset_name": "job_posting_risk_50"
  },
  "result_payload": {
    "completed_cases": 32,
    "total_cases": 50
  },
  "message": "실행 중인 실험 작업 조회 성공"
}
```

**Response (200) - 실행 중인 작업 없음**:
```json
{
  "job_id": null,
  "status": null,
  "job_type": null,
  "target_type": null,
  "target_id": null,
  "progress": null,
  "current_step": null,
  "error_message": null,
  "request_payload": null,
  "result_payload": null,
  "message": "실행 중인 실험 작업이 없습니다."
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 422 | `VALIDATION_ERROR` | "유효하지 않은 쿼리 파라미터입니다." | 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

### 31. 채용공고 RAG 실험 활성 작업 상세 조회

**Method**: `GET`

**URL**: `/api/v1/job-postings/experiment-jobs/{job_id}`

**Description**: 채용공고 RAG 실험 작업의 상태를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `job_id` (integer, required): 작업 ID

**Response (200)**:
```json
{
  "job_id": 1001,
  "status": "COMPLETED",
  "job_type": "RAG_EXPERIMENT",
  "target_type": "EXPERIMENT_RUN",
  "target_id": 1,
  "progress": 100,
  "current_step": "COMPLETED",
  "error_message": null,
  "request_payload": {
    "run_id": 1,
    "dataset_name": "job_posting_risk_50"
  },
  "result_payload": {
    "completed_cases": 50,
    "total_cases": 50,
    "retrieval_recall_at_5": 0.92,
    "macro_f1": 0.87,
    "avg_latency_ms": 1250
  },
  "message": "실험 작업 상태 조회 성공"
}
```

**에러 응답**:

| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
|---------|---------|------|---------|
| 404 | `JOB_NOT_FOUND` | "존재하지 않는 작업입니다." | 존재하지 않는 작업 ID |
| 401 | `UNAUTHORIZED` | "인증이 필요합니다." | 유효하지 않은 토큰 |

---

## 참고 코드

### 작업 상태 (Job Status)

| 상태 코드 | 설명 |
|---------|------|
| `PENDING` | 작업 대기 중 |
| `PROCESSING` | 작업 실행 중 |
| `COMPLETED` | 작업 완료 |
| `FAILED` | 작업 실패 |
| `CANCELLED` | 작업 취소됨 |

### 분석 유형 (Analysis Type)

| 유형 | 설명 |
|------|------|
| `FULL` | 전체 분석 (컴플라이언스 + 위법성 검토) |
| `QUICK` | 빠른 분석 (기본 컴플라이언스만) |
| `DETAILED` | 상세 분석 (심층 법률 검토 포함) |

### 위반 심각도 (Violation Severity)

| 심각도 | 설명 |
|--------|------|
| `LOW` | 낮음 - 권장사항 수준 |
| `MEDIUM` | 중간 - 수정 권장 |
| `HIGH` | 높음 - 즉시 수정 필요 |
| `CRITICAL` | 심각 - 법적 리스크 매우 높음 |

### 위반 유형 (Violation Type)

| 유형 | 설명 |
|------|------|
| `AGE_DISCRIMINATION` | 연령 차별 |
| `GENDER_DISCRIMINATION` | 성별 차별 |
| `DISABILITY_DISCRIMINATION` | 장애 차별 |
| `APPEARANCE_DISCRIMINATION` | 외모 차별 |
| `REGIONAL_DISCRIMINATION` | 지역 차별 |
| `MARRIAGE_DISCRIMINATION` | 혼인 여부 차별 |
| `EDUCATION_DISCRIMINATION` | 학력 차별 |
| `MINOR_ISSUE` | 기타 경미한 이슈 |

### 실험 유형 (Experiment Type)

| 유형 | 설명 |
|------|------|
| `RAG_EVAL` | RAG 검색 성능 평가 |
| `COMPLIANCE_EVAL` | 컴플라이언스 분석 정확도 평가 |
| `LATENCY_TEST` | 응답 시간 성능 테스트 |
| `A_B_TEST` | A/B 테스트 비교 실험 |

### 실험 상태 (Experiment Status)

| 상태 | 설명 |
|------|------|
| `PENDING` | 실험 대기 중 |
| `RUNNING` | 실험 실행 중 |
| `COMPLETED` | 실험 완료 |
| `FAILED` | 실험 실패 |
| `CANCELLED` | 실험 취소됨 |

### 케이스 결과 상태 (Case Result Status)

| 상태 | 설명 |
|------|------|
| `PASSED` | 테스트 통과 |
| `FAILED` | 테스트 실패 |
| `ERROR` | 실행 오류 |
| `SKIPPED` | 건너뜀 |