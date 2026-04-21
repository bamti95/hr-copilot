## 1. 인증 (Authentication)

### 1.1 로그인

**Endpoint**: `POST /auth/login`

**설명**: 관리자 계정으로 로그인하여 JWT 토큰을 발급받습니다.

**Request Body**:
```json
{
  "login_id": "admin@example.com",
  "password": "password123"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "manager": {
      "id": 1,
      "login_id": "admin@example.com",
      "name": "홍길동",
      "email": "admin@example.com",
      "role_type": "HR_MANAGER",
      "status": "ACTIVE"
    }
  },
  "message": "로그인 성공"
}
```

#### 에러 응답 (Error Response)
| 상태 코드 | 에러 코드 | 메시지 | 발생 상황 |
| :--- | :--- | :--- | :--- |
| **401** | `INVALID_CREDENTIALS` | "로그인 정보가 일치하지 않습니다." | login_id 또는 password 불일치 시 |
| **403** | `ACCOUNT_INACTIVE` | "비활성화된 계정입니다." | status가 INACTIVE일 때 |

---

### 1.2 로그아웃

**Endpoint**: `POST /auth/logout`

**설명**: 현재 세션을 종료합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200)**:
```json
{
  "success": true,
  "message": "로그아웃 성공"
}
```

---

### 1.3 토큰 갱신

**Endpoint**: `POST /auth/refresh`

**설명**: 만료된 토큰을 갱신합니다.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "message": "토큰 갱신 성공"
}
```