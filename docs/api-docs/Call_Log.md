## 8. LLM 호출 로그 (LLM Call Log)

### 8.1 세션별 LLM 호출 로그 목록 조회

**Endpoint**: `GET /llm-logs/interview-sessions/{session_id}`

**설명**: 특정 면접 세션의 LLM API 호출 이력을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `session_id` (integer, required): 면접 세션 ID

**Response (200)**:
```json
{
  "sessionId": 123,
  "traceId": "trace-abc-123",
  "items": [
    {
      "id": 1,
      "managerId": 10,
      "candidateId": 50,
      "documentId": 20,
      "promptProfileId": 5,
      "interviewSessionsId": 123,
      "modelName": "gpt-4",
      "nodeName": "questioner",
      "runId": "run-xyz-456",
      "parentRunId": "parent-run-abc-789",
      "traceId": "trace-abc-123",
      "runType": "chain",
      "executionOrder": 1,
      "requestJson": {
        "messages": [
          {
            "role": "user",
            "content": "Generate interview questions"
          }
        ]
      },
      "outputJson": {
        "questions": [
          {
            "category": "TECHNICAL",
            "question_text": "RESTful API 설계 원칙에 대해 설명해주세요."
          }
        ]
      },
      "responseJson": {
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "created": 1714905600,
        "model": "gpt-4-0613"
      },
      "inputTokens": 1500,
      "outputTokens": 2000,
      "totalTokens": 3500,
      "estimatedCost": "0.105",
      "currency": "USD",
      "elapsedMs": 4500,
      "costAmount": "0.105",
      "callStatus": "SUCCESS",
      "errorMessage": null,
      "callTime": 4500,
      "startedAt": "2025-04-05T10:30:00Z",
      "endedAt": "2025-04-05T10:30:04.5Z",
      "createdAt": "2025-04-05T10:30:05Z"
    }
  ]
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |
| **422** | `VALIDATION_ERROR` | "유효성 검사 실패" | 잘못된 파라미터 형식일 때 |

---

### 8.2 세션 내 특정 노드 LLM 호출 로그 조회

**Endpoint**: `GET /llm-logs/interview-sessions/{session_id}/nodes/{node_name}`

**설명**: 특정 면접 세션 내 특정 노드(Questioner, Predictor, Driller 등)의 LLM 호출 이력을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `session_id` (integer, required): 면접 세션 ID
- `node_name` (string, required): 노드 이름 (예: questioner, predictor, driller, reviewer, scorer)

**Response (200)**:
```json
{
  "sessionId": 123,
  "traceId": "trace-abc-123",
  "items": [
    {
      "id": 2,
      "managerId": 10,
      "candidateId": 50,
      "documentId": 20,
      "promptProfileId": 5,
      "interviewSessionsId": 123,
      "modelName": "gpt-4",
      "nodeName": "driller",
      "runId": "run-driller-001",
      "parentRunId": "parent-run-abc-789",
      "traceId": "trace-abc-123",
      "runType": "chain",
      "executionOrder": 3,
      "requestJson": {
        "messages": [
          {
            "role": "system",
            "content": "You are a technical interviewer..."
          },
          {
            "role": "user",
            "content": "Generate follow-up questions"
          }
        ]
      },
      "outputJson": {
        "follow_up_questions": [
          {
            "question_text": "그렇다면 RESTful API에서 멱등성은 어떻게 보장하나요?",
            "depth_level": 2
          }
        ]
      },
      "responseJson": {
        "id": "chatcmpl-def456",
        "object": "chat.completion",
        "created": 1714905620
      },
      "inputTokens": 1800,
      "outputTokens": 1200,
      "totalTokens": 3000,
      "estimatedCost": "0.090",
      "currency": "USD",
      "elapsedMs": 3800,
      "costAmount": "0.090",
      "callStatus": "SUCCESS",
      "errorMessage": null,
      "callTime": 3800,
      "startedAt": "2025-04-05T10:30:20Z",
      "endedAt": "2025-04-05T10:30:23.8Z",
      "createdAt": "2025-04-05T10:30:24Z"
    }
  ]
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |
| **404** | `NODE_NOT_FOUND` | "해당 노드의 로그를 찾을 수 없습니다." | 존재하지 않는 노드 이름일 때 |
| **422** | `VALIDATION_ERROR` | "유효성 검사 실패" | 잘못된 파라미터 형식일 때 |

---

### 8.3 LLM 호출 로그 상세 조회

**Endpoint**: `GET /llm-logs/interview-sessions/{session_id}/logs/{log_id}`

**설명**: 특정 LLM 호출의 상세 로그를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `session_id` (integer, required): 면접 세션 ID
- `log_id` (integer, required): LLM 호출 로그 ID

**Response (200)**:
```json
{
  "id": 1,
  "managerId": 10,
  "candidateId": 50,
  "documentId": 20,
  "promptProfileId": 5,
  "interviewSessionsId": 123,
  "modelName": "gpt-4",
  "nodeName": "questioner",
  "runId": "run-xyz-456",
  "parentRunId": "parent-run-abc-789",
  "traceId": "trace-abc-123",
  "runType": "chain",
  "executionOrder": 1,
  "requestJson": {
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are an expert technical interviewer..."
      },
      {
        "role": "user",
        "content": "Based on the candidate's resume, generate 5 technical questions."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "outputJson": {
    "questions": [
      {
        "category": "TECHNICAL",
        "question_text": "RESTful API 설계 원칙에 대해 설명해주세요.",
        "expected_answer": "REST는 Representational State Transfer의 약자로...",
        "evaluation_guide": "HTTP 메서드 활용, 상태 코드, URI 설계 등을 언급하는지 확인"
      },
      {
        "category": "TECHNICAL",
        "question_text": "데이터베이스 인덱스의 동작 원리를 설명해주세요.",
        "expected_answer": "인덱스는 B-Tree 또는 Hash 구조로...",
        "evaluation_guide": "B-Tree 구조, 조회 성능 향상, 쓰기 성능 트레이드오프 이해도 평가"
      }
    ],
    "metadata": {
      "resume_analysis": "Backend developer with 3 years experience",
      "difficulty_level": "intermediate"
    }
  },
  "responseJson": {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1714905600,
    "model": "gpt-4-0613",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "{\"questions\": [...]}"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 1500,
      "completion_tokens": 2000,
      "total_tokens": 3500
    }
  },
  "inputTokens": 1500,
  "outputTokens": 2000,
  "totalTokens": 3500,
  "estimatedCost": "0.105",
  "currency": "USD",
  "elapsedMs": 4500,
  "costAmount": "0.105",
  "callStatus": "SUCCESS",
  "errorMessage": null,
  "callTime": 4500,
  "startedAt": "2025-04-05T10:30:00Z",
  "endedAt": "2025-04-05T10:30:04.5Z",
  "createdAt": "2025-04-05T10:30:05Z"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `LOG_NOT_FOUND` | "LLM 호출 로그를 찾을 수 없습니다." | 존재하지 않는 로그 ID일 때 |
| **404** | `SESSION_NOT_FOUND` | "면접 세션을 찾을 수 없습니다." | 존재하지 않는 세션 ID일 때 |
| **422** | `VALIDATION_ERROR` | "유효성 검사 실패" | 잘못된 파라미터 형식일 때 |

---
