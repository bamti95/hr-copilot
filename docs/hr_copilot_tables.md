# HR Copilot MVP - 최종 테이블 목록 및 역할 정의

---

## 1. 개요

본 문서는 **RAG 기반 채용 면접 질문 자동생성 HR Copilot** 프로젝트의  
MVP 기준 데이터베이스 테이블 구조와 각 테이블의 역할을 정의한다.

### 설계 원칙
- PostgreSQL 단일 DB 사용
- pgvector 확장 사용 (임베딩 저장)
- 정형 데이터 + 비정형(임베딩) 데이터 통합 관리
- 멀티테넌트(site_key)는 MVP에서 제외
- CMS 관리자 구조 포함
- AI 로그 및 통계 필수 포함

---

## 2. 전체 도메인 구성

테이블은 다음 6개 영역으로 구성된다.

1. 관리자(CMS)
2. 채용/HR
3. 문서 관리
4. 프롬프트/워크플로우
5. 질문 결과
6. AI 로그/통계

---

## 3. 관리자(CMS) 영역

### 3.1 admin
관리자 계정 정보

**역할**
- 관리자 로그인 및 인증
- 시스템 접근 주체

**주요 컬럼**
- id (PK)
- login_id
- password
- name
- email
- group_id (FK)
- status
- last_login_at

---

### 3.2 admin_group
관리자 권한 그룹

**역할**
- 관리자 권한 분류
- 역할 기반 접근 제어(RBAC)

---

### 3.3 adm_menu
관리자 메뉴

**역할**
- 관리자 UI 메뉴 구조 정의
- LNB 구성

---

### 3.4 admin_group_menu
권한 그룹별 메뉴 접근 권한

**역할**
- 메뉴 접근 제어
- read/write/delete 권한 관리

---

### 3.5 admin_access_log
관리자 활동 로그

**역할**
- 로그인/작업 이력 기록
- 감사 로그

---

## 4. 채용/HR 영역

### 4.1 job_posting
채용공고

**역할**
- JD 저장
- 면접 기준 데이터

---

### 4.2 candidate
지원자 정보

**역할**
- 지원자 기본 정보 관리

---

### 4.3 candidate_application
지원서

**역할**
- 지원자와 채용공고 연결
- 지원 상태 관리

---

## 5. 문서 관리 영역

### 5.1 document
문서 메타

**역할**
- 업로드된 파일 정보 관리
- 문서 타입 구분 (이력서, 포트폴리오 등)

---

### 5.2 document_chunk
문서 청크 + 임베딩

**역할**
- RAG 검색 핵심 테이블
- 청크 텍스트 + embedding 저장

**특징**
- pgvector 사용 (1536 차원)
- 유사도 검색 수행

---

### 5.3 document_job
문서 처리 작업

**역할**
- 문서 파싱 / 청킹 / 임베딩 상태 관리
- 비동기 작업 추적

---

## 6. 프롬프트 / 워크플로우 영역

### 6.1 prompt_template
프롬프트 원문

**역할**
- LLM 입력 템플릿 관리
- system/user prompt 저장

---

### 6.2 prompt_profile
프롬프트 실행 설정

**역할**
- 질문 생성 방식 정의
- 템플릿 + 옵션 묶음

**예시 역할**
- 질문 개수
- 난이도
- 스타일
- temperature 등

---

### 6.3 workflow_run
실행 이력

**역할**
- 질문 생성 요청 단위 기록
- 실행 상태 추적

---

### 6.4 workflow_step_result
단계별 결과

**역할**
- RAG 각 단계 결과 저장
- 디버깅 및 분석 가능

---

## 7. 질문 결과 영역

### 7.1 interview_question_set
질문 세트

**역할**
- 전체 결과 묶음
- 요약 / 리스크 포함

---

### 7.2 interview_question_item
질문 상세

**역할**
- 개별 질문 저장
- 질문 근거 포함

---

## 8. AI 로그 / 통계 영역

### 8.1 llm_call_log ⭐ 핵심

**역할**
- LLM 호출 로그 저장
- 통계/대시보드 핵심 데이터

**저장 정보**
- 성공/실패
- 응답 시간
- 토큰 사용량
- 비용

---

### 8.2 chat_query_log

**역할**
- 사용자 질문 로그
- TOP 질문 통계

---

### 8.3 (선택) usage_daily_stats

**역할**
- 일별 집계
- 성능 최적화용

---

## 9. 핵심 관계 요약

- candidate → candidate_application → job_posting
- document → document_chunk
- workflow_run → workflow_step_result
- workflow_run → interview_question_set → interview_question_item
- workflow_run → llm_call_log

---

## 10. 핵심 설계 포인트

### 1. DB는 하나
- PostgreSQL 단일 DB
- pgvector 포함

### 2. 문서 중심 구조
- document → chunk → embedding

### 3. 프롬프트 분리
- template (문장)
- profile (설정)

### 4. 로그 기반 통계
- llm_call_log 중심
- 모든 지표 산출 가능

---

## 11. 결론

본 구조는 단순 CRUD 시스템이 아닌

**“AI + RAG + CMS + 운영 대시보드가 결합된 실무형 시스템”**

을 목표로 설계되었다.

MVP 단계에서도 충분히 확장 가능한 구조이며,
향후 멀티테넌트 및 고도화에도 대응 가능하다.
