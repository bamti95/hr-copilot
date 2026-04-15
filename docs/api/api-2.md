## 2. 관리자 관리 (Manager)

### 2.1 관리자 목록 조회

**Endpoint**: `GET /managers`

**설명**: 등록된 전체 관리자 목록을 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `page` (integer, optional): 페이지 번호 (기본값: 1)
- `limit` (integer, optional): 페이지당 항목 수 (기본값: 20)
- `status` (string, optional): 상태 필터 (ACTIVE, INACTIVE)
- `role_type` (string, optional): 권한 필터

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "managers": [
      {
        "id": 1,
        "login_id": "admin@example.com",
        "name": "홍길동",
        "email": "admin@example.com",
        "status": "ACTIVE",
        "role_type": "HR_MANAGER",
        "created_at": "2025-01-15T10:30:00Z",
        "created_by": null
      },
      {
        "id": 2,
        "login_id": "manager01",
        "name": "김철수",
        "email": "manager01@example.com",
        "status": "ACTIVE",
        "role_type": "HR_MANAGER",
        "created_at": "2025-02-01T14:20:00Z",
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
  "message": "관리자 목록 조회 성공"
}
```

---

### 2.2 관리자 상세 조회

**Endpoint**: `GET /managers/{id}`

**설명**: 특정 관리자의 상세 정보를 조회합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "admin@example.com",
    "name": "홍길동",
    "email": "admin@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-01-15T10:30:00Z",
    "created_by": null,
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "관리자 조회 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |

---

### 2.3 관리자 생성

**Endpoint**: `POST /managers`

**설명**: 새로운 관리자 계정을 생성합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "login_id": "newmanager",
  "password": "SecurePassword123!",
  "name": "이영희",
  "email": "newmanager@example.com",
  "role_type": "HR_MANAGER"
}
```

**Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "login_id": "newmanager",
    "name": "이영희",
    "email": "newmanager@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-04-15T09:15:00Z",
    "created_by": 1
  },
  "message": "관리자 생성 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **400** | `DUPLICATE_LOGIN_ID` | "이미 존재하는 로그인 ID입니다." | 중복된 login_id로 등록 시도 시 |
| **400** | `INVALID_PASSWORD` | "비밀번호는 8자 이상이어야 합니다." | 비밀번호 형식 미달 시 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

---

### 2.4 관리자 수정

**Endpoint**: `PUT /managers/{id}`

**설명**: 관리자 정보를 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Request Body**:
```json
{
  "name": "이영희",
  "email": "updated@example.com",
  "role_type": "HR_MANAGER"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "login_id": "newmanager",
    "name": "이영희",
    "email": "updated@example.com",
    "status": "ACTIVE",
    "role_type": "HR_MANAGER",
    "created_at": "2025-04-15T09:15:00Z",
    "created_by": 1
  },
  "message": "관리자 정보 수정 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |
| **400** | `INVALID_EMAIL` | "유효하지 않은 이메일 형식입니다." | 이메일 형식 오류 시 |

---

### 2.5 관리자 상태 변경

**Endpoint**: `PATCH /managers/{id}/status`

**설명**: 관리자 계정의 활성/비활성 상태를 변경합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Request Body**:
```json
{
  "status": "INACTIVE"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "status": "INACTIVE"
  },
  "message": "관리자 상태 변경 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |
| **400** | `INVALID_STATUS` | "유효하지 않은 상태값입니다." | 잘못된 status 값일 때 |

---

### 2.6 관리자 삭제 (논리 삭제)

**Endpoint**: `DELETE /managers/{id}`

**설명**: 관리자를 논리 삭제합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Path Parameters**:
- `id` (integer, required): 관리자 ID

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 3,
    "deleted_at": "2025-04-15T10:30:00Z",
    "deleted_by": 1
  },
  "message": "관리자 삭제 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **404** | `MANAGER_NOT_FOUND` | "존재하지 않는 관리자입니다." | 존재하지 않는 관리자 ID일 때 |