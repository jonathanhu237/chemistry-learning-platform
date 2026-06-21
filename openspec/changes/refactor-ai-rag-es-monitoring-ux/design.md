## Context

The current teacher `智能监控` route is a single long dashboard rendered by `AIConfigurationPage.tsx`. It combines at least seven operator tasks in one vertical flow:

- OpenAI-compatible provider health and recent usage.
- RAG/BGE sidecar runtime state.
- ES index health, mapping version, analyzer settings, and document counts.
- Chemistry dictionary metadata.
- Outbox/index sync status.
- Query-level retrieval diagnostics.
- Student AI guardrail state and call trends.

This was appropriate as a first integration pass because it verified that the data is available. It is now a UX problem: the first screen does not answer "what is broken?", and detailed diagnostics are visible before the user chooses a diagnostic task.

The mature pattern from Grafana, Datadog, Elastic/OpenSearch, LangSmith, and Langfuse is consistent: use dashboards for at-a-glance status, group large dashboard areas into tabs/rows, and move troubleshooting into drilldown modules such as traces, logs, service maps, query explainers, or custom dashboards. This change applies that pattern to the teacher console without changing the underlying ES/RAG/AI contracts.

## Goals / Non-Goals

**Goals:**

- Make the first screen fit the main operational answer: OpenAI, RAG, ES, dictionaries/outbox, guardrails, and recent calls are healthy or need attention.
- Split the current long page into task-specific modules with persistent top-level navigation.
- Keep routine status, low-frequency diagnostics, and raw/debug details visually distinct.
- Turn ES retrieval diagnostics into a focused query workbench rather than one panel in a long page.
- Turn dictionary and outbox state into a governance module that explains readiness, freshness, failures, and retryability.
- Preserve existing admin API usage and teacher-only authorization.
- Reduce `AIConfigurationPage.tsx` from a behavior-owning monolith into a composition boundary with route-local modules and hooks.
- Verify responsive layout at normal desktop and narrow laptop widths because this page is dense by nature.

**Non-Goals:**

- Do not change ES mapping, query planner boosts, chemistry vocabulary semantics, outbox semantics, or RAG runtime behavior.
- Do not add dictionary editing in this pass.
- Do not move provider credential editing onto the monitoring page.
- Do not expose raw diagnostic internals to student APIs.
- Do not introduce a third-party observability product or embed Grafana/Kibana.
- Do not create a landing/marketing page; this remains an operational teacher console.

## Decisions

### 1. Use a compact health overview plus module tabs

The route should render a stable header, a compact health strip, an attention summary, and a quick query diagnostic entry before the module detail. Detail modules live behind tabs:

- `总览`
- `OpenAI`
- `RAG`
- `ES 检索`
- `词典与同步`
- `安全护栏`
- `调用趋势`

Rationale: tabs solve the "one screen cannot fit everything" problem while preserving a single route for monitoring. A side navigation inside the page would be heavier than necessary because the teacher app already has a left navigation shell.

Alternative considered: keep one page and collapse cards. Collapses reduce height, but they still make the page feel like a pile of unrelated cards and hide the route's mental model.

### 2. Treat the overview as a triage surface, not a miniature copy of every module

The overview should show status summaries and the next action, not every metric. It should include:

- Six compact status tiles: OpenAI, RAG, ES, dictionary, outbox, guardrail.
- An attention list for warning/error states, such as ES yellow, failed sync rows, stale mapping, unreachable BGE, missing dictionary assets, or recent AI errors.
- A quick query diagnostic input with top result and matched route chips.
- Recent refresh time and manual refresh action.

Rationale: first-screen value comes from prioritization. If every module contributes all fields to the overview, the current long dashboard problem returns.

Alternative considered: show only a grid of service cards. That is tidy but loses the "what do I do now?" action path for ES query debugging, which is the main reason this page exists.

### 3. Keep modules task-oriented

Each tab should answer one operator question:

- `OpenAI`: Is the provider reachable and what is recent usage/error state?
- `RAG`: Is BGE/RAG available, warm, and performing within expected runtime limits?
- `ES 检索`: Why did a point query return these results?
- `词典与同步`: Are dictionary assets, mapping version, document counts, and outbox sync consistent?
- `安全护栏`: Are student AI safety policies active and what outcomes are being produced?
- `调用趋势`: What are usage/error trends over the selected time range?

Rationale: module names should map to user intent rather than backend implementation classes. For example, "词典与同步" groups dictionary assets and outbox because both answer data freshness/readiness.

Alternative considered: split by API endpoint. That would mirror implementation but make the UI harder for teachers/operators to use.

### 4. Make ES retrieval diagnostics a workbench

The ES module should use a three-column or stacked workbench layout depending on viewport:

- Query input and normalized terms: formulae, strict aliases, reagent aliases, condition tags, phenomenon tags, property tags, reaction features.
- Recall routes: named route, route type, fields, boost/weight, enabled state, and route health if available.
- Ranked results: rank, title, score, matched routes, formula/condition/phenomenon chips, and a compact explanation.

Optional raw details such as ES payload or analyzer tokens should be hidden behind a secondary details drawer or disclosure, not shown by default.

Rationale: query diagnostics are interactive troubleshooting, closer to Elastic Discover/OpenSearch trace drilldown than to a passive metric card.

Alternative considered: keep query terms, routes, and results as three stacked blocks in a card. That still requires too much scrolling and makes route-to-result comparison difficult.

### 5. Keep provider and feature configuration outside monitoring

The monitoring page may show links or actions such as `去系统设置` or `查看配置`, but it should not own provider credential forms, API-key saving, feature switches, or dictionary editing.

Rationale: monitoring answers "what is happening?". Settings answers "what should be configured?". Mixing these roles makes the page harder to audit and increases risk of accidental mutations while diagnosing.

Alternative considered: add inline remediation controls everywhere. That may be efficient for power users, but it turns a status page into a high-risk operations console.

### 6. Decompose the frontend by module before adding polish

`AIConfigurationPage.tsx` should become a route composition layer. Route-local ownership should be split into:

- data hooks for AI status, RAG runtime, index diagnostics, and search diagnostics;
- pure mappers for health tone, attention items, dictionary summaries, route chips, and trend data;
- module components for overview, OpenAI, RAG, ES workbench, dictionary/outbox, guardrail, and trends;
- scoped CSS for the monitoring console.

Rationale: the current file already shows monolith pressure. A UX refactor that only moves markup around inside the same component would make future diagnostic additions harder.

Alternative considered: create global dashboard components. The patterns are not yet proven across multiple routes; route-local modules are safer and easier to revise.

### 7. Use restrained operational visual language

This is a teacher/operator tool, not a marketing page. The design should use dense but readable information, compact status tiles, Ant Design tabs, tags, tables/lists, and drawers/disclosures. It should avoid nested cards, oversized hero treatment, and decorative backgrounds.

Rationale: the audience needs to compare states repeatedly. Visual hierarchy should come from status, grouping, and spacing rather than ornament.

Alternative considered: make the page more illustrative. That would reduce operational density and make diagnostics feel less trustworthy.

## Risks / Trade-offs

- [Risk] The overview may become another overloaded dashboard. → Limit it to status, attention items, and quick diagnosis; all detailed fields belong to module tabs.
- [Risk] Moving details behind tabs may hide useful information during incidents. → Keep warning/error indicators and direct tab links in the attention list.
- [Risk] ES diagnostics may still overflow on narrow laptop screens. → Use responsive stacking, stable min-width constraints, wrapping chips, and tables/lists that scroll internally only when appropriate.
- [Risk] Module splitting may introduce duplicated loading/error states. → Centralize query hooks and shared state mappers, then pass typed view models into modules.
- [Risk] Raw DSL/analyzer details may leak into default UI. → Put raw details behind explicit secondary disclosures and keep existing teacher/admin authorization.
- [Risk] Frontend-only refactor may reveal missing diagnostic fields. → Treat missing fields as follow-up backend tasks only if they are necessary for the specified UX; do not broaden the scope into ES redesign.
- [Risk] Existing production chunk warnings may change. → Run typecheck/build and record any new route chunk impact; preserve lazy route boundaries.

## Migration Plan

1. Preserve `/ai-config` route and `智能监控` navigation entry so existing bookmarks continue to work.
2. Extract data hooks and view mappers from the current page without changing API calls or query keys.
3. Introduce the overview and tab shell using the same live diagnostics data.
4. Move existing OpenAI/RAG/ES/dictionary/guardrail/trend UI into module components, reducing visible fields where the spec requires summary-only overview behavior.
5. Add focused frontend tests for tab rendering, status summaries, query diagnostic display, and mapper behavior.
6. Run teacher frontend typecheck/build and browser/screenshot QA for normal desktop and narrow laptop widths.

Rollback is straightforward because this change is UI-only: revert the route-local frontend changes while keeping the existing backend diagnostics and ES/RAG implementation intact.

## Open Questions

- Should tab selection persist in the URL query string, local storage, or remain in local component state for the first implementation?
- Should the quick query diagnostic on the overview reuse the full ES workbench state when the user opens the `ES 检索` tab?
- Should manual outbox retry actions be exposed in `词典与同步` now, or should the first iteration remain read-only with links to existing job controls?
- Should dictionary assets show hashes by default, or only behind a "详情" disclosure for operators?
