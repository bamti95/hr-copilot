---
name: hr-copilot-front-generator
frontend feature-based admin structure, tenant-aware design when applicable, UTF-8 without BOM, and strict build/project safety rules.
---
### Frontend rules
Admin frontend features must follow this structure:

`src/features/manager/{FeatureName}/`
- `components/`
- `hooks/`
- `services/`
- `types/`
- `index.tsx`

Additional frontend rules:
- `index.tsx` is the page controller layer.
- Detailed UI blocks go in `components/`.
- State and page logic go in `hooks/`.
- API calls go in `services/`.
- Types align with backend DTO naming:
  - `XxxRequest`
  - `XxxResponse`
  - `XxxListResponse`
- Do not introduce a global state library unless explicitly requested.

### Encoding and project safety
- All files must be UTF-8 without BOM.
- Do not create or replace Gradle build files unless explicitly requested.
- Do not scaffold a new backend or frontend project.
- Reuse the current repository layout as the source of truth.

### Frontend
Feature folders should follow existing HSBS style, usually PascalCase.

Examples:
- `src/features/admin/AdminFaqCategory/`
- `src/features/admin/AdminPopupBanner/`

### Service function names
Prefer clear verb-based names:

- `fetchXxxList`
- `fetchXxxDetail`
- `createXxx`
- `updateXxx`
- `deleteXxx`
- `updateXxxUseTf`