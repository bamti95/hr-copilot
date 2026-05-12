# 채용공고 RAG Baseline 및 Agentic 고도화 가이드

## 1. 현재 구현 범위

현재 채용공고 컴플라이언스 기능은 **rule-rag-baseline** 수준으로 구현되어 있음.

크게 두 영역이 붙어 있음.

1. 채용공고 분석 기능
2. 법률 기반지식 RAG 관리 기능

채용공고 분석 기능은 관리자가 채용공고 본문을 입력하거나 파일을 업로드하면 공고를 저장하고, 위험 후보 문구를 탐지한 뒤 분석 리포트를 저장하는 구조임.

법률 기반지식 RAG 관리 기능은 `backend/sample_data/source_data` 안의 법률 PDF 또는 관리자가 업로드한 PDF/문서를 기반지식으로 등록하고, 텍스트 추출, 청킹, 임시 embedding 생성, 검색 테스트까지 할 수 있는 구조임.

현재 구현된 것은 “운영 품질의 Agentic RAG”가 아니라, 파일 업로드부터 chunk 저장과 검색 검증까지 가능한 **RAG 기반지식 시스템 baseline**임.

## 2. 현재 백엔드 구조

관련 주요 파일은 아래와 같음.

```text
backend/api/v1/routers/job_posting_router.py
backend/services/job_posting_service.py
backend/services/job_posting_knowledge_service.py
backend/repositories/job_posting_repository.py
backend/repositories/job_posting_knowledge_repository.py
backend/schemas/job_posting.py
backend/models/job_posting.py
backend/models/job_posting_analysis_report.py
backend/models/job_posting_knowledge_source.py
backend/models/job_posting_knowledge_chunk.py
```

## 3. 현재 채용공고 분석 흐름

현재 분석은 `backend/services/job_posting_service.py`의 `run_rule_rag_analysis()` 중심으로 동작함.

흐름은 아래와 같음.

```text
채용공고 입력/업로드
→ JobPosting 저장
→ run_rule_rag_analysis() 실행
→ regex 기반 위험 후보 문구 탐지
→ 후보별 query_terms 생성
→ JobPostingKnowledgeChunk keyword 검색
→ 단순 score 기반 근거 정렬
→ risk_level 계산
→ final_report 생성
→ JobPostingAnalysisReport 저장
```

현재 위험 문구 탐지는 `detect_issues()`에서 수행함.

현재 방식은 LLM 판단이 아니라 `RISK_PATTERNS` 정규식 기반임.

현재 근거 검색은 `JobPostingKnowledgeChunkRepository.search_candidates()`를 사용함.

현재 방식은 BM25나 pgvector similarity search가 아니라 `content`, `summary`, `issue_code`, `law_name`에 대한 `ilike` keyword baseline임.

현재 리포트 생성은 `build_final_report()`에서 heuristic으로 생성함.

LLM structured output은 아직 붙어 있지 않음.

## 4. 현재 기반지식 적재 흐름

기반지식 적재는 `backend/services/job_posting_knowledge_service.py` 중심으로 구현되어 있음.

흐름은 아래와 같음.

```text
PDF/문서 업로드 또는 source_data seed
→ JobPostingKnowledgeSource 생성
→ extract_text_from_file() 텍스트 추출
→ source_type 자동 추론
→ 문서 유형별 chunk 분리
→ chunk metadata 추론
→ local-hash-embedding-v1 embedding 생성
→ JobPostingKnowledgeChunk 저장
```

관련 함수는 아래와 같음.

```text
upload_source()
create_or_update_source()
index_source()
seed_source_data()
build_chunks_for_source()
split_legal_text()
embed_text()
```

## 5. 현재 청킹 전략

현재 청킹은 `job_posting_knowledge_service.py` 안에서 처리함.

진입점은 아래 함수임.

```python
build_chunks_for_source()
```

이 함수가 내부적으로 아래 함수를 호출함.

```python
split_legal_text()
```

문서 유형에 따라 분기함.

```text
LAW_TEXT
→ split_by_article()
→ 법 조항 단위 분리 시도함

INSPECTION_CASE
→ split_by_case_blocks()
→ 지도점검/위반 사례 블록 단위 분리 시도함

그 외 LEGAL_GUIDEBOOK / LEGAL_MANUAL
→ split_by_heading_or_window()
→ 제목, 번호, 문단 기반 분리함
```

현재 chunk 크기 기준은 아래와 같음.

```python
MAX_CHUNK_CHARS = 1800
MIN_CHUNK_CHARS = 240
```

긴 chunk는 `expand_long_parts()`에서 문단 기준으로 다시 나눔.

현재 chunk에 저장되는 주요 값은 아래와 같음.

```text
content
summary
chunk_type
chunk_key
chunk_index
section_title
issue_code
risk_category
severity
law_name
article_no
penalty_guide
tags
metadata_json
embedding_model
embedding
token_count
content_hash
```

## 6. 현재 Metadata 추론

chunk별 metadata는 아래 함수들로 추론함.

```python
infer_issue_code()
infer_risk_category()
infer_severity()
infer_law_name()
infer_article_no()
infer_penalty_guide()
infer_tags()
document_priority()
```

예를 들면, 지도점검 PDF 안에 `혼인여부`, `가족`, `키`, `체중`, `근로조건 변경` 같은 표현이 있으면 `IRRELEVANT_PERSONAL_INFO`, `PHYSICAL_CONDITION`, `UNFAVORABLE_CONDITION_CHANGE` 같은 issue code를 추론하려고 함.

다만 현재는 rule 기반 추론이라 정확도가 제한적임.

## 7. 현재 Embedding 전략

현재 embedding은 실제 semantic embedding이 아님.

현재 함수는 아래임.

```python
embed_text()
```

현재 모델명은 아래로 저장됨.

```python
LOCAL_EMBEDDING_MODEL = "local-hash-embedding-v1"
```

현재 방식은 아래와 같음.

```text
텍스트에서 토큰 추출
→ 각 토큰을 SHA256 hash
→ 1536차원 벡터 index에 누적
→ L2 normalization
→ JobPostingKnowledgeChunk.embedding 저장
```

현재 장점은 아래와 같음.

```text
외부 API 없이 바로 동작함
embedding 저장/검색 흐름 검증 가능함
Vector DB 연결 전 baseline 검증 가능함
```

현재 한계는 아래와 같음.

```text
의미 기반 검색이 아님
문맥 유사도 품질 낮음
한국어 형태소 처리 없음
법률 문장 간 semantic similarity 약함
```

## 8. 현재 검색 전략

기반지식 검색 API는 아래임.

```text
POST /api/v1/job-postings/knowledge-sources/search
```

백엔드 구현 위치는 아래임.

```python
JobPostingKnowledgeService.search_knowledge()
```

repository 후보 조회는 아래에서 함.

```python
JobPostingKnowledgeChunkRepository.find_search_pool()
```

검색 흐름은 아래와 같음.

```text
query 입력
→ extract_query_terms()로 검색어 추출
→ query embedding 생성
→ chunk 후보 pool 조회
→ keyword score 계산
→ cosine similarity 계산
→ hybrid score 계산
→ 점수순 정렬
→ 결과 반환
```

현재 검색 모드는 아래 3개임.

```text
HYBRID
KEYWORD
VECTOR
```

현재 hybrid score는 아래 비율로 계산함.

```python
hybrid_score = keyword_score * 0.45 + vector_score * 0.55
```

단, 현재 vector score는 `local-hash-embedding-v1` 기반이라 운영 품질 semantic search는 아님.

## 9. 현재 프론트 화면

관리자 콘솔에 채용공고 분석 메뉴가 추가되어 있음.

라우트는 아래와 같음.

```text
/manager/job-postings
→ 채용공고 분석 목록

/manager/job-postings/new
→ 채용공고 본문 입력 또는 파일 업로드 후 분석 실행

/manager/job-postings/:id
→ 채용공고 상세 및 분석 이력

/manager/job-postings/:id/report
→ 분석 리포트 상세

/manager/job-postings/knowledge-sources
→ 법률 기반지식 업로드, source_data 적재, 인덱싱, chunk 미리보기, 검색 테스트
```

프론트 주요 파일은 아래와 같음.

```text
frontend/src/features/manager/JobPosting/index.tsx
frontend/src/features/manager/JobPosting/services/jobPostingService.ts
frontend/src/features/manager/JobPosting/types/index.ts
frontend/src/app/router/index.tsx
frontend/src/common/data/managerConsoleData.ts
```

## 10. 현재까지 가능한 것

현재 가능한 것은 아래와 같음.

```text
채용공고 저장 가능함
채용공고 파일 업로드 분석 가능함
채용공고 본문 입력 분석 가능함
분석 리포트 저장 가능함
위험 문구 baseline 탐지 가능함
기반지식 PDF 업로드 가능함
source_data 법률 PDF 일괄 적재 가능함
텍스트 추출 가능함
문서 유형별 baseline 청킹 가능함
임시 embedding 저장 가능함
기반지식 검색 테스트 가능함
chunk 미리보기 가능함
분석 리포트에서 매칭 근거 확인 가능함
```

## 11. 아직 구현 안 된 것

아직 안 된 것은 아래와 같음.

```text
실제 embedding 모델 연동 안 됨
pgvector DB operator 기반 similarity search 안 됨
BM25 검색 안 됨
hybrid retrieval 운영 품질로 고도화 안 됨
reranker 안 됨
LLM structured output 안 됨
Agentic 재검색 루프 안 됨
근거 충분성 판단 안 됨
근거 없는 판단 제거/보수화 안 됨
AiJob 기반 비동기 인덱싱/분석 안 됨
LlmCallLog 기반 노드별 추적은 모델 확장만 되어 있고 실제 job posting pipeline 로그 연결은 아직 제한적임
```

## 12. 앞으로 RAG Agentic을 붙일 위치

Agentic RAG는 현재 `job_posting_service.py`의 `run_rule_rag_analysis()`를 대체하거나 내부를 분해하는 방식으로 붙이면 됨.

추천 구조는 아래와 같음.

```text
backend/ai/job_posting_graph/
  state.py
  nodes.py
  runner.py
```

또는 서비스 단위로 먼저 분리해도 됨.

```text
backend/services/job_posting_retrieval_service.py
backend/services/job_posting_reranker_service.py
backend/services/job_posting_llm_service.py
backend/services/job_posting_guardrail_service.py
```

권장 흐름은 아래와 같음.

```text
1. 공고 파싱
2. 위험 후보 문구 탐지
3. 후보별 검색 query 생성
4. BM25 검색
5. vector 검색
6. hybrid evidence merge
7. reranker 재정렬
8. 근거 충분성 판단
9. 부족하면 query rewrite
10. 재검색
11. LLM structured output 생성
12. 근거 없는 판단 제거/보수화
13. 최종 리포트 저장
```

이 흐름의 최종 저장 위치는 기존 `JobPostingAnalysisReport`를 그대로 쓰면 됨.

## 13. RAG 고도화 시 수정할 위치

청킹 고도화는 아래 파일에서 하면 됨.

```text
backend/services/job_posting_knowledge_service.py
```

구체적으로 수정할 함수는 아래임.

```python
split_legal_text()
split_by_article()
split_by_case_blocks()
split_by_heading_or_window()
expand_long_parts()
build_chunks_for_source()
```

법률 문서별 정교한 parser를 붙이려면 아래처럼 분리하는 것이 좋음.

```text
backend/services/job_posting_chunking_service.py
```

예상 역할은 아래와 같음.

```text
법령 조항 parser
지도점검 사례 parser
표/목록 parser
페이지 metadata 유지
chunk overlap 적용
parent-child chunk 생성
evidence card 생성
```

## 14. Embedding 고도화 시 수정할 위치

embedding 고도화는 현재 아래 함수 교체가 핵심임.

```python
embed_text()
```

위치는 아래임.

```text
backend/services/job_posting_knowledge_service.py
```

다만 운영용으로는 별도 서비스로 빼는 게 좋음.

```text
backend/services/embedding_service.py
```

예상 구조는 아래와 같음.

```python
class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...
```

교체 후 저장 필드는 그대로 사용 가능함.

```text
JobPostingKnowledgeChunk.embedding
JobPostingKnowledgeChunk.embedding_model
```

실제 모델 예시는 아래와 같음.

```text
OpenAI text-embedding-3-small
OpenAI text-embedding-3-large
bge-m3
multilingual-e5-large
KoSimCSE 계열
사내 embedding 모델
```

주의할 점은 embedding dimension이 바뀌면 DB migration도 필요함.

현재 모델은 아래 기준임.

```python
Vector(1536)
```

예를 들어 `text-embedding-3-large`를 3072 차원으로 쓰면 `Vector(3072)`로 migration 필요함.

반대로 `text-embedding-3-small` 1536 차원이면 현재 구조와 맞음.

## 15. pgvector 고도화 시 수정할 위치

현재 vector 검색은 Python에서 cosine similarity를 계산함.

운영용으로는 아래 repository에서 DB operator 기반 검색으로 바꿔야 함.

```text
backend/repositories/job_posting_knowledge_repository.py
```

추가할 함수 예시는 아래와 같음.

```python
search_by_vector()
search_by_keyword()
hybrid_search()
```

현재는 아래 함수가 baseline 후보 조회를 담당함.

```python
find_search_pool()
```

향후에는 `find_search_pool()` 대신 아래처럼 바꾸는 게 좋음.

```text
search_by_vector()
→ pgvector <=> 또는 cosine distance 사용

search_by_bm25()
→ PostgreSQL full-text search 또는 별도 BM25 엔진 사용

hybrid_search()
→ vector 결과 + BM25 결과를 RRF 또는 weighted score로 merge
```

## 16. BM25 고도화 시 수정할 위치

BM25는 repository 계층에 붙이는 게 좋음.

```text
backend/repositories/job_posting_knowledge_repository.py
```

PostgreSQL full-text 기반이면 migration으로 `tsvector` 컬럼 또는 index를 추가해야 함.

예상 추가 필드/인덱스는 아래와 같음.

```text
content_tsvector
GIN index
```

혹은 별도 검색엔진을 쓰면 repository가 외부 search client를 호출하게 됨.

```text
OpenSearch
Elasticsearch
Meilisearch
Typesense
```

## 17. Hybrid Retrieval 고도화 시 수정할 위치

현재 hybrid score는 `search_knowledge()` 안에서 직접 계산함.

현재 위치는 아래임.

```python
JobPostingKnowledgeService.search_knowledge()
```

운영용으로는 아래 서비스로 분리하는 게 좋음.

```text
backend/services/job_posting_retrieval_service.py
```

역할은 아래와 같음.

```text
query normalization
query expansion
BM25 검색 호출
vector 검색 호출
RRF 또는 weighted merge
중복 chunk 제거
source priority 반영
evidence payload 생성
```

## 18. Reranker 붙일 위치

reranker는 retrieval 이후에 붙이면 됨.

추천 위치는 아래임.

```text
backend/services/job_posting_reranker_service.py
```

역할은 아래와 같음.

```text
query + candidate chunk 입력
cross-encoder 또는 LLM rerank 수행
top-k evidence 반환
근거 문장 highlight
```

Reranker 결과는 아래에 저장하면 됨.

```text
JobPostingAnalysisReport.matched_evidence
JobPostingAnalysisReport.retrieval_summary
```

## 19. LLM Structured Output 붙일 위치

LLM structured output은 현재 `build_final_report()`를 대체하면 됨.

현재 위치는 아래임.

```text
backend/services/job_posting_service.py
```

운영용으로는 아래 파일을 새로 만드는 게 좋음.

```text
backend/services/job_posting_llm_service.py
```

역할은 아래와 같음.

```text
공고 원문
위험 후보 문구
retrieved evidence
법령/사례 근거
수정 문구
risk level
structured JSON report 생성
```

저장 위치는 아래 기존 필드를 그대로 쓰면 됨.

```text
JobPostingAnalysisReport.issue_summary
JobPostingAnalysisReport.matched_evidence
JobPostingAnalysisReport.compliance_warnings
JobPostingAnalysisReport.improvement_suggestions
JobPostingAnalysisReport.rewrite_examples
JobPostingAnalysisReport.final_report
```

## 20. 근거 충분성 판단 붙일 위치

근거 충분성 판단은 retrieval/rerank 이후, LLM output 이전에 넣는 게 좋음.

추천 위치는 아래임.

```text
backend/services/job_posting_guardrail_service.py
```

또는 Agent graph node로 만들면 됨.

```text
backend/ai/job_posting_graph/nodes.py
```

역할은 아래와 같음.

```text
후보 issue별 evidence 개수 확인
법령 조항 또는 사례 근거 존재 여부 확인
score threshold 확인
근거 부족 issue는 보수화
근거 부족 query는 rewrite 대상으로 전달
```

저장 위치는 아래가 적절함.

```text
JobPostingAnalysisReport.retrieval_summary
JobPostingAnalysisReport.compliance_warnings
JobPostingAnalysisReport.final_report
```

## 21. Query Rewrite / 재검색 붙일 위치

Agentic 재검색 루프는 graph로 빼는 게 가장 좋음.

추천 위치는 아래임.

```text
backend/ai/job_posting_graph/
```

예상 노드는 아래와 같음.

```text
parse_posting
detect_risk_candidates
generate_retrieval_queries
hybrid_retrieve
rerank_evidence
evaluate_evidence_sufficiency
rewrite_query
retry_retrieve
generate_structured_report
guardrail_report
save_report
```

이 노드별 로그는 `LlmCallLog`에 아래 값으로 저장하면 됨.

```text
pipeline_type = JOB_POSTING_COMPLIANCE
job_posting_id
job_posting_analysis_report_id
node_name
input_tokens
output_tokens
estimated_cost
request_json
output_json
trace_id
run_id
```

## 22. AiJob 비동기화 붙일 위치

현재 분석/인덱싱은 동기 실행에 가까움.

비동기화는 기존 `AiJob` 모델을 사용하면 됨.

사용할 job type은 아래임.

```text
JOB_POSTING_COMPLIANCE_ANALYSIS
JOB_POSTING_KNOWLEDGE_INDEXING
```

대상 타입은 아래임.

```text
JOB_POSTING
KNOWLEDGE_SOURCE
```

적용 위치는 아래임.

```text
backend/services/job_posting_service.py
backend/services/job_posting_knowledge_service.py
```

향후 구조는 아래처럼 가면 됨.

```text
API 요청
→ AiJob 생성
→ status QUEUED
→ background worker 실행
→ progress/current_step 업데이트
→ 결과 저장
→ 프론트 polling
```

## 23. 다음 개발 우선순위

추천 우선순위는 아래임.

```text
1. 실제 embedding 모델 교체
2. pgvector DB similarity search 구현
3. BM25 또는 full-text search 추가
4. hybrid retrieval service 분리
5. 분석 파이프라인에서 keyword baseline을 hybrid retrieval로 교체
6. LLM structured output 추가
7. evidence sufficiency check 추가
8. query rewrite/retry loop 추가
9. AiJob 비동기화
10. LlmCallLog 기반 노드 로그 저장
```

## 24. 한 줄 요약

현재는 `source_data` 법률 PDF와 업로드 문서를 기반지식으로 등록하고, baseline 청킹/임시 embedding/검색 검증까지 가능한 상태임.

다음 단계는 `job_posting_knowledge_service.py`의 청킹/embedding을 고도화하고, `job_posting_knowledge_repository.py`에 pgvector/BM25 검색을 추가한 뒤, `job_posting_service.py`의 `run_rule_rag_analysis()`를 Agentic RAG pipeline으로 교체하는 것임.
