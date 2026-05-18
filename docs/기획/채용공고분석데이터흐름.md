# 채용공고 분석 Data Flow

## 1. 목적과 범위

채용공고 분석 기능은 채용공고 원문 또는 업로드 파일을 `AiJob` 백그라운드 작업으로 접수한 뒤, Rule 기반 위험 문구 탐지와 법률 기반지식 RAG 검색을 결합해 컴플라이언스 리포트를 생성한다.

주요 백엔드 진입점은 `backend/api/v1/routers/job_posting_router.py`이고, 실행 로직은 `backend/services/job_posting_service.py`, 기반지식 인덱싱은 `backend/services/job_posting_knowledge_service.py`, RAG 검색은 `backend/services/job_posting_retrieval_service.py`, trace 기록은 `backend/services/job_posting_trace_service.py`가 담당한다.

## 2. API 진입점

### 채용공고 분석 작업

- `POST /api/v1/job-postings/analyze-text/jobs`
  - 수동 입력 공고를 저장 또는 갱신한다.
  - `ai_job`에 `JOB_POSTING_COMPLIANCE_ANALYSIS` 작업을 생성한다.
  - FastAPI `BackgroundTasks`로 `JobPostingService.run_analysis_job(job_id)`를 실행한다.

- `POST /api/v1/job-postings/analyze-file/jobs`
  - 업로드 파일을 저장한다.
  - 파일 경로와 확장자를 `request_payload`에 넣어 `ai_job`을 생성한다.
  - 백그라운드에서 파일 텍스트 추출 후 공고 분석을 실행한다.

- `POST /api/v1/job-postings/{posting_id}/analysis-reports/jobs`
  - 기존 공고 기준으로 재분석 `ai_job`을 생성한다.
  - 백그라운드에서 동일 공고를 다시 분석한다.

- `GET /api/v1/job-postings/analysis-jobs/{job_id}`
  - 프론트 polling 대상이다.
  - `status`, `progress`, `current_step`, `result_payload`, `error_message`를 반환한다.

### 기반지식 작업

- `POST /api/v1/job-postings/knowledge-sources/upload`
  - PDF, DOCX, TXT, HWP, XLSX 등 기반지식 파일을 저장하고 `job_posting_knowledge_source`를 생성한다.

- `POST /api/v1/job-postings/knowledge-sources/{source_id}/index/jobs`
  - 단일 기반지식 문서 인덱싱 `ai_job`을 생성한다.
  - 백그라운드에서 텍스트 추출, chunk 생성, embedding 생성을 수행한다.

- `POST /api/v1/job-postings/knowledge-sources/seed-source-data/jobs`
  - `backend/sample_data/source_data`의 PDF 기반지식을 일괄 적재한다.

- `GET /api/v1/job-postings/knowledge-index-jobs/{job_id}`
  - 기반지식 인덱싱 작업의 polling 대상이다.

## 3. AiJob 상태 모델

모델은 `backend/models/ai_job.py`의 `AiJob`이다.

중요 필드:

- `job_type`
  - 채용공고 분석: `JOB_POSTING_COMPLIANCE_ANALYSIS`
  - 기반지식 인덱싱: `JOB_POSTING_KNOWLEDGE_INDEXING`
- `status`
  - `QUEUED`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `RETRYING`, `CANCELLED`
- `target_type`
  - 공고 분석은 `JOB_POSTING`
  - 기반지식은 `KNOWLEDGE_SOURCE`
- `target_id`
  - 분석 대상 공고 ID 또는 기반지식 source ID
- `progress`
  - 프론트 진행률 표시의 기준
- `current_step`
  - 프론트 진행 메시지 표시의 기준
- `request_payload`
  - 작업 실행에 필요한 입력 데이터
- `result_payload`
  - 완료 후 프론트가 후속 화면 이동에 사용하는 결과 데이터

## 4. 프론트 polling 흐름

프론트는 `frontend/src/features/manager/JobPosting/hooks/useJobPolling.ts`를 통해 상태를 polling한다.

흐름:

1. 사용자가 분석 또는 인덱싱 버튼을 누른다.
2. 서비스 함수가 `.../jobs` API를 호출한다.
3. API는 `202 Accepted`와 함께 초기 `JobPostingAiJob`을 반환한다.
4. 프론트가 `startPolling(submittedJob)`을 호출한다.
5. `useJobPolling`이 `fetchAnalysisJob(jobId)` 또는 `fetchKnowledgeIndexJob(jobId)`를 반복 호출한다.
6. 응답의 `progress`, `status`, `currentStep`이 `JobProgressCard`에 반영된다.
7. terminal status가 되면:
   - `SUCCESS`: `onCompleted` 실행
   - 그 외: `onFailed` 실행

이번 수정으로 `useJobPolling`은 `setInterval` 대신 `setTimeout` 루프와 ref 기반 callback을 사용한다. 이로 인해 job 객체가 갱신될 때마다 timer가 불필요하게 재생성되는 문제를 줄이고, 최신 callback을 안정적으로 참조한다.

## 5. 채용공고 분석 상세 흐름

### 5.1 작업 제출

`JobPostingService.submit_analyze_text_job`

1. `upsert_posting`으로 공고 원문 hash 기준 저장 또는 갱신
2. `AiJob` 생성
   - `status=QUEUED`
   - `progress=2`
   - `current_step=analysis_job_created`
   - `request_payload.mode=TEXT`
   - `request_payload.posting_id`
3. commit 후 job response 반환

파일 분석은 `submit_analyze_file_job`에서 파일을 먼저 저장하고, `request_payload.mode=FILE`, `file_path`, `file_ext`, `job_title`, `company_name`을 저장한다.

### 5.2 백그라운드 실행

`JobPostingService.run_analysis_job(job_id)`

1. `ai_job` 조회
2. `status=RUNNING`, `progress=10`, `current_step=analysis_started`
3. mode별 분기
   - `TEXT` 또는 `EXISTING`
     - 공고 조회
     - `progress=35`, `current_step=posting_loaded`
   - `FILE`
     - `extract_text_from_file`로 텍스트 추출
     - `progress=30`, `current_step=file_text_extracted`
     - 추출 텍스트로 공고 저장
     - `progress=45`, `current_step=posting_saved`
4. `run_rule_rag_analysis` 실행
5. 리포트 ID와 위험 등급을 `result_payload`에 저장
6. `status=SUCCESS`, `progress=100`, `current_step=analysis_completed`

이번 수정으로 `run_rule_rag_analysis` 내부에도 `progress_callback`을 주입했다. 따라서 긴 RAG 처리 중에도 `ai_job.progress`가 다음 단계별로 반영된다.

분석 내부 progress:

- `50`: `detecting_risk_phrases`
- `58`: `generating_retrieval_queries`
- `62~80`: `retrieving_evidence_N_of_M`
- `82`: `checking_evidence_sufficiency`
- `87`: `reranking_evidence`
- `92`: `generating_structured_report`
- `96`: `saving_report_and_trace`
- `100`: `analysis_completed`

## 6. Rule 기반 위험 문구 탐지

`job_posting_service.py`의 `RISK_PATTERNS`가 1차 탐지를 담당한다.

각 패턴은 다음 정보를 가진다.

- `issue_type`
  - 예: `GENDER_DISCRIMINATION`, `AGE_DISCRIMINATION`, `IRRELEVANT_PERSONAL_INFO`, `FALSE_JOB_AD`
- `severity`
  - `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `pattern`
  - 공고 원문에 적용하는 정규식
- `reason`
  - 위험 사유
- `replacement`
  - 추천 수정 문구
- `query_terms`
  - RAG 검색에 사용할 핵심어

`detect_issues(posting_text)`는 정규식 매칭 결과를 중복 제거하고, issue payload를 만든다.

생성되는 issue 주요 필드:

- `issue_type`
- `severity`
- `category`
  - 법적 이슈는 `LEGAL`, 브랜딩/품질 이슈는 `BRANDING`
- `flagged_text`
- `why_risky`
- `recommended_revision`
- `confidence`
- `query_terms`
- `sources`

## 7. 기반지식 적재 및 청킹 전략

### 7.1 문서 업로드

`JobPostingKnowledgeService.upload_source`

1. `_save_knowledge_upload`로 파일 저장
2. `KnowledgeSourceCreateRequest` 구성
3. `create_or_update_source`로 `job_posting_knowledge_source` 저장 또는 갱신
4. 초기 상태:
   - `extract_status=PENDING`
   - `index_status=PENDING`
   - `chunk_count=0`

### 7.2 인덱싱

`JobPostingKnowledgeService.index_source`

1. source 조회
2. `extract_status=PROCESSING`, `index_status=PROCESSING`
3. `extract_text_from_file(file_path, file_ext)`로 텍스트 추출
4. 추출 실패 시:
   - `extract_status=FAILED`
   - `index_status=FAILED`
   - `chunk_count=0`
5. 기존 chunk 삭제
6. `build_chunks_for_source(source, extracted_text)` 실행
7. chunk별 embedding 생성 후 저장
8. source의 `chunk_count`, `index_status=SUCCESS` 갱신

### 7.3 청킹 전략

상수:

- `MAX_CHUNK_CHARS = 1000`
- `MIN_CHUNK_CHARS = 180`

텍스트 정규화:

- `normalize_chunk_source_text`
  - 줄바꿈, 공백, 문단 구조를 정리해 chunk 분할 전 입력을 안정화한다.

분기:

- 법령 텍스트: `split_by_article`
  - 조문 번호 단위로 1차 분할
  - 긴 조문은 항/호/문단 기준으로 재분할
  - 전략명: `law_article_then_paragraph_item`

- 점검/사례 문서: `split_by_case_blocks`
  - 사례 단위 패턴으로 1차 분할
  - 긴 사례는 길이 제한 기준으로 재분할
  - 전략명: `case_one_case_then_limit`

- 가이드/매뉴얼 문서: `split_by_heading_or_window`
  - 제목/헤딩으로 block 구성
  - block이 길면 문단 또는 문장 단위로 재분할
  - 전략명: `guide_heading_then_limit`

공통 길이 제한:

- `split_to_limit`
- `split_to_limit_blocks`
- `split_by_hard_limit`

이 함수들은 chunk가 `MAX_CHUNK_CHARS`를 넘지 않도록 문단, 문장, hard limit 순서로 나눈다. 너무 작은 조각은 가능하면 앞 chunk와 합쳐 `MIN_CHUNK_CHARS` 이상이 되도록 조정한다.

### 7.4 chunk metadata

`build_chunks_for_source`가 생성하는 주요 값:

- `knowledge_source_id`
- `chunk_type`
  - `LEGAL_CLAUSE`, `INSPECTION_CASE`, `LEGAL_GUIDE`
- `chunk_key`
- `chunk_index`
- `section_title`
- `content`
- `summary`
- `issue_code`
- `risk_category`
- `severity`
- `law_name`
- `article_no`
- `tags`
- `metadata`
  - `source_title`
  - `source_type`
  - `chunking_strategy`
- `embedding_model`
- `embedding`
- `content_hash`
- `token_count`

## 8. 임베딩 전략

구현 위치: `backend/services/job_posting_embedding_service.py`

### 8.1 기본 모델

- 환경 변수: `JOB_POSTING_EMBEDDING_MODEL`
- 기본값: `BAAI/bge-m3`
- dimension: `1536`

`SentenceTransformer` 로딩에 성공하면 `BAAI/bge-m3`를 사용한다.

### 8.2 fallback embedding

모델 로딩 또는 추론 실패 시 `local-hash-embedding-v1`을 사용한다.

fallback 방식:

1. 텍스트에서 token 추출
2. token별 SHA-256 hash 계산
3. hash index를 1536차원 vector 위치로 사용
4. sign bit로 양수/음수 누적
5. L2 normalization

이 방식은 semantic embedding은 아니지만 개발/로컬 환경에서 pgvector 검색 흐름을 유지하기 위한 deterministic fallback이다.

### 8.3 vector dimension 보정

`_fit_vector_dim`

- 모델 출력이 1536보다 길면 truncate 후 normalize
- 짧으면 zero padding
- 정확히 1536이면 반올림 후 사용

## 9. 검색 및 RAG 전략

구현 위치: `backend/services/job_posting_retrieval_service.py`

### 9.1 issue query 생성

`build_issue_query(issue)`는 다음 값을 결합한다.

- `issue_type`
- `flagged_text`
- `why_risky`
- `query_terms`

### 9.2 hybrid retrieval

`retrieve_for_issue`

1. query terms 추출
2. query embedding 생성
3. full text 검색
   - `chunk_repo.search_by_full_text`
   - limit: `limit * 3`
4. vector 검색
   - `chunk_repo.search_by_vector`
   - 실패 시 `_python_vector_fallback`
5. text/vector 결과 merge
6. heuristic rerank
7. CrossEncoder rerank 가능 시 추가 rerank
8. 상위 `limit`개 반환

### 9.3 점수 결합

`merge_retrieval_rows`

- text score
- vector score
- keyword score
- source priority
- issue_code match bonus

문서 유형별 가중치:

- 법령 텍스트: text `0.6`, vector `0.4`
- 가이드/매뉴얼/점검 사례: text `0.4`, vector `0.6`
- 기타: text `0.45`, vector `0.55`

### 9.4 rerank 전략

`rerank_evidence`

추가 bonus:

- 법령명 또는 조문 번호 있음: `+0.25`
- 점검 사례 문서: `+0.15`
- 가이드/매뉴얼: `+0.1`
- issue_code 일치: `+0.2`

`apply_slot_policy`

- 법령 근거 2개
- 가이드/매뉴얼 2개
- 사례 1개
- 이후 남은 결과를 점수순으로 채움

`apply_model_rerank`

- 환경 변수 `JOB_POSTING_RERANKER_MODEL`
- 기본값 `BAAI/bge-reranker-v2-m3`
- CrossEncoder 로딩 성공 시 query-document pair 점수로 rerank score를 보정한다.
- 실패 또는 미설치 시 `heuristic-slot-rerank`만 사용한다.

## 10. 리포트 생성

`run_rule_rag_analysis`

1. `JobPostingAnalysisReport` 생성
2. `detect_issues`
3. retrieval query 생성
4. issue별 RAG 검색
5. evidence sufficiency 계산
6. evidence rerank
7. risk level 계산
8. structured compliance report 생성
9. report 저장

저장되는 주요 필드:

- `analysis_status`
- `risk_level`
- `issue_count`
- `violation_count`
- `warning_count`
- `confidence_score`
- `detected_issue_types`
- `retrieval_summary`
- `summary_text`
- `parsed_sections`
- `overall_score`
- `risk_score`
- `attractiveness_score`
- `issue_summary`
- `matched_evidence`
- `compliance_warnings`
- `improvement_suggestions`
- `rewrite_examples`
- `final_report`

## 11. Trace 기록

구현 위치: `backend/services/job_posting_trace_service.py`

`JobPostingTraceRecorder`는 각 pipeline node를 `llm_call_log`에 기록한다.

기록되는 node 예시:

- `detect_risk_phrases`
- `generate_retrieval_queries`
- `bm25_retrieve`
- `vector_retrieve`
- `merge_hybrid_results`
- `check_evidence_sufficiency`
- `rerank_evidence`
- `generate_structured_report`
- `save_report_and_logs`
- `pipeline_failed`

각 로그에는 다음이 포함된다.

- `trace_id`
- `run_id`
- `parent_run_id`
- `execution_order`
- `request_json`
- `output_json`
- `elapsed_ms`
- `call_status`
- `error_message`

## 12. 실패 처리

분석 작업 실패:

- `run_analysis_job` 예외 발생
- rollback
- `ai_job.status=FAILED`
- `ai_job.progress=100`
- `ai_job.current_step=analysis_failed`
- `ai_job.error_message=str(exc)`
- 프론트 polling이 terminal status로 인식 후 error 표시

분석 pipeline 내부 실패:

- `run_rule_rag_analysis`가 `pipeline_failed` trace 기록
- report `analysis_status=FAILED`
- report `error_message` 저장

기반지식 인덱싱 실패:

- source `extract_status` 또는 `index_status=FAILED`
- `ai_job.status=FAILED`
- `current_step=knowledge_index_failed`
- `error_message` 저장

## 13. 이번 수정 사항

Polling 상태 반영 문제를 해결하기 위해 다음을 변경했다.

- 프론트 `useJobPolling`
  - interval 재생성에 취약한 구조를 `setTimeout` 루프로 변경
  - fetcher와 callback을 ref로 보관해 최신 콜백을 안정적으로 호출
  - polling 시작 직후 즉시 첫 fetch 수행

- 프론트 신규 분석/상세 재분석
  - `pollJob`을 직접 await 하는 blocking 흐름에서 `useJobPolling` 기반 흐름으로 변경
  - job 제출 직후 진행 카드가 갱신되고, 완료 시 리포트 화면으로 이동

- 백엔드 `run_rule_rag_analysis`
  - `progress_callback` 추가
  - 위험 문구 탐지, query 생성, evidence retrieval, sufficiency, rerank, report 생성, 저장 단계별로 `ai_job.progress`와 `current_step` 갱신
  - 긴 RAG 처리 중에도 프론트 polling이 의미 있는 진행률을 받을 수 있음

