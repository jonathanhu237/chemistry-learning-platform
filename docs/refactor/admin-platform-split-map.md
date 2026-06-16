# Admin Platform Split Map

This map records the current large-file boundaries before behavior-preserving modularization. It should be updated when a route or endpoint is moved, and each move should keep existing route paths, endpoint paths, permissions, and payload shapes stable.

## Frontend Route Map

Source: `apps/admin-web/src/App.tsx`.

Current shell and route components:

| Lines | Component | Route | Target Module |
| --- | --- | --- | --- |
| 281 | `App` | top-level router | `src/app/App.tsx` |
| 343 | `LoginPage` | `/login` | `src/pages/LoginPage.tsx` |
| 408 | `ProtectedShell` | authenticated layout | `src/app/ProtectedShell.tsx` |
| 1561 | `LearningResourcesPage` | `/overview` | `src/features/resources/LearningResourcesPage.tsx` |
| 1744 | `ClassesPage` | `/classes` | `src/features/classes/ClassesPage.tsx` |
| 2349 | `ExperimentsPage` | `/experiments` | `src/features/experiments/ExperimentsPage.tsx` |
| 3467 | `VideoResourcesPage` | `/videos` | `src/features/media/VideoResourcesPage.tsx` |
| 4585 | `QuestionBanksPage` | `/question-banks` | `src/features/question-bank/QuestionBanksPage.tsx` |
| 5603 | `AnalyticsPage` | `/analytics` | `src/features/analytics/AnalyticsPage.tsx` |
| 5853 | `FeedbackPage` | `/feedback` | `src/features/feedback/FeedbackPage.tsx` |
| 6955 | `LearningAssistantPage` | `/learning-assistant` | `src/features/learning-assistant/LearningAssistantPage.tsx` |
| 7802 | `SettingsPage` | `/settings` | `src/features/settings/SettingsPage.tsx` |
| 8137 | `AIConfigurationPage` | `/ai-config` | `src/features/ai-config/AIConfigurationPage.tsx` |

Redirects to preserve:

- `/` -> `/overview`
- `/curriculum` -> `/experiments`
- `/review` -> `/question-banks`

## Frontend Shared Extraction Map

Keep these as shared modules before moving page bodies:

- `src/api/`: existing `api.ts`, generated API types, auth helpers, query key helpers.
- `src/app/`: shell layout, nav items, route definitions, auth guard, theme provider.
- `src/components/`: `PageTitle`, `QueryState`, `AIGlowButton`, shared tags, shared media thumbnail pieces.
- `src/lib/format/`: `formatDateTime`, `formatBytes`, status labels, question labels, source-ref labels.
- `src/lib/assistant-markdown/`: markdown normalization, KaTeX/mhchem rendering, image resolution, `AssistantMarkdownContent`.
- `src/features/resources/`: periodic table/resource overview widgets, experiment framework panel, source workspace.
- `src/features/question-bank/`: question list/detail, workbench gate, workbench drawer, candidate validation/publish controls.
- `src/features/media/`: upload queue, Uppy/tus setup, duplicate handling, thumbnails, video preview.

Heavy dependencies currently imported at the top of `App.tsx` and suitable for lazy feature chunks:

- `@ant-design/charts` via `UsageLineChart`
- `katex`, `katex/contrib/mhchem`, `react-markdown`, `remark-gfm`, `remark-math`
- `@uppy/core`, `@uppy/tus`, `hash-wasm`
- learning-assistant diagnostics and image preview code

## Frontend Style Split Map

Source: `apps/admin-web/src/styles.css`.

Suggested first-pass style files:

- `src/styles/base.css`: `:root`, `body`, `#root`, Ant Design baseline overrides.
- `src/styles/layout.css`: `.admin-shell`, sider/header/content, collapsed nav, page title.
- `src/features/classes/classes.css`: `.class-*`.
- `src/features/experiments/experiments.css`: `.experiment-*`, `.video-point-*` used inside experiments.
- `src/features/media/media.css`: `.video-*`, upload queue, preview, duplicate panel.
- `src/features/question-bank/question-bank.css`: `.question-*`, workbench status/detail/evidence.
- `src/features/resources/resources.css`: `.resource-*`, `.experiment-framework-*`, periodic table/workbench.
- `src/features/feedback/feedback.css`: `.feedback-*`.
- `src/features/learning-assistant/learning-assistant.css`: `.assistant-*`, markdown, chat, diagnostics.

Split CSS after component extraction so selectors can move with their owning feature and visual behavior can be compared page-by-page.

## Backend Endpoint Map

Source: `server/app/experiment_admin.py`.

Preserve these endpoint paths while extracting routers:

| Lines | Endpoint Group | Paths | Target Router |
| --- | --- | --- | --- |
| 642-901 | Experiments and experiment media bindings | `/api/admin/experiments*`, `/api/admin/experiment-videos` | `server/app/routers/admin_experiments.py` |
| 2002-2027 | Learning resource overview/framework | `/api/admin/learning-resources/overview`, `/api/admin/experiment-knowledge-framework/overview` | `server/app/routers/admin_learning_resources.py` |
| 2041-2456 | Question bank CRUD/import/export | `/api/admin/question-banks*` excluding workbench/generation | `server/app/routers/admin_question_banks.py` |
| 2456-2968 | AI generation and point-aware suggestions helpers | generation source loading, local/OpenAI suggestion helpers | `server/app/services/question_generation_service.py` |
| 2969-4118 | Question workbench sessions, turns, candidates | `/api/admin/question-banks/workbench-*` | `server/app/routers/admin_question_workbench.py` plus `services/question_workbench_service.py` |
| 4295-4518 | Legacy draft generation endpoints | `/api/admin/question-banks/generate`, `/drafts*` | `server/app/routers/admin_question_drafts.py` |
| 4615 | Student submit API | `/api/experiment-questions/submit` | `server/app/routers/student_experiment_questions.py` |
| 4832-5177 | Class analytics | `/api/admin/analytics/classes/*` | `server/app/routers/admin_analytics.py` |

Current extraction status:

- Done: student submissions -> `server/app/routers/student_experiment_questions.py`, `server/app/services/student_experiment_service.py`.
- Done: learning resource overview/framework -> `server/app/routers/admin_learning_resources.py`, `server/app/services/learning_resource_service.py`.
- Done: class analytics -> `server/app/routers/admin_analytics.py`, `server/app/services/analytics_service.py`.
- Done: experiments and experiment media bindings -> `server/app/routers/admin_experiments.py`, `server/app/services/experiment_catalog_service.py`.
- Done: question-bank CRUD/import/export -> `server/app/routers/admin_question_banks.py`, `server/app/services/question_bank_service.py`.
- Done: question draft list/update/publish/reject -> `server/app/routers/admin_question_drafts.py`, `server/app/services/question_draft_service.py`.
- Remaining: question generation `/api/admin/question-banks/generate`, question workbench sessions/candidates, point-aware suggestions, and shared question-generation helpers.

Pydantic request models currently defined at the top of the file should move into `server/app/schemas/experiment_admin.py` or feature-specific schema modules before router extraction:

- `ExperimentCreateRequest`, `ExperimentUpdateRequest`, `ExperimentChapterBinding`
- `QuestionRequest`, `QuestionUpdateRequest`, `GenerationRequest`
- `QuestionBankAssistantRequest`, `PointAwareSuggestionRequest`
- `WorkbenchSessionRequest`, `WorkbenchMessageRequest`, `DraftUpdateRequest`
- `ExperimentQuestionSubmitRequest`, `ExperimentAnswer`
- media binding request models

## Backend Service Extraction Map

Prefer service extraction before router moves when helper functions are shared by multiple endpoints:

- `services/experiment_catalog_service.py`: experiment listing, chapter bindings, formal catalog counts, video point derivation.
- `services/media_binding_service.py`: experiment video/resource bindings, media asset lookup and point resource operations.
- `services/learning_resource_service.py`: resource dashboard stats, framework overview, chapter/unit/kp listing.
- `services/question_bank_service.py`: question payload validation, bank CRUD, imports/exports, source ref attachment.
- `services/question_generation_service.py`: local/OpenAI generation, point-aware metadata, source audit and option diagnostics.
- `services/question_workbench_service.py`: RAG gate, session context, evidence package retrieval, turn/candidate lifecycle.
- `services/analytics_service.py`: class dashboard, student report, weak points, exports.
- `services/student_experiment_service.py`: submit answers, grade attempts, progress/events.

## Migration Guardrails

- Keep `admin_main.py` router inclusion stable during extraction.
- Each extracted router should preserve the same prefix and tags or include compatibility aliases.
- Move tests or add focused regression tests immediately after moving an endpoint group.
- Run `python scripts/validate_production_resources.py` before and after refactor phases that touch import/resource code.
- Run backend tests for moved endpoints before starting the next endpoint group.
