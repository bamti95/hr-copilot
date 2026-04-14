# HR Copilot BS — 테이블 정의서 (Audit 컬럼 통합본)

> PostgreSQL 15+ 기준 | 네이밍 표준 v2 적용 

---

## 1. 관리자 CMS 영역

### 1.1 `manager` — 관리자 계정
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | 관리자 식별자 |
| 일반 | `login_id` | VARCHAR(100) | ✓ | — | 로그인 아이디 (UNIQUE) |
| 일반 | `password` | VARCHAR(255) | ✓ | — | BCrypt 해시 비밀번호 |
| 일반 | `name` | VARCHAR(100) | ✓ | — | 이름 |
| 일반 | `status` | VARCHAR(20) | ✓ | 'ACTIVE' | 계정 상태: ACTIVE / INACTIVE / LOCK |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 등록 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 등록자 ID → manager.id |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID → manager.id |
| Boolean| `is_deleted` | CHAR(1) | ✓ | 'N' | Soft delete 여부 (Y/N) |

---

## 2. 문서 관리 영역

### 2.1 `document` — 업로드 문서
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | 문서 식별자 |
| 일반 | `document_type` | VARCHAR(30) | ✓ | — | ROLE_PROFILE / RESUME / PORTFOLIO |
| 일반 | `title` | VARCHAR(255) | ✓ | — | 문서 제목 |
| 일반 | `file_path` | VARCHAR(500) | ✓ | — | 서버 저장 경로 |
| FK | `candidate_id` | INTEGER | ✓ | — | 어떤지원자의 문서인가 |
| 일반 | `extracted_text`| TEXT | — | NULL | OCR / 파서 추출 텍스트 전문 |
| 일반 | `extract_status` | VARCHAR(20) | ✓ | 'PENDING' | PENDING / READY / FAILED |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 등록 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 업로드 관리자 ID → manager.id |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID → manager.id |
| Boolean| `is_deleted` | CHAR(1) | ✓ | 'N' | Soft delete 여부 (Y/N) |

---

## 3. 프롬프트 관리 영역

### 3.1 `prompt_profile` — 프롬프트 실행 전략 프로파일
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | 프롬프트 프로파일 식별자 |
| 일반 | `profile_key` | VARCHAR(100) | ✓ | — | 고유 키 (UNIQUE) |
| 일반 | `strategy_type` | VARCHAR(50) | ✓ | — | GENERAL / DEEP_DIVE / RISK_FOCUS |
| 일반 | `output_schema` | TEXT | — | NULL | LLM 출력 JSON 스키마 명세 |
| Boolean| `is_active` | CHAR(1) | ✓ | 'Y' | 활성 여부 (Y/N) |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 등록 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 등록자 ID → manager.id |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID → manager.id |

---

## 4. 면접 및 로그 영역

### 4.1 `interview_question_item` — 면접 질문 개별 항목
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | 질문 항목 식별자 |
| 일반 | `category` | VARCHAR(50) | ✓ | — | COMPETENCY / RISK / EXPERIENCE |
| 일반 | `question_text` | TEXT | ✓ | — | 면접 질문 본문 |
| 일반 | `expected_answer`| TEXT | — | NULL | 기대 답변 |
| 일반 | `difficulty_level`| VARCHAR(20) | — | NULL | EASY / MEDIUM / HARD |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 등록 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 생성자 ID → manager.id |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID → manager.id |

### 4.2 `llm_call_log` — LLM API 호출 로그
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | LLM 호출 로그 식별자 |
| FK | `workflow_run_id`| INTEGER | ✓ | — | 분석 실행 ID → workflow_run.id |
| 일반 | `model_name` | VARCHAR(100) | ✓ | — | 사용 모델명 |
| 일반 | `response_json` | JSONB | — | NULL | 구조화 응답 JSONB |
| 일반 | `total_tokens` | INTEGER | — | NULL | 총 토큰 수 |
| 일반 | `cost_amount` | NUMERIC(12,6) | — | NULL | 호출 비용 (USD) |
| 일반 | `call_status` | VARCHAR(20) | ✓ | — | SUCCESS / FAIL |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 생성 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 시스템/관리자 ID |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID |

---

## 5. 지원자 관리 영역

### 5.1 `candidate` — 지원자 기본 정보
| 구분 | 컬럼명 | 타입 | NOT NULL | 기본값 | 설명 |
|:---|:---|:---|:---:|:---|:---|
| PK | `id` | SERIAL | ✓ | AUTO | 지원자 식별자 |
| 일반 | `name` | VARCHAR(100) | ✓ | — | 지원자 성명 |
| 일반 | `email` | VARCHAR(255) | ✓ | — | 이메일 주소 (UNIQUE) |
| 일반 | `phone` | VARCHAR(50) | ✓ | — | 연락처 |
| 일반 | `birth_date` | DATE | — | NULL | 생년월일 |
| 일반 | `apply_status` | VARCHAR(30) | ✓ | 'APPLIED' | 지원 상태 |
| FK | `resume_doc_id` | INTEGER | — | NULL | 대표 이력서 문서 ID → document.id |
| FK | `portfolio_doc_id`| INTEGER | — | NULL | 대표 포트폴리오 문서 ID → document.id |
| Audit | `created_at` | TIMESTAMPTZ | ✓ | NOW() | 지원 일시 |
| Audit | `created_by` | INTEGER | — | NULL | 등록 주체 ID |
| Audit | `deleted_at` | TIMESTAMPTZ | — | NULL | 삭제 일시 |
| Audit | `deleted_by` | INTEGER | — | NULL | 삭제자 ID |
| Boolean| `is_deleted` | CHAR(1) | ✓ | 'N' | 데이터 삭제 여부 (Y/N) |