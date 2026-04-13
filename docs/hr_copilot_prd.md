# 📄 HR Copilot BS

## 요구사항 정의서 (MVP 1단계 + 확장 고려)

---

## 1. 개요

### 1.1 목적

본 문서는 HR Copilot BS 시스템의 요구사항을 정의하며,
관리자 CMS 구조를 포함한 AI 기반 면접 설계 시스템 구현 기준을 제공한다.

---

### 1.2 시스템 정의

> **데이터를 해석하여 면접 전략을 설계하고, 향후 RAG 기반 확장까지 고려한 AI 채용 의사결정 시스템**

---

## 2. 시스템 구성

### 2.1 주요 영역

1. 관리자(CMS) 영역
2. 채용/문서 관리 영역
3. LLM 분석 및 전략 생성 영역
4. 결과 관리 영역
5. 로그/통계 영역
6. (확장) RAG 처리 영역

---

## 3. 공통 관리자(CMS) 요구사항 ⭐

👉 **모든 기능의 기반 (필수 공통 모듈)**

---

### 3.1 관리자 계정 관리

#### FR-ADM-01 관리자 생성

* 관리자는 계정을 생성할 수 있어야 한다.

#### FR-ADM-02 관리자 인증

* JWT 기반 인증을 지원해야 한다.

#### FR-ADM-03 관리자 상태 관리

* ACTIVE / INACTIVE / LOCK 상태 관리 가능해야 한다.

---

### 3.2 관리자 권한 그룹

#### FR-ADM-04 권한 그룹 생성

* 관리자는 권한 그룹을 생성할 수 있어야 한다.

#### FR-ADM-05 권한 매핑

* 그룹별 메뉴 접근 권한을 설정할 수 있어야 한다.

---

### 3.3 관리자 메뉴 관리

#### FR-ADM-06 메뉴 생성

* 메뉴는 트리 구조로 생성 가능해야 한다.

#### FR-ADM-07 메뉴 구조

* parent-child 관계 지원
* depth 기반 계층 구조

#### FR-ADM-08 메뉴 정보

* menu_name
* menu_key (고유)
* menu_path
* sort_no

---

### 3.4 메뉴 권한 제어

#### FR-ADM-09 접근 권한

* read / write / delete 권한 분리

#### FR-ADM-10 권한 검증

* API 호출 시 메뉴 권한 검증 필수

---

### 3.5 관리자 로그

#### FR-ADM-11 접근 로그

* 로그인 / 작업 이력 저장

#### FR-ADM-12 로그 항목

* action_type
* target
* result
* ip / user_agent

---

## 4. 핵심 기능 요구사항 (LLM 중심)

---

### 4.1 문서 관리

#### FR-01 문서 업로드

* Role Profile / Resume / Portfolio 업로드

#### FR-02 텍스트 추출

* PDF, DOCX 지원

#### FR-03 문서 저장

* 원본 + 텍스트 저장

---

### 4.2 프롬프트 관리

#### FR-04 Template 관리

* 생성 / 수정 / 삭제

#### FR-05 Profile 관리

* 템플릿 조합 및 전략 정의

---

### 4.3 프롬프트 조립 엔진 ⭐

#### FR-06 조립 로직

* Template + Profile 기반 조립

#### FR-07 데이터 주입

* role_profile / candidate_profile 삽입

#### FR-08 출력 구조 강제

* JSON 구조 반환 필수

---

### 4.4 LLM 분석 및 전략 생성

#### FR-09 분석 실행

* 문서 기반 LLM 분석 수행

#### FR-10 생성 항목

* 핵심 역량
* 검증 포인트
* 리스크 요소
* 면접 질문
* 질문 근거
* 기대 답변

---

### 4.5 결과 관리

#### FR-11 질문 세트 저장

* interview_question_set 저장

#### FR-12 질문 상세 저장

* interview_question_item 저장

---

### 4.6 로그 및 통계

#### FR-13 LLM 로그 저장

* 요청/응답 기록

#### FR-14 비용 추적

* 토큰 사용량
* latency
* cost

---

## 5. 데이터 구조

---

### 5.1 관리자 영역

* admin
* admin_group
* adm_menu
* admin_group_menu
* admin_access_log

---

### 5.2 핵심 영역

* document
* prompt_template
* prompt_profile
* workflow_run
* interview_question_set
* interview_question_item
* llm_call_log

---

## 6. RAG 확장 고려 요구사항 ⭐

👉 **지금은 미구현, 반드시 구조 포함**

---

### 6.1 문서 청킹

#### FR-RAG-01

* document → chunk 분할 가능 구조 유지

---

### 6.2 임베딩

#### FR-RAG-02

* vector embedding 컬럼 확장 가능해야 함

---

### 6.3 검색

#### FR-RAG-03

* 유사도 검색 기능 확장 가능해야 함

---

### 6.4 워크플로우 확장

#### FR-RAG-04

* retrieve 단계 추가 가능 구조

---

### 6.5 질문 근거 연결

#### FR-RAG-05

* 질문 ↔ chunk 연결 가능 구조

---

## 7. 비기능 요구사항

---

### 7.1 성능

* 응답 시간: 5초 이내

### 7.2 확장성

* RAG, Agent 구조 확장 가능

### 7.3 안정성

* 실패 로그 기록 필수

### 7.4 보안

* 관리자 인증 필수
* 파일 검증 필수

---

## 8. 시스템 흐름

```plaintext
문서 업로드
→ 텍스트 추출
→ Prompt Profile 선택
→ Template 조립
→ LLM 실행
→ 결과 저장
→ 관리자 조회
```

---

## 9. 로드맵

### Phase 1 (MVP)

* LLM 기반 분석

### Phase 2

* Chunk 기반 처리

### Phase 3

* RAG + 비교 분석

---

## 10. 핵심 설계 원칙

---

### 1️⃣ Prompt 중심 설계

→ RAG보다 먼저

### 2️⃣ 구조화된 출력

→ JSON 강제

### 3️⃣ 로그 기반 개선

→ 지속 고도화

### 4️⃣ 확장 가능 아키텍처

→ RAG 자연 확장

---

# 🎯 최종 정의

> **관리자 CMS 기반 위에, Prompt 중심 LLM 실행 구조를 구축하고, 향후 RAG까지 자연스럽게 확장 가능한 AI 면접 설계 시스템**

---
