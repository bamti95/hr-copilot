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