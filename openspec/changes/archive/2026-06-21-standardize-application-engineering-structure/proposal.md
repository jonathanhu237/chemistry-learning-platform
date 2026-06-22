## Why

Recent work exposed that the product now moves as one application made of three coupled engineering surfaces: the student H5 frontend, the teacher/admin frontend, and the backend service stack. The backend has just been slimmed into explicit runtime/API/domain/infrastructure/worker ownership, but the frontend structures are less formally governed and the next round of work could easily reintroduce the same kind of coupling in a different layer.

The most important product rule to preserve is semantic page ownership: student root tabs open reusable second-level pages, and a second-level page is defined by navigation semantics rather than by apparent URL depth. For example, the experiment library can be opened from home, and a specific experiment point can be opened from learning cards, search results, related links, or tests without becoming a "third-level" implementation detail.

The repository already has git discipline, production readiness validation, Compose smoke, backend architecture checks, admin e2e smoke, and student mobile QA. This change turns the current engineering shape into explicit OpenSpec requirements so future destructive refactors can be done intentionally instead of by accident.

## Current Investigation

### Student H5 frontend

- Current root: `apps/student-web/src`.
- Existing useful split: `app/router`, `app/shell`, `routes`, `features`, `shared`, `mobile`, `styles`.
- Strong pattern already present: `app/router/navigation.ts` centralizes route semantics such as `navigateToPoint`, `navigateToVideoLibrary`, `navigateToAiChat`, and assessment navigation.
- Current risk: `api.ts` is already 679 lines and mixes many endpoint schemas and request helpers.
- Current risk: several complex feature files are large, especially `features/atom-viewer/AtomViewerZdog.tsx` at 1057 lines and `features/assistant/StudentAiChatPanel.tsx` at 789 lines.
- Current risk: global CSS files remain large and route/feature styling ownership is not yet fully explicit.

### Teacher/admin frontend

- Current root: `apps/admin-web/src`.
- Existing split: `api`, `components`, `features`, `lib`.
- Current risk: `App.tsx` still owns theme, login, auth guard, navigation, route registry, shell layout, and lazy page loading in one 438-line file.
- Current risk: `api/index.ts` is 1235 lines and acts as a monolithic schema/client barrel for unrelated admin domains.
- Current risk: several pages are large page-plus-workflow modules, including `LearningAssistantPage.tsx` at 1267 lines, `ExperimentsPage.tsx` at 1159 lines, `QuestionBanksPage.tsx` at 1065 lines, and `VideoResourcesPage.tsx` at 934 lines.
- Current risk: feature CSS is also large, including `learning-assistant.css` at 1338 lines and global `styles.css` at 1128 lines.

### Backend

- Current root: `server/app`.
- Existing useful split after `backend-slim-domain-architecture`: `app_runtime`, `api`, `domains`, `infrastructure`, `workers`, `scripts_support`.
- Current backend architecture validation already blocks legacy wrappers and forbidden import directions.
- Current risk: some domain files are still intentionally large after the first split, especially `domains/questions/workbench.py`, `domains/student_learning/point_detail.py`, and `domains/assistant/agent.py`.
- Current risk: root-level compatibility-adjacent modules such as schemas, repositories, auth, curriculum, and RAG helpers remain outside the new owner map and need a documented migration posture rather than ad hoc movement.

## What Changes

- Define a repository-level engineering structure contract for the three application surfaces.
- Define student H5 page semantics, route-stack ownership, navigation helper ownership, feature boundaries, API client boundaries, and mobile QA gates.
- Define teacher/admin shell, route registry, feature module, API client, and page decomposition boundaries.
- Extend backend slim architecture expectations so future domain growth is governed by sub-owners, not just top-level package moves.
- Define production engineering governance for structural changes, including when Compose, ES/IK, backend tests, frontend builds, admin e2e, and student mobile QA are required.
- Preserve the policy that destructive refactors are allowed when the spec, validation gates, and git history make rollback clear; do not preserve obsolete wrappers solely for compatibility.

## Capabilities

### New Capabilities

- `application-engineering-structure`: Defines the whole-application owner map and cross-surface dependency posture.
- `student-h5-engineering-structure`: Defines student H5 route-stack, page semantics, feature/API/style ownership, and mobile validation.
- `admin-web-engineering-structure`: Defines teacher/admin shell, route, feature, API, style, and e2e ownership.
- `backend-engineering-structure`: Extends the backend owner map into future module-size and sub-domain ownership rules.
- `production-engineering-governance`: Defines validation gates for structural changes across the whole application.

## Impact

- OpenSpec requirements for future frontend/backend structure work.
- Future refactors in `apps/student-web`, `apps/admin-web`, and `server/app`.
- Future validation scripts and production readiness checks.
- No application code is changed by this proposal.
