---
name: hr-copilot-backend-generator
description: Backend feature generation and maintenance for the HR Copilot FastAPI/SQLAlchemy/Alembic app. Use when adding or modifying API routers, services, repositories, Pydantic schemas, SQLAlchemy models, Alembic migrations, background jobs, and backend validation.
---

# HR Copilot Backend Skill

이 스킬은 현재 HR Copilot 백엔드 구조를 유지하면서 API, service, repository, schema, model, migration을 추가하거나 수정하기 위한 작업 기준이다. 새 백엔드 프로젝트를 만들지 말고, 기존 FastAPI 계층 구조와 주변 구현을 먼저 따른다.

## Project Safety

- Reuse the current repository layout. Do not scaffold a new backend project.
- Keep all files UTF-8 without BOM.
- Do not create or replace Gradle/frontend build files from backend work.
- Use `uv` for backend dependency and verification commands.
- Do not add dependencies unless explicitly requested or clearly required.
- Do not edit `.env` with secrets. Use `.env_example` only when documenting new config keys.
- Preserve existing async SQLAlchemy patterns.

## Backend Structure

The backend follows this layout:

```txt
backend/
- main.py
- core/
- dependencies/
- api/v1/routers/
- schemas/
- models/
- repositories/
- services/
- ai/
- common/
- tasks/
- alembic/
```

Use each layer for its intended responsibility:

- `api/v1/routers/`: FastAPI route definitions, request/response models, dependency wiring.
- `schemas/`: Pydantic request/response DTOs.
- `models/`: SQLAlchemy ORM entities and enums.
- `repositories/`: database query and persistence logic.
- `services/`: business logic, transactions, orchestration, background job entry points.
- `dependencies/`: FastAPI dependencies such as authenticated manager lookup and role checks.
- `core/`: configuration, database/session setup, security primitives.
- `common/`: shared pure utilities, file handling, normalization, document helpers.
- `ai/`: LLM/client or graph-specific integrations.
- `alembic/versions/`: schema migrations only.

## Router Rules

- Put new v1 routers under `api/v1/routers/`.
- Register new routers in `api/v1/routers/router.py`.
- Use `APIRouter(prefix=..., tags=[...])`.
- Use `Depends(get_db)` for `AsyncSession`.
- Use `get_current_active_manager` when an endpoint requires authenticated manager access.
- Keep routers thin: validate inputs, wire dependencies, call services, and return DTOs.
- Do not put SQL queries or complex business logic in routers.

## Schema Rules

- Use Pydantic `BaseModel` request/response DTOs.
- Match frontend DTO naming where possible:
  - `XxxRequest`
  - `XxxResponse`
  - `XxxListResponse`
- Prefer `from_entity` classmethods for ORM-to-response mapping when the feature already uses that pattern.
- Keep API response shapes stable and explicit.
- For list endpoints, include `items`, `total_count`, and `total_pages` when pagination is used.

## Service Rules

- Put business logic and orchestration in `services/`.
- Services should accept `db: AsyncSession` from routers unless running in an isolated background job.
- For background jobs that run outside the request session, use `AsyncSessionLocal` deliberately and keep session scope explicit.
- Commit/rollback boundaries should be clear. Prefer committing in the service layer after a complete business operation.
- Raise `HTTPException` from services only when the existing feature already follows that pattern; otherwise keep domain checks clear and consistent with nearby services.
- Keep LLM/RAG/pipeline constants named and centralized within the owning service or related module.

## Repository Rules

- Put database access in `repositories/`.
- Reuse `BaseRepository` for simple `add`, `flush`, `refresh`, and `get_by_id` behavior.
- Use async SQLAlchemy queries with `select`, `func`, `desc`, and `await db.execute(...)`.
- Keep soft-delete filters explicit with `deleted_at.is_(None)` when the model supports soft deletion.
- Do not hide business decisions inside repositories; repositories should query and persist.

## Model and Migration Rules

- Put SQLAlchemy models in `models/` and export new models from `models/__init__.py` when needed by startup/import paths.
- Prefer existing base mixins such as `AuditBase` when the entity needs audit or soft-delete fields.
- Schema changes must be represented by Alembic migrations under `alembic/versions/`.
- Do not call `Base.metadata.create_all()` for schema evolution; startup only checks connectivity.
- Before creating or editing migrations, inspect current heads with:

```bash
uv run python -m alembic -c alembic.ini heads
```

- Keep migrations reversible with meaningful `upgrade()` and `downgrade()` where feasible.

## Auth and Tenant/Manager Scope

- Manager-protected endpoints should depend on `get_current_active_manager`.
- Use `current_manager.id` as `actor_id`, `created_by`, `deleted_by`, or manager scope when the domain model requires it.
- Do not trust client-provided manager IDs for authorization-sensitive operations.
- Preserve role checks through `require_role_type(...)` when a feature requires restricted access.

## API Naming

- Use REST-style route paths under `/api/v1`.
- Keep route function names verb-based and specific, such as `create_xxx`, `list_xxx`, `get_xxx`, `update_xxx`, `delete_xxx`.
- Prefer service method names that mirror the use case, such as `create_xxx`, `list_xxx`, `get_xxx`, `submit_xxx_job`, or `run_xxx_job`.
- Keep frontend service names compatible with backend DTO and route semantics.

## File and Document Handling

- Reuse helpers in `common/file_storage.py`, `common/file_util.py`, `common/document_types.py`, and `common/document_extraction.py`.
- Validate file extensions and content size consistently with existing constants.
- Do not store uploaded files in new arbitrary directories unless the feature explicitly owns that storage path.

## Verification

After backend changes:

- run a focused compile check, for example:

```bash
uv run python -m compileall backend
```

- run Alembic head validation after migration changes:

```bash
uv run python -m alembic -c alembic.ini heads
```

- import touched routers or services when a narrow check is faster and sufficient
- verify that new routers are registered and response models import cleanly
- avoid leaving unused imports, broken model exports, or migrations that depend on missing models
