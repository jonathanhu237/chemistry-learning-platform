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
| Split | `LearningResourcesPage` | `/overview` | `src/features/resources/LearningResourcesPage.tsx` |
| Split | `ClassesPage` | `/classes` | `src/features/classes/ClassesPage.tsx` |
| Split | `ExperimentsPage` | `/experiments` | `src/features/experiments/ExperimentsPage.tsx` |
| Split | `VideoResourcesPage` | `/videos` | `src/features/media/VideoResourcesPage.tsx` |
| Split | `QuestionBanksPage` | `/question-banks` | `src/features/question-bank/QuestionBanksPage.tsx` |
| Split | `AnalyticsPage` | `/analytics` | `src/features/analytics/AnalyticsPage.tsx` |
| Split | `FeedbackPage` | `/feedback` | `src/features/feedback/FeedbackPage.tsx` |
| Split | `LearningAssistantPage` | `/learning-assistant` | `src/features/learning-assistant/LearningAssistantPage.tsx` |
| Split | `SettingsPage` | `/settings` | `src/features/settings/SettingsPage.tsx` |
| Split | `AIConfigurationPage` | `/ai-config` | `src/features/ai-config/AIConfigurationPage.tsx` |

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

- `@ant-design/plots` usage charts are lazy-loaded inside `src/features/ai-config/AIConfigurationPage.tsx`
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

The first-pass style split has been applied. `src/styles.css` now keeps root variables, login/admin shell layout, shared utilities, shared modal/drawer helpers, Ant Design baseline overrides, and shared responsive overrides. Feature-owned styles load from their lazy page chunks:

- `src/features/ai-config/ai-config.css`
- `src/features/classes/classes.css`
- `src/features/experiments/experiments.css`
- `src/features/feedback/feedback.css`
- `src/features/learning-assistant/learning-assistant.css`
- `src/features/media/media.css`
- `src/features/question-bank/question-bank.css`
- `src/features/resources/resources.css`
- `src/features/settings/settings.css`

Current frontend extraction status:

- Done: shared `PageTitle` and `QueryState` -> `src/components/`.
- Done: feedback page -> `src/features/feedback/FeedbackPage.tsx`, lazy-loaded from the `/feedback` route.
- Done: feedback selectors -> `src/features/feedback/feedback.css`, imported by the feedback feature chunk.
- Done: settings page -> `src/features/settings/SettingsPage.tsx`, lazy-loaded from the `/settings` route.
- Done: settings-only selectors -> `src/features/settings/settings.css`; shared `.settings-grid` remains global until learning assistant context layout is split.
- Done: AI config page -> `src/features/ai-config/AIConfigurationPage.tsx`, lazy-loaded from the `/ai-config` route.
- Done: learning-assistant runtime format helpers -> `src/features/learning-assistant/runtimeFormat.ts`, shared by learning assistant diagnostics and AI config.
- Done: analytics page -> `src/features/analytics/AnalyticsPage.tsx`, lazy-loaded from the `/analytics` route.
- Done: shared status/diagnostic display helpers -> `src/lib/status.tsx`, used by analytics and remaining legacy pages.
- Done: resource overview page -> `src/features/resources/LearningResourcesPage.tsx`, lazy-loaded from the `/overview` route.
- Done: resource/media display helpers -> `src/features/resources/resourceUtils.ts`, shared by resource overview and remaining legacy experiment/media pages.
- Done: classes/students page -> `src/features/classes/ClassesPage.tsx`, lazy-loaded from the `/classes` route.
- Done: shared error formatter -> `src/lib/errors.ts`, used by classes and remaining legacy pages.
- Done: videos/media page -> `src/features/media/VideoResourcesPage.tsx`, lazy-loaded from the `/videos` route with Uppy/tus and `hash-wasm` work isolated to the media feature.
- Done: shared authenticated image loader -> `src/components/AuthenticatedImage.tsx`, reused by media and remaining experiment pages.
- Done: experiments page -> `src/features/experiments/ExperimentsPage.tsx`, lazy-loaded from the `/experiments` route.
- Done: shared experiment hooks -> `src/features/experiments/experimentHooks.ts`, reused by experiments and remaining learning-assistant code.
- Done: question bank page and AI workbench UI -> `src/features/question-bank/QuestionBanksPage.tsx`, lazy-loaded from the `/question-banks` route.
- Done: learning assistant page -> `src/features/learning-assistant/LearningAssistantPage.tsx`, lazy-loaded from the `/learning-assistant` route with assistant markdown/KaTeX rendering isolated to the feature.
- Done: global CSS split -> feature CSS files listed above; Vite emits feature CSS chunks for the lazy pages.

## Backend Endpoint Map

Source: `server/app/experiment_admin.py`.

Preserve these endpoint paths while extracting routers:

| Lines | Endpoint Group | Paths | Target Router |
| --- | --- | --- | --- |
| 642-901 | Experiments and experiment media bindings | `/api/admin/experiments*`, `/api/admin/experiment-videos` | `server/app/routers/admin_experiments.py` |
| 2002-2027 | Learning resource overview/framework | `/api/admin/learning-resources/overview`, `/api/admin/experiment-knowledge-framework/overview` | `server/app/routers/admin_learning_resources.py` |
| 2041-2456 | Question bank CRUD/import/export | `/api/admin/question-banks*` excluding workbench/generation | `server/app/routers/admin_question_banks.py` |
| Split | AI generation helpers | generation source loading and local/OpenAI draft helpers | `server/app/services/question_generation_service.py` |
| Split | Point-aware suggestion endpoint and helpers | `/api/admin/question-banks/point-aware-suggestions` | `server/app/routers/admin_point_aware_questions.py` plus `server/app/services/point_aware_question_service.py` |
| Split | Question workbench sessions, turns, candidates | `/api/admin/question-banks/workbench-*` | `server/app/routers/admin_question_workbench.py` plus `server/app/services/question_workbench_service.py` |
| Split | Legacy draft generation endpoints | `/api/admin/question-banks/generate`, `/drafts*` | `server/app/routers/admin_question_generation.py`, `server/app/routers/admin_question_drafts.py` |
| 4615 | Student submit API | `/api/experiment-questions/submit` | `server/app/routers/student_experiment_questions.py` |
| 4832-5177 | Class analytics | `/api/admin/analytics/classes/*` | `server/app/routers/admin_analytics.py` |

Current extraction status:

- Done: student submissions -> `server/app/routers/student_experiment_questions.py`, `server/app/services/student_experiment_service.py`.
- Done: learning resource overview/framework -> `server/app/routers/admin_learning_resources.py`, `server/app/services/learning_resource_service.py`.
- Done: class analytics -> `server/app/routers/admin_analytics.py`, `server/app/services/analytics_service.py`.
- Done: experiments and experiment media bindings -> `server/app/routers/admin_experiments.py`, `server/app/services/experiment_catalog_service.py`.
- Done: question-bank CRUD/import/export -> `server/app/routers/admin_question_banks.py`, `server/app/services/question_bank_service.py`.
- Done: question draft list/update/publish/reject -> `server/app/routers/admin_question_drafts.py`, `server/app/services/question_draft_service.py`.
- Done: shared question generation helpers -> `server/app/services/question_generation_service.py`.
- Done: question generation `/api/admin/question-banks/generate` -> `server/app/routers/admin_question_generation.py`, `server/app/services/question_generation_service.py`.
- Done: point-aware suggestions `/api/admin/question-banks/point-aware-suggestions` -> `server/app/routers/admin_point_aware_questions.py`, `server/app/services/point_aware_question_service.py`.
- Done: question workbench sessions/candidates -> `server/app/routers/admin_question_workbench.py`, `server/app/services/question_workbench_service.py`.
- Remaining: `server/app/experiment_admin.py` is now a compatibility stub only; backend endpoint groups have moved.

Pydantic request models are centralized in `server/app/experiment_admin_schemas.py` during this refactor. A later naming cleanup may move them into `server/app/schemas/experiment_admin.py` or feature-specific schema modules:

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
- `services/question_generation_service.py`: local/OpenAI generation, generation source loading, draft persistence.
- `services/point_aware_question_service.py`: point-aware metadata, source audit, option diagnostics, and point-aware suggestion draft persistence.
- `services/question_workbench_service.py`: RAG gate, session context, evidence package retrieval, turn/candidate lifecycle.
- `services/analytics_service.py`: class dashboard, student report, weak points, exports.
- `services/student_experiment_service.py`: submit answers, grade attempts, progress/events.

## Agent Helper Split

`server/app/agent.py` remains the student assistant orchestration module. Pure reusable helpers have moved out:

- `server/app/services/agent_output_normalization.py`: chemistry/math output contract and LaTeX/mhchem normalization helpers.
- `server/app/services/rag_source_service.py`: RAG source/chunk to evidence payload conversion, asset URL/Markdown helpers, and source serialization used by both the student agent and question workbench.

## Migration Guardrails

- Keep `admin_main.py` router inclusion stable during extraction.
- Each extracted router should preserve the same prefix and tags or include compatibility aliases.
- Move tests or add focused regression tests immediately after moving an endpoint group.
- Run `python scripts/validate_production_resources.py` before and after refactor phases that touch import/resource code.
- Run backend tests for moved endpoints before starting the next endpoint group.
