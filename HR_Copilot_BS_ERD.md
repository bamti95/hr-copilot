# HR Copilot BS — ERD

> PostgreSQL 15+ 기준 | 네이밍 표준 v2 적용  
> Mermaid `erDiagram` — GitHub / GitLab / Notion / Obsidian 에서 바로 렌더링

---

## 전체 ERD

```mermaid
erDiagram

    %% ── 1. 관리자 CMS 공통 영역 ──────────────────────────────────────────

    manager_group {
        serial      id              PK
        varchar100  group_name
        varchar100  group_key       UK
        text        description
        integer     created_by
        timestamptz created_at
        integer     deleted_by
        timestamptz deleted_at
        char1       is_deleted
    }

    manager {
        serial      id              PK
        varchar100  login_id        UK
        varchar255  password
        varchar100  name
        integer     group_id        FK
        varchar255  email
        varchar20   status
        timestamptz last_login_at
        integer     created_by
        timestamptz created_at
        integer     deleted_by
        timestamptz deleted_at
        char1       is_deleted
    }

    manager_menu {
        serial      id              PK
        integer     parent_id       FK
        varchar100  menu_name
        varchar100  menu_key        UK
        varchar255  menu_path
        integer     depth
        integer     sort_no
        varchar100  icon
        integer     created_by
        timestamptz created_at
        integer     deleted_by
        timestamptz deleted_at
        char1       is_deleted
    }

    manager_group_menu {
        serial      id              PK
        integer     group_id        FK
        integer     menu_id         FK
        char1       can_read
        char1       can_write
        char1       can_delete
        integer     created_by
        timestamptz created_at
        integer     deleted_by
        timestamptz deleted_at
        char1       is_deleted
    }

    %% ── 2. 문서 관리 영역 ───────────────────────────────────────────────

    document {
        serial      id              PK
        varchar30   document_type
        varchar255  title
        varchar255  original_file_name
        varchar500  file_path
        varchar20   file_ext
        bigint      file_size
        varchar100  mime_type
        text        extracted_text
        varchar20   extract_status
        integer     created_by      FK
        timestamptz created_at
        integer     deleted_by      FK
        timestamptz deleted_at
        char1       is_deleted
    }

    %% ── 3. 프롬프트 관리 영역 ───────────────────────────────────────────

    prompt_template {
        serial      id              PK
        varchar150  template_name
        varchar100  template_key    UK
        varchar50   template_type
        text        content
        integer     version_no
        text        description
        char1       is_active
        char1       is_deleted
        integer     created_by      FK
        timestamptz created_at
        integer     updated_by      FK
        timestamptz updated_at
        integer     deleted_by      FK
        timestamptz deleted_at
    }

    prompt_profile {
        serial      id              PK
        varchar150  profile_name
        varchar100  profile_key     UK
        text        description
        varchar50   strategy_type
        text        output_schema
        char1       is_active
        char1       is_deleted
        integer     created_by      FK
        timestamptz created_at
        integer     updated_by      FK
        timestamptz updated_at
        integer     deleted_by      FK
        timestamptz deleted_at
    }

    prompt_profile_template {
        serial      id              PK
        integer     profile_id      FK
        integer     template_id     FK
        integer     sort_no
        char1       is_required
        char1       is_active
        char1       is_deleted
        integer     created_by      FK
        timestamptz created_at
    }

    %% ── 4. LLM 실행 및 결과 영역 ────────────────────────────────────────

    workflow_run {
        serial      id              PK
        integer     role_document_id        FK
        integer     resume_document_id      FK
        integer     portfolio_document_id   FK
        integer     prompt_profile_id       FK
        varchar20   run_status
        text        assembled_prompt
        timestamptz started_at
        timestamptz finished_at
        text        error_message
        integer     created_by      FK
        timestamptz created_at
    }

    interview_question_set {
        serial      id              PK
        integer     workflow_run_id FK
        varchar255  set_title
        text        summary
        jsonb       core_competencies
        jsonb       risk_factors
        jsonb       verification_points
        integer     total_question_count
        char1       is_active
        char1       is_deleted
        integer     created_by      FK
        timestamptz created_at
    }

    interview_question_item {
        serial      id              PK
        integer     question_set_id FK
        integer     question_no
        varchar50   category
        text        question_text
        text        question_reason
        text        expected_answer
        text        evaluation_point
        varchar20   difficulty_level
        char1       is_active
        char1       is_deleted
        integer     created_by      FK
        timestamptz created_at
    }

    llm_call_log {
        serial      id              PK
        integer     workflow_run_id FK
        varchar100  model_name
        text        request_prompt
        text        response_text
        jsonb       response_json
        integer     prompt_tokens
        integer     completion_tokens
        integer     total_tokens
        integer     latency_ms
        numeric126  cost_amount
        varchar20   call_status
        text        error_message
        timestamptz created_at
    }

    %% ── 5. RAG 확장 선반영 영역 ─────────────────────────────────────────

    document_chunk {
        serial      id              PK
        integer     document_id     FK
        integer     chunk_no
        text        chunk_text
        integer     token_count
        varchar20   embedding_status
        timestamptz created_at
    }

    chunk_embedding {
        serial      id              PK
        integer     chunk_id        FK
        varchar100  embedding_model
        jsonb       vector_value
        integer     dimension
        timestamptz created_at
    }

    question_chunk_mapping {
        serial      id              PK
        integer     question_item_id FK
        integer     chunk_id         FK
        numeric54   relevance_score
        timestamptz created_at
    }

    %% ── 관계 정의 ────────────────────────────────────────────────────────

    manager_group           ||--o{ manager                  : "소속"
    manager_group           ||--o{ manager_group_menu       : "권한 보유"
    manager_menu            ||--o{ manager_group_menu       : "메뉴 노출"
    manager_menu            ||--o{ manager_menu             : "상위-하위(self)"

    document                ||--o{ workflow_run             : "role_document"
    document                ||--o{ workflow_run             : "resume_document"
    document                ||--o{ workflow_run             : "portfolio_document"
    prompt_profile          ||--o{ workflow_run             : "사용"
    prompt_profile          ||--o{ prompt_profile_template  : "구성"
    prompt_template         ||--o{ prompt_profile_template  : "포함"

    workflow_run            ||--|| interview_question_set   : "생성(1:1)"
    interview_question_set  ||--o{ interview_question_item  : "포함"
    workflow_run            ||--o{ llm_call_log             : "기록"

    document                ||--o{ document_chunk           : "분할"
    document_chunk          ||--|| chunk_embedding          : "임베딩(1:1)"
    interview_question_item ||--o{ question_chunk_mapping   : "근거 연결"
    document_chunk          ||--o{ question_chunk_mapping   : "근거 제공"
```

---

## 영역별 관계 상세

---

### A. 관리자 CMS 공통

```mermaid
erDiagram
    manager_group ||--o{ manager              : "소속"
    manager_group ||--o{ manager_group_menu   : "권한 보유"
    manager_menu  ||--o{ manager_group_menu   : "메뉴 노출"
    manager_menu  ||--o{ manager_menu         : "상위-하위(self)"

    manager_group {
        serial  id          PK
        varchar group_name
        varchar group_key   UK
    }
    manager {
        serial  id          PK
        varchar login_id    UK
        varchar status
        integer group_id    FK
    }
    manager_menu {
        serial  id          PK
        integer parent_id   FK
        varchar menu_key    UK
        integer depth
        integer sort_no
    }
    manager_group_menu {
        serial  id          PK
        integer group_id    FK
        integer menu_id     FK
        char1   can_read
        char1   can_write
        char1   can_delete
    }
```

---

### B. 프롬프트 조립 구조

```mermaid
erDiagram
    prompt_profile          ||--o{ prompt_profile_template  : "구성"
    prompt_template         ||--o{ prompt_profile_template  : "포함"

    prompt_profile {
        serial  id              PK
        varchar profile_key     UK
        varchar strategy_type
        char1   is_active
    }
    prompt_template {
        serial  id              PK
        varchar template_key    UK
        varchar template_type
        integer version_no
        char1   is_active
    }
    prompt_profile_template {
        serial  id              PK
        integer profile_id      FK
        integer template_id     FK
        integer sort_no
        char1   is_required
    }
```

---

### C. LLM 실행 및 결과 흐름

```mermaid
erDiagram
    document               ||--o{ workflow_run            : "role / resume / portfolio"
    prompt_profile         ||--o{ workflow_run            : "사용"
    workflow_run           ||--|| interview_question_set  : "생성(1:1)"
    interview_question_set ||--o{ interview_question_item : "포함"
    workflow_run           ||--o{ llm_call_log            : "기록"

    document {
        serial  id              PK
        varchar document_type
        varchar extract_status
    }
    workflow_run {
        serial  id                      PK
        integer role_document_id        FK
        integer resume_document_id      FK
        integer portfolio_document_id   FK
        integer prompt_profile_id       FK
        varchar run_status
    }
    interview_question_set {
        serial  id                  PK
        integer workflow_run_id     FK
        jsonb   core_competencies
        jsonb   risk_factors
        integer total_question_count
    }
    interview_question_item {
        serial  id              PK
        integer question_set_id FK
        varchar category
        varchar difficulty_level
    }
    llm_call_log {
        serial  id              PK
        integer workflow_run_id FK
        integer total_tokens
        numeric cost_amount
        varchar call_status
    }
```

---

### D. RAG 확장 구조

```mermaid
erDiagram
    document                ||--o{ document_chunk          : "분할"
    document_chunk          ||--|| chunk_embedding         : "임베딩(1:1)"
    interview_question_item ||--o{ question_chunk_mapping  : "근거 연결"
    document_chunk          ||--o{ question_chunk_mapping  : "근거 제공"

    document {
        serial  id  PK
    }
    document_chunk {
        serial  id              PK
        integer document_id     FK
        integer chunk_no
        varchar embedding_status
    }
    chunk_embedding {
        serial  id              PK
        integer chunk_id        FK
        varchar embedding_model
        jsonb   vector_value
        integer dimension
    }
    interview_question_item {
        serial  id  PK
    }
    question_chunk_mapping {
        serial  id                  PK
        integer question_item_id    FK
        integer chunk_id            FK
        numeric relevance_score
    }
```

---

## 테이블 목록 및 용도 요약

| 영역 | 테이블 | 용도 |
|:---|:---|:---|
| CMS 공통 | `manager_group` | 권한 그룹 정의 |
| CMS 공통 | `manager` | 관리자 계정 |
| CMS 공통 | `manager_menu` | CMS 메뉴 트리 |
| CMS 공통 | `manager_group_menu` | 그룹별 메뉴 권한 (N:M 해소) |
| 문서 | `document` | 업로드 문서 원본 (Role/Resume/Portfolio) |
| 프롬프트 | `prompt_template` | 프롬프트 원문 + 버전 관리 |
| 프롬프트 | `prompt_profile` | 실행 전략 프로파일 |
| 프롬프트 | `prompt_profile_template` | 프로파일-템플릿 조립 매핑 |
| 실행/결과 | `workflow_run` | LLM 분석 실행 단위 |
| 실행/결과 | `interview_question_set` | 면접 질문 세트 (실행 결과 헤더) |
| 실행/결과 | `interview_question_item` | 면접 질문 개별 항목 |
| 실행/결과 | `llm_call_log` | LLM API 호출 로그 |
| RAG 확장 | `document_chunk` | 문서 텍스트 분할 청크 |
| RAG 확장 | `chunk_embedding` | 청크 임베딩 벡터 |
| RAG 확장 | `question_chunk_mapping` | 질문-청크 근거 연결 |
