---
name: hr-copilot-front-generator
description: Frontend feature generation and maintenance for the HR Copilot React/Vite admin app. Use when adding or modifying manager/admin frontend features, API services, hooks, DTO-aligned types, UI harnesses, and project-safe frontend code.
---

# HR Copilot Frontend Skill

이 스킬은 기존 HR Copilot 프론트엔드 구조를 유지하면서 manager/admin 기능을 추가하거나 수정하기 위한 작업 기준이다. 새 프로젝트를 만들지 말고, 현재 repository layout과 주변 feature 구현을 source of truth로 사용한다.

## Project Safety

- Reuse the current repository layout. Do not scaffold a new frontend project.
- Do not create or replace Gradle/backend build files from frontend work.
- Keep all files UTF-8 without BOM.
- Do not introduce a global state library unless explicitly requested.
- Do not add new test/mock/storybook dependencies unless explicitly requested.
- Before changing a feature, inspect nearby files in `src/features/manager` and shared utilities in `src/common`.

## Feature Structure

Manager frontend features should follow this structure:

```txt
src/features/manager/{FeatureName}/
- components/
- hooks/
- services/
- types/
- index.tsx
```

Feature folders should follow the existing HSBS style, usually PascalCase.

Examples:

- `src/features/manager/Candidate/`
- `src/features/manager/JobPosting/`
- `src/features/manager/LlmUsageDashboard/`

Additional folders are allowed when the feature already needs them, such as:

- `pages/` for feature-internal route pages
- `constants/` for stable constants
- `utils/` for feature-local helpers
- `harness/` for dev-only UI fixtures or mock pages

## Layer Responsibilities

- `index.tsx` is the page controller layer: route/page composition, hook wiring, and top-level loading/error/empty branching.
- `components/` contains detailed UI blocks and presentational components.
- `hooks/` contains state, effects, polling, form logic, and page-level orchestration.
- `services/` contains API calls only.
- `types/` contains DTO-aligned types and feature-local view types.
- `utils/` contains pure feature-local helpers.

Move code to `src/common` only when multiple features actually reuse it.

## Existing Project Conventions

- Use the shared axios instance from `src/services/api.ts` for HTTP calls.
- Reuse common UI from `src/common/components` when applicable, including table/layout primitives.
- Follow the existing manager/admin layout and visual density.
- Prefer local feature state for filters, forms, tabs, modals, selected rows, and transient UI state.
- If tenant/manager scoping is present in the backend API, preserve it in service calls and avoid client-side bypasses.

## DTO and Service Naming

Types should align with backend DTO naming:

- `XxxRequest`
- `XxxResponse`
- `XxxListResponse`

Prefer clear verb-based service names:

- `fetchXxxList`
- `fetchXxxDetail`
- `createXxx`
- `updateXxx`
- `deleteXxx`
- `updateXxxUseTf`

Service functions should return typed response data and keep transformation minimal. Put display formatting in components or feature-local utils, not in API services.

## UI and UX Rules

- Build admin screens for scanning, comparison, and repeated operation.
- Prefer compact, predictable layouts over landing-page or marketing composition.
- Use `lucide-react` icons for icon buttons when an icon exists.
- Avoid nested cards and decorative-only UI.
- Make loading, empty, error, and success states explicit.
- Ensure long Korean/English text does not overflow buttons, tables, cards, or narrow screens.
- Keep detailed rendering out of `index.tsx` once the JSX becomes hard to scan.

## Dev Harness Rules

Use a dev harness when UI behavior is complex, backend integration is unavailable, or visual/manual verification is needed.

Preferred locations:

- Shared harness utilities: `src/dev-harness/`
- Feature fixtures: `src/features/manager/{FeatureName}/harness/`

Harness code should:

- use realistic DTO-shaped fixture data
- cover success, loading, empty, and error states
- avoid real backend calls
- be gated by `import.meta.env.DEV` or excluded from production navigation
- not be added to production routes unless explicitly requested
- not introduce Vitest, Testing Library, MSW, Storybook, or other harness dependencies unless explicitly requested

## Verification

After frontend changes:

- run `npm run build`
- run `npm run lint` when relevant
- for visual UI changes, verify the screen in a local Vite dev server when possible
- check for unused imports, broken route imports, dead harness routes, and type mismatches
