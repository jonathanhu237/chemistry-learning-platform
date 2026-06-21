## 1. Baseline and UX Inventory

- [x] 1.1 Capture the current `智能监控` page at normal desktop and narrow laptop widths to record overflow, scroll depth, and information-density problems.
- [x] 1.2 Inventory the existing data sources used by `AIConfigurationPage.tsx`: AI configuration, learning-assistant runtime, video-library index diagnostics, and video-library search diagnostics.
- [x] 1.3 Confirm which fields are already sufficient for the overview, OpenAI, RAG, ES retrieval, dictionary/outbox, guardrail, and trend modules.
- [x] 1.4 Identify any missing diagnostic fields needed for the specified UX and either map them to existing payloads or document a narrowly scoped backend follow-up.

## 2. Module Architecture

- [x] 2.1 Create a route-local monitoring module structure under `apps/web-teacher/src/features/ai-config` for overview, OpenAI, RAG, ES retrieval, dictionary/outbox, guardrail, trends, hooks, mappers, and shared UI helpers.
- [x] 2.2 Extract data fetching into route-local hooks while preserving existing endpoints, query keys, refetch intervals, enabled conditions, and error behavior.
- [x] 2.3 Extract pure view mappers for health tone, subsystem status, attention items, dictionary summaries, route chips, ranked result summaries, and trend chart data.
- [x] 2.4 Convert `AIConfigurationPage.tsx` into a composition boundary that owns page state, module navigation, and high-level query wiring rather than all module markup.

## 3. Overview and Module Navigation

- [x] 3.1 Implement the first-screen overview with compact status tiles for OpenAI, RAG/BGE, ES, dictionary assets, outbox/index sync, and guardrails.
- [x] 3.2 Implement the `需要关注` attention area with direct navigation to the affected module for warning, error, stale, failed, missing, degraded, or unavailable states.
- [x] 3.3 Add last-refresh and manual-refresh affordances that refresh the relevant monitoring queries without forcing a full page reload.
- [x] 3.4 Implement stable module navigation for `总览`, `OpenAI`, `RAG`, `ES 检索`, `词典与同步`, `安全护栏`, and `调用趋势`.
- [x] 3.5 Ensure each module has localized loading, empty, and error states with retry support.

## 4. Detail Modules

- [x] 4.1 Build the OpenAI module with connectivity, model, API key configured state, AI channel, request/error counts, check times, last request summary, and settings-link remediation without inline credential editing.
- [x] 4.2 Build the RAG module with BGE service state, RAG mode, query generation state, retrieval/rerank/final counts, service URL, latency, model load state, memory, uptime, warmup, model paths, and error display.
- [x] 4.3 Build the ES retrieval workbench with query input, normalized terms, formulae, strict aliases, feature tags, route list, ranked point-placement results, score, matched routes, and empty/error states.
- [x] 4.4 Add a secondary disclosure, drawer, or details surface for raw ES/analyzer diagnostics when available, keeping raw details out of the default ES workbench view.
- [x] 4.5 Build the dictionary/outbox module with dictionary category counts, analyzer asset state, mapping version, desired mapping version, ES document count, published point-content count, sync status counts, and retry/readiness presentation.
- [x] 4.6 Build the safety guardrail module with policy version, active state, recent decision count, invalid decision count, handled risk count, and outcome distribution.
- [x] 4.7 Build the trend module with selectable ranges for AI calls/errors and a readable chart or fallback table.

## 5. Responsive Visual Polish

- [x] 5.1 Replace nested-card stacks with module layouts using compact status tiles, tags, lists/tables, alerts, and disclosures scoped to the monitoring page.
- [x] 5.2 Add responsive CSS so overview status tiles and module layouts wrap or stack at narrow laptop widths without horizontal page scrolling.
- [x] 5.3 Ensure long values such as model paths, service URLs, formula signatures, route names, dictionary hashes, and result titles truncate, wrap, or disclose without overlap.
- [x] 5.4 Keep page copy operational and compact; avoid visible instructional text that explains how to use obvious controls.
- [x] 5.5 Preserve the existing teacher console visual language, Ant Design theme, compact 8px-or-less radius, and restrained operational styling.

## 6. Tests and Verification

- [x] 6.1 Add focused tests for health-tone mapping, attention item generation, dictionary/outbox summary mapping, route/result mapping, and query diagnostic empty/error behavior where feasible.
- [x] 6.2 Add component or behavior tests that verify module navigation renders the expected modules and does not duplicate all detail content in one long page.
- [x] 6.3 Run `npm run typecheck` in `apps/web-teacher` and fix any TypeScript regressions.
- [x] 6.4 Run `npm run build` in `apps/web-teacher` and document any new or changed production chunk warnings.
- [x] 6.5 Use browser or screenshot QA to inspect the overview, ES retrieval module, dictionary/outbox module, and RAG module at normal desktop width.
- [x] 6.6 Use browser or screenshot QA to inspect the overview and ES retrieval module at narrow laptop width, verifying no text overlap, clipped controls, or unusable horizontal scrolling.

## 7. Runtime Smoke Check

- [x] 7.1 Rebuild and restart the `web-teacher` container or dev server after implementation so the running UI reflects the refactor.
- [x] 7.2 Verify the running teacher console still opens `/ai-config` from the `智能监控` navigation entry.
- [x] 7.3 Run a live ES diagnostic query such as `H2O2 KMnO4 酸性` and confirm the ES module shows normalized formulae, condition tags, recall routes, and the expected top result.
- [x] 7.4 Verify provider settings and feature switches remain outside the monitoring modules and are reachable only through the existing settings or credential-management path.
