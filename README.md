# 최종 프로젝트 기획안 정리  
## 주제: RAG 기반 채용 면접 질문 자동생성 HR Copilot

---

## 1. 프로젝트 개요

### 1.1 프로젝트명
**RAG 기반 채용 면접 질문 자동생성 HR Copilot**

### 1.2 프로젝트 한 줄 소개
채용 담당자 또는 면접관이 **채용공고(JD), 지원자 이력서, 포트폴리오**를 업로드하면,  
AI가 문서를 분석하여 **핵심 역량 요약, 검증 포인트 추출, 맞춤형 면접 질문 생성, 질문 생성 근거 제시**까지 수행하는 시스템이다.

### 1.3 프로젝트 주제 선정 배경
채용 과정에서는 다음과 같은 문제가 자주 발생한다.

- 지원자 서류를 일일이 검토하는 데 시간이 많이 든다.
- 면접 질문이 면접관 개인 역량에 따라 편차가 크다.
- JD와 지원자 경험 간의 적합도를 빠르게 파악하기 어렵다.
- 생성된 질문이 왜 필요한 질문인지 근거를 정리하기 어렵다.

이 프로젝트는 이러한 문제를 해결하기 위해,  
**LLM + RAG 기반의 문서 이해 및 질문 생성 시스템**을 구축하는 것을 목표로 한다.

### 1.4 타겟층
- 기업 인사담당자(HR)
- 실무 면접관
- 스타트업 채용 담당자
- 다수 지원자를 검토해야 하는 조직

---

## 2. 프로젝트 목표

### 2.1 핵심 목표
- JD, 이력서, 포트폴리오를 기반으로 **맞춤형 면접 질문 자동 생성**
- 생성된 질문에 대해 **문서 근거와 검증 포인트 제공**
- 직무/조직/면접 스타일에 따라 **프롬프트 커스터마이징 가능**
- 정형 데이터와 비정형 문서를 함께 관리할 수 있는 **실무형 AI 시스템 설계**

### 2.2 기대 효과
- 서류 검토 시간 단축
- 면접 준비 시간 단축
- 면접 질문 품질 표준화
- 지원자별 맞춤 질문 제공
- 조직 단위로 재사용 가능한 프롬프트/질문 정책 관리 가능

---

## 3. 핵심 기능 정의

## 3.1 문서 업로드 기반 질문 생성
사용자는 다음 문서를 업로드할 수 있다.

- 채용공고(JD)
- 지원자 이력서
- 포트폴리오
- 필요 시 자기소개서, 경력기술서 등 확장 가능

업로드된 문서는 다음 흐름으로 처리된다.

1. 파일 저장
2. 문서 파싱
3. 텍스트 청킹
4. 임베딩 생성
5. pgvector 저장
6. 질문 생성 시 관련 청크 검색
7. LLM 호출
8. 구조화된 결과 반환

### 3.2 문서 요약 및 분석
AI는 업로드된 문서를 바탕으로 다음 정보를 추출한다.

- 문서 요약
- 핵심 기술 스택
- 주요 프로젝트 경험
- JD 기준 핵심 요구 역량
- 지원자의 강점
- 검증 필요 포인트
- 면접에서 확인해야 할 gap

### 3.3 예상 면접 질문 자동 생성
질문은 단순 생성이 아니라 유형별로 구성한다.

- 인성 질문
- 직무 기술 질문
- 프로젝트 심화 질문
- 협업/문제 해결 질문
- 꼬리 질문

### 3.4 질문 생성 근거 제공
생성된 질문에는 반드시 근거를 함께 제시한다.

예시:
- “이력서에서 Spring Boot 기반 파일 업로드 기능 구현 경험이 언급됨”
- “포트폴리오에서 Redis 캐싱 사용 경험이 있으나 성능 개선 수치가 없음”
- “JD에서 대규모 트래픽 대응 경험이 중요 역량으로 명시됨”

### 3.5 JD-지원자 매칭 분석
AI는 JD와 지원자 문서를 함께 분석하여 다음을 제공한다.

- 요구 역량 목록
- 지원자 보유 역량 목록
- 일치하는 역량
- 부족하거나 검증이 필요한 항목
- 면접 시 중점 확인 포인트

### 3.6 프롬프트 커스터마이징
조직이나 직무에 따라 아래 항목을 설정할 수 있다.

- 질문 스타일
- 난이도
- 질문 개수
- 직무군별 템플릿
- 출력 포맷
- 후속 질문 생성 여부
- 검증 중심 / 인성 중심 / 기술 중심 비율

---

## 4. 차별화 포인트

### 4.1 단순 챗봇이 아닌 HR 특화 AI Copilot
일반적인 챗봇이 아니라, **채용 실무를 돕는 문서 기반 면접 지원 시스템**이라는 점에서 차별화된다.

### 4.2 RAG 기반 문서 이해
JD, 이력서, 포트폴리오를 함께 읽고 검색하여 질문을 생성하므로,  
단순 프롬프트 기반 질문 생성보다 정확도가 높다.

### 4.3 질문 생성 근거 제시
질문만 출력하는 것이 아니라 **문서 내 근거와 검증 목적**을 함께 제공하므로 실무 활용성이 높다.

### 4.4 프롬프트 정책 관리
프롬프트를 하드코딩하지 않고, DB 기반으로 저장/버전 관리하여  
조직별 정책 반영과 재사용이 가능하다.

### 4.5 확장 가능한 워크플로우 구조
LangGraph를 적용해 단계형 AI 실행 흐름을 만들고,  
향후 human-in-the-loop, 질문 재생성, 결과 수정 이력 관리까지 확장 가능하다.

---

## 5. 시스템 전체 흐름

## 5.1 사용자 시나리오
1. 채용 담당자가 JD를 등록한다.
2. 지원자의 이력서 및 포트폴리오를 업로드한다.
3. 시스템이 문서를 파싱하고 청킹/임베딩을 수행한다.
4. 면접 질문 생성 요청을 수행한다.
5. 시스템이 관련 문맥을 검색하고 JD/지원자 간 gap을 분석한다.
6. AI가 구조화된 질문 세트와 생성 근거를 반환한다.
7. 사용자는 질문 결과를 저장하거나 재생성할 수 있다.

## 5.2 백엔드 처리 흐름
1. 파일 업로드 API 호출
2. 파일 저장 및 문서 메타 저장
3. 비동기 ingest 수행
4. 문서 파싱 및 청킹
5. 임베딩 생성 및 pgvector 저장
6. 질문 생성 API 호출
7. retriever 검색
8. LangGraph workflow 실행
9. structured output 생성
10. 결과 저장 및 응답 반환

---

## 6. 기술 구조 설계

## 6.1 프론트엔드 기술 스택
- React (Vite)
- TypeScript (TSX)
- Zustand
- React Router
- Axios
- TanStack Query
- Tailwind CSS 또는 필요 시 UI 라이브러리 혼합

### 6.1.1 상태관리 전략
#### 권장안
- **Zustand + sessionStorage**

#### 이유
- JWT access token 보관 시 localStorage보다 상대적으로 안전성 설명이 용이함
- 브라우저 종료 시 세션 종료로 관리 가능
- 최종 프로젝트 규모에서 구현 난이도와 보안 설명의 균형이 좋음

#### 추천 방식
- access token: sessionStorage
- 사용자 상태: Zustand store
- 서버 데이터 캐시: TanStack Query
- refresh token은 고도화 시 HttpOnly Cookie 구조로 확장 고려

### 6.1.2 프론트 주요 화면 구성
- 로그인
- 대시보드
- JD 관리
- 지원자 관리
- 문서 업로드/목록
- 질문 생성 화면
- 질문 결과 상세
- 프롬프트 설정
- 실행 이력 관리

### 6.1.3 레이아웃 설계
BO(Back Office) 느낌의 관리형 UI로 구성한다.

- Header
- LNB
- Main Content
- Footer

#### LNB 메뉴 예시
- 대시보드
- 공고 관리
- 지원자 관리
- 문서 관리
- 질문 생성
- 프롬프트 관리
- 실행 이력
- 사용자 관리

### 6.1.4 대시보드 구성
대시보드는 메인 진입 화면으로 아래 정보를 제공한다.

- 전체 지원자 수
- 업로드 문서 수
- 질문 생성 건수
- 최근 분석 요청
- 문서 처리 상태
- 직무별 질문 생성 통계
- 최근 실행 이력

### 6.1.5 추천 폴더 구조
```bash
src/
├─ app/
│  ├─ router/
│  └─ providers/
├─ pages/
├─ features/
│  ├─ auth/
│  ├─ dashboard/
│  ├─ document/
│  ├─ interview/
│  ├─ prompt/
│  └─ user/
├─ components/
│  ├─ common/
│  └─ layout/
├─ services/
├─ hooks/
├─ types/
├─ utils/
├─ assets/
├─ App.tsx
└─ main.tsx
```

### 6.1.6 프론트 추가 고려 사항
- 업로드 상태(progress) UI 필요
- 질문 재생성 버튼 제공
- 질문 근거 문장 하이라이트 UI
- 후보자별 비교 화면 확장 가능
- 프롬프트 설정 변경 이력 표시 고려
- 폼 검증 및 에러 메시지 일관성 필요

---

## 6.2 백엔드 기술 스택
- Python
- FastAPI
- SQLAlchemy ORM
- Async/Await 기반 비동기 DB 연결
- PostgreSQL
- pgvector
- Alembic
- Pydantic
- LangChain / LangGraph
- BackgroundTasks 또는 향후 Celery/RQ 확장

### 6.2.1 백엔드 아키텍처
3계층 아키텍처를 적용한다.

- Router
- Service
- Repository

추가적으로 ORM 모델은 `models`에서 관리한다.

### 6.2.2 백엔드 예시 구조
```bash
app/
├─ main.py
├─ core/
├─ api/
│  └─ v1/
│      └─ routers/
├─ services/
├─ repositories/
├─ models/
├─ schemas/
├─ db/
├─ llm/
├─ workers/
├─ utils/
└─ common/
```

### 6.2.3 계층별 역할
#### Router
- 요청/응답 처리
- 입력 검증
- 인증/인가 확인
- HTTP status 관리

#### Service
- 비즈니스 로직
- 문서 처리 흐름 제어
- LLM 호출 orchestration
- workflow 실행
- 트랜잭션 처리

#### Repository
- DB CRUD
- ORM query 관리
- 검색 및 페이징 처리

#### Models
- SQLAlchemy ORM 테이블 정의
- 관계 매핑 관리

#### Schemas
- Pydantic request/response
- structured output 정의

---

## 7. RAG 및 LLM 처리 설계

## 7.1 문서 처리 파이프라인
1. 파일 업로드
2. 파일 저장
3. 문서 파싱
4. 텍스트 정제
5. 청킹
6. 임베딩
7. 벡터 저장
8. 검색
9. LLM 추론
10. 결과 저장

## 7.2 추천 문서 처리 모듈 분리
- parser service
- chunk service
- embedding service
- retriever service
- generation service
- result formatter

## 7.3 질문 생성 시 추천 응답 구조
자유 텍스트보다 구조화된 응답이 좋다.

예시:
```json
{
  "summary": "지원자는 React, Spring Boot 기반의 웹 서비스 구축 경험이 있다.",
  "coreSkills": ["React", "Spring Boot", "MySQL"],
  "projects": [
    {
      "name": "CMS 구축 프로젝트",
      "keywords": ["파일 업로드", "관리자 페이지", "권한 관리"]
    }
  ],
  "riskPoints": [
    "성능 개선 수치가 명확하지 않음"
  ],
  "questions": [
    {
      "type": "직무",
      "question": "Spring Boot에서 파일 업로드를 구현할 때 어떤 보안 포인트를 고려했나요?",
      "reason": "포트폴리오 내 파일 업로드 기능 구현 경험이 언급됨"
    }
  ]
}
```

## 7.4 Structured Output 도입 필요성
LLM 응답을 JSON 스키마 기반으로 고정하면 다음 장점이 있다.

- 프론트 렌더링이 쉬움
- 결과 신뢰성이 높아짐
- DB 저장이 편리함
- 질문/근거/요약을 별도 컬럼으로 관리 가능

따라서 Pydantic 기반 structured output을 적극 도입하는 것이 좋다.

---

## 8. LangGraph State 및 프롬프트 엔지니어링 저장 구조

## 8.1 핵심 정리
LangGraph State 전체를 파이썬 객체 그대로 DB에 저장하는 것보다,  
**실행에 의미 있는 상태값과 중간 결과를 분리 저장하는 방식**이 더 적절하다.

즉, DB에는 다음을 저장하는 구조가 좋다.

- 프롬프트 템플릿
- 프롬프트 프로필
- 실행 이력
- 단계별 결과
- 최종 질문 세트
- 사용 문서/버전 정보

## 8.2 LangGraph State 예시
```python
class InterviewCopilotState(TypedDict):
    session_id: str
    jd_document_id: int | None
    candidate_document_id: int | None
    portfolio_document_id: int | None

    retrieved_chunks: list
    jd_summary: str
    candidate_summary: str
    portfolio_summary: str

    required_skills: list[str]
    candidate_skills: list[str]
    gap_points: list[str]

    question_style: str
    difficulty_level: str
    question_count: int

    generated_questions: list[dict]
    final_result: dict
```

이 구조는 런타임 상태로 사용하고,  
DB에는 이를 아래처럼 나누어 저장하는 방식이 좋다.

## 8.3 저장 추천 대상
### 1) prompt_template
- system prompt
- user prompt
- 출력 포맷
- 버전
- 활성 여부

### 2) prompt_profile
- 질문 스타일
- 난이도
- 질문 개수
- 직무군별 옵션
- 조직별 설정

### 3) workflow_run
- 실행 시작/종료 시간
- 상태
- 사용한 문서 ID
- 사용한 프롬프트 버전
- 오류 여부

### 4) workflow_step_result
- retrieve 결과
- JD 분석 결과
- 지원자 분석 결과
- gap 분석 결과
- 질문 생성 결과

### 5) interview_question_set
- 최종 질문 세트
- 요약
- 리스크 포인트
- 결과 JSON

## 8.4 LangGraph 도입 목적
LangGraph는 단순 유행 기술이 아니라, 아래 목적에 적합하다.

- 단계형 노드 구성
- 처리 흐름 분기
- 실패 복구
- 결과 재생성
- human-in-the-loop 확장
- 실행 이력 추적

## 8.5 LangGraph workflow 예시
1. 입력 검증
2. 문서 메타 조회
3. retriever 실행
4. JD 분석
5. 지원자 분석
6. gap analysis
7. 질문 생성
8. output validation
9. 결과 저장

## 8.6 추가 도입 추천 기술
- Pydantic Structured Output
- BackgroundTasks
- Rerank 로직
- 문서 parser 전략 분리
- 실행 로그 추적(request_id, workflow_run_id 등)
- Alembic migration 관리
- 향후 Redis queue 또는 Celery 도입 가능

---

## 9. DB 설계 방향

## 9.1 PostgreSQL + pgvector 사용 방향
이번 프로젝트는 **PostgreSQL을 메인 DB로 사용**하고,  
문서 청킹 및 임베딩 저장은 **pgvector 확장을 적용한 동일 PostgreSQL 인스턴스**에서 시작하는 것을 추천한다.

### 결론
**MVP 기준으로는 DB를 두 개로 나누지 않고, PostgreSQL 하나에 일반 테이블 + pgvector를 함께 운영하는 구조가 가장 적절하다.**

## 9.2 하나의 DB로 시작하는 이유
- 개발 복잡도 감소
- 운영 단순화
- 데이터 정합성 관리 용이
- 문서 메타와 청크 데이터 연결이 쉬움
- 졸업/최종 프로젝트 범위에 적합

## 9.3 추후 두 개 DB로 분리하는 시점
다음 조건이 생기면 분리를 고려할 수 있다.

- 문서량 증가
- 검색 트래픽 증가
- 벡터 인덱스 최적화 필요
- 운영 DB와 검색 DB 격리 필요
- 고성능 벡터 스토어 전환 필요

## 9.4 발표용 정리 문장
> 본 프로젝트는 MVP 단계에서 운영 복잡도를 줄이기 위해 PostgreSQL 단일 인스턴스에 pgvector를 함께 적용한다.  
> 정형 데이터와 임베딩 데이터를 동일 DB 내에서 관리하여 개발 효율과 데이터 정합성을 확보하고,  
> 추후 문서량 및 검색 트래픽이 증가할 경우 벡터 저장소를 별도 분리하는 확장형 구조를 고려한다.

---

## 10. 파일 저장 전략

## 10.1 권장안
### MVP
- 서버 내부 파일 시스템에 저장
- DB에는 파일 경로(path), 원본 파일명, 저장 파일명, MIME type, size 등만 저장

### 고도화
- AWS S3 Bucket으로 전환
- presigned URL
- 접근 권한 분리
- 저장소 추상화 계층 적용

## 10.2 왜 로컬 저장으로 시작하는가
- 초기 구현이 단순하다
- 인프라 설정 부담이 적다
- 프로젝트 범위 관리가 쉽다

## 10.3 추천 저장소 추상화 구조
```python
class FileStoragePort(Protocol):
    async def save(self, file) -> str: ...
    async def delete(self, path: str) -> None: ...
```

구현체 예시
- LocalFileStorageService
- S3FileStorageService

이렇게 설계하면, MVP 이후에도 로직 변경 없이 저장소만 교체 가능하다.

---

## 11. 추천 DB 테이블 초안

## 11.1 사용자/인증
- user
- auth_token 또는 세션 관련 테이블(선택)

## 11.2 채용 관련
- job_posting
- candidate
- candidate_application

## 11.3 문서 관련
- document
- document_chunk

## 11.4 프롬프트 및 워크플로우 관련
- prompt_template
- prompt_profile
- workflow_run
- workflow_step_result

## 11.5 결과 관련
- interview_question_set
- interview_question_item

## 11.6 document_chunk 테이블 방향
MVP에서는 chunk와 embedding을 한 테이블에 함께 두는 방식이 단순하다.

예시 컬럼:
- id
- document_id
- chunk_index
- content
- embedding (vector)
- token_count
- metadata (jsonb)

---

## 12. 보안 및 운영 고려 사항

## 12.1 인증 방식
- JWT 기반 인증
- 프론트에서는 sessionStorage 저장
- 백엔드에서는 토큰 검증 미들웨어/의존성 구성

## 12.2 파일 업로드 보안
- 파일 확장자 검사
- MIME type 검사
- 업로드 크기 제한
- 저장 파일명 난수화
- 실행 파일 업로드 차단

## 12.3 문서 접근 권한
- 사용자별 접근 통제
- 업로드 문서와 결과에 대한 권한 체크 필요

## 12.4 로그 관리
- request_id
- workflow_run_id
- ingest_id
- 실행 시간
- 예외 로그
- 토큰 사용량

## 12.5 예외 처리
- 문서 파싱 실패
- 임베딩 실패
- 질문 생성 실패
- 프롬프트 포맷 오류
- 파일 저장 실패

---

## 13. 프로젝트 수행 방향 및 구현 전략

## 13.1 1단계: 기반 구축
- React + Vite + TS 프로젝트 세팅
- FastAPI 프로젝트 세팅
- PostgreSQL + pgvector 연동
- JWT 인증 기본 구축
- BO 레이아웃 구성

## 13.2 2단계: 문서 업로드 및 관리
- JD / 이력서 / 포트폴리오 업로드
- 파일 메타 저장
- 문서 목록/상세 조회
- 파일 저장 구조 구축

## 13.3 3단계: RAG 파이프라인 구축
- 문서 파서
- 청킹
- 임베딩
- pgvector 저장
- 검색 API 구현

## 13.4 4단계: 질문 생성 기능 구현
- JD 분석
- 지원자 분석
- gap 도출
- 질문 생성
- structured output 반환

## 13.5 5단계: 프롬프트 관리 및 워크플로우
- prompt_template 관리
- prompt_profile 관리
- LangGraph workflow 적용
- 실행 이력 저장

## 13.6 6단계: 대시보드 및 고도화
- 통계 카드
- 최근 실행 이력
- 처리 상태 시각화
- 질문 재생성
- 향후 S3 전환 가능 구조 정리

---

## 14. WBS 초안

## 14.1 분석 및 기획
- 프로젝트 주제 확정
- 요구사항 정리
- 기능 우선순위 결정
- ERD 및 화면 구조 설계

## 14.2 프론트엔드 개발
- 공통 레이아웃
- 로그인/인증
- 대시보드
- JD/지원자/문서 관리
- 질문 생성/결과 화면
- 프롬프트 관리 화면

## 14.3 백엔드 개발
- 인증 API
- 파일 업로드 API
- 문서 관리 API
- 질문 생성 API
- 프롬프트 관리 API
- 대시보드 통계 API

## 14.4 AI/RAG 개발
- 문서 파싱
- 청킹
- 임베딩 저장
- retriever 구현
- structured output
- LangGraph workflow

## 14.5 테스트 및 보완
- API 테스트
- 파일 업로드 테스트
- RAG 품질 점검
- 질문 품질 검증
- UI/UX 보완

## 14.6 배포 및 시연 준비
- 서버 배포
- DB 마이그레이션
- 시연 데이터 준비
- 발표 자료 정리

---

## 15. 최종 기술 스택 제안

## 15.1 프론트엔드
- React (Vite)
- TypeScript
- Zustand
- TanStack Query
- React Router
- Axios
- Tailwind CSS

## 15.2 백엔드
- Python
- FastAPI
- SQLAlchemy Async ORM
- Pydantic
- Alembic

## 15.3 데이터베이스
- PostgreSQL
- pgvector

## 15.4 AI/문서 처리
- LangChain
- LangGraph
- OpenAI Embeddings / Chat Model
- 문서 parser 계층
- structured output

## 15.5 파일/인프라
- MVP: Local File Storage
- 고도화: AWS S3
- 배포 환경: Linux Server 기반

---

## 16. 최종 결론

본 프로젝트는 **채용 면접관을 위한 질문 자동생성 HR Copilot**을 주제로 하며,  
JD와 지원자 문서를 함께 분석하는 **RAG 기반 문서 이해형 AI 시스템**이다.

핵심 기능은 다음과 같다.

- JD / 이력서 / 포트폴리오 업로드
- 문서 청킹 및 임베딩
- pgvector 기반 검색
- 요약 / 역량 분석 / gap 분석
- 맞춤형 면접 질문 생성
- 질문 생성 근거 제시
- 프롬프트 정책 저장 및 LangGraph 기반 실행 흐름 관리

기술 구조는 다음 방향이 가장 적절하다.

- 프론트: React + Vite + TypeScript + Zustand + TanStack Query
- 백엔드: FastAPI + Async SQLAlchemy + 3계층 아키텍처
- DB: PostgreSQL 단일 인스턴스 + pgvector
- 파일 저장: MVP는 로컬, 고도화 시 S3 전환
- AI 워크플로우: LangGraph + Structured Output

즉, 이 프로젝트는 단순 질문 생성기가 아니라  
**채용 실무를 지원하는 문서 기반 AI Copilot**로 설계하는 것이 가장 적절하며,  
기술적 타당성, 구현 가능성, 시연 효과, 확장성 모두를 고려했을 때 매우 적합한 최종 프로젝트 주제라고 볼 수 있다.
