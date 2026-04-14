# 📄 HR Copilot BS — 테이블 정의서 (Audit 컬럼 통합본)

> PostgreSQL 14.22 기준
> 

---

## 0. 공통 컬럼 정의

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 등록 일시 |
| Audit | created_by | INTEGER | - | NULL | 등록자 ID → [manager.id](http://manager.id/) |
| Audit | deleted_at | TIMESTAMPTZ | - | NULL | 삭제 일시 |
| Audit | deleted_by | INTEGER | - | NULL | 삭제자 ID → [manager.id](http://manager.id/) |

---

## 1. 계정 영역

### 1.0 manager (슈퍼 관리자)

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 관리자 식별자 |
| 일반 | login_id | VARCHAR(100) | ✓ | - | 로그인 아이디 (UNIQUE) |
| 일반 | password | VARCHAR(255) | ✓ | - | BCrypt 비밀번호 |
| 일반 | name | VARCHAR(100) | ✓ | - | 이름 |
| 일반 | email | VARCHAR(255) | ✓ | - | 이메일 |
| 일반 | last_login_at | TIMESTAMPTZ | - | NULL | 마지막 로그인 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 등록일 |
| Audit | created_by | INTEGER | - | NULL | 생성자 |
| Audit | deleted_at | TIMESTAMPTZ | - | NULL | 삭제일 |
| Audit | deleted_by | INTEGER | - | NULL | 삭제자 |

---

### 1.1 user (서비스 사용자)

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 사용자 ID |
| 일반 | login_id | VARCHAR(100) | ✓ | - | 로그인 ID |
| 일반 | password | VARCHAR(255) | ✓ | - | 비밀번호 |
| 일반 | name | VARCHAR(100) | ✓ | - | 이름 |
| 일반 | email | VARCHAR(100) | ✓ | - | 이메일 |
| 일반 | status | VARCHAR(20) | ✓ | ACTIVE | 상태 |
| 일반 | request_status  | VARCHAR(20)  | - | REQUESTED | 요청 상태 (REQUESTED / APPROVED / REJECTED / ACTIVE) |
| 일반 | request_note  | TEXT  | - | NULL | 계정 생성 요청 사유 |
| 일반 | requested_by_name | VARCHAR(100) | - | NULL | 계정 생성을 요청한 사람 이름 |
| 일반 | requested_by_email  | VARCHAR(255) | - | NULL | 계정 생성을 요청한 사람 이메일 |
| 일반 | role_type | VARCHAR(50) | ✓ | NULL | 사용자 권한 유형 (HR_MANAGER 등) |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |
| Audit | created_by | INTEGER | - | NULL | 생성자 |
| Audit | deleted_at | TIMESTAMPTZ | - | NULL | 삭제일 |
| Audit | deleted_by | INTEGER | - | NULL | 삭제자 |

---

## 2. 문서 관리

### 2.1 document

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 문서 ID |
| 일반 | document_type | VARCHAR(30) | ✓ | - | RESUME / PORTFOLIO |
| 일반 | title | VARCHAR(255) | ✓ | - | 제목 |
| 일반 | file_path | VARCHAR(500) | ✓ | - | 파일 경로 |
| FK | candidate_id | INTEGER | ✓ | - | 지원자 |
| 일반 | extracted_text | TEXT | - | NULL | 추출 텍스트 |
| 일반 | extract_status | VARCHAR(20) | ✓ | PENDING | 상태 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |
| Audit | created_by | INTEGER | - | NULL | 생성자 |
| Audit | deleted_at | TIMESTAMPTZ | - | NULL | 삭제일 |
| Audit | deleted_by | INTEGER | - | NULL | 삭제자 |

---

## 3. 프롬프트 관리

### 3.1 prompt_profile

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | ID |
| 일반 | profile_key | VARCHAR(100) | ✓ | - | UNIQUE KEY |
| 일반 | strategy_type | VARCHAR(50) | ✓ | - | 전략 |
| 일반 | output_schema | TEXT | - | NULL | 출력 스키마 |
| 일반 | is_active | CHAR(1) | ✓ | Y | 활성 여부 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |
| Audit | created_by | INTEGER | - | NULL | 생성자 |
| Audit | deleted_at | TIMESTAMPTZ | - | NULL | 삭제일 |
| Audit | deleted_by | INTEGER | - | NULL | 삭제자 |

---

## 4. 면접 & 로그

### 4.1 interview_question_item

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 질문 ID |
| 일반 | category | VARCHAR(50) | ✓ | - | 유형 |
| 일반 | question_text | TEXT | ✓ | - | 질문 |
| 일반 | expected_answer | TEXT | - | NULL | 기대 답변 |
| 일반 | difficulty_level | VARCHAR(20) | - | NULL | 난이도 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |
| Audit | created_by | INTEGER | - | NULL | 생성자 |

---

### 4.2 llm_call_log

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 로그 ID |
| FK | workflow_run_id | INTEGER | ✓ | - | 실행 ID |
| 일반 | model_name | VARCHAR(100) | ✓ | - | 모델 |
| 일반 | response_json | JSONB | - | NULL | 응답 |
| 일반 | total_tokens | INTEGER | - | NULL | 토큰 |
| 일반 | cost_amount | NUMERIC | - | NULL | 비용 |
| 일반 | call_status | VARCHAR(20) | ✓ | - | 상태 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |

---

## 5. 지원자

### 5.1 candidate

| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- | --- |
| PK | id | SERIAL | ✓ | AUTO | 지원자 ID |
| 일반 | name | VARCHAR(100) | ✓ | - | 이름 |
| 일반 | email | VARCHAR(255) | ✓ | - | 이메일 |
| 일반 | phone | VARCHAR(50) | ✓ | - | 전화 |
| 일반 | birth_date | DATE | - | NULL | 생일 |
| 일반 | apply_status | VARCHAR(30) | ✓ | APPLIED | 상태 |
| FK | resume_doc_id | INTEGER | - | NULL | 이력서 |
| FK | portfolio_doc_id | INTEGER | - | NULL | 포폴 |
| Audit | created_at | TIMESTAMPTZ | ✓ | NOW() | 생성일 |