## Why

The teacher `AI/RAG/ES 监控` page now exposes the right operational data, but it places OpenAI health, RAG runtime, ES index state, dictionary assets, outbox sync, query diagnostics, usage trends, and guardrail policy into one long dashboard. Teachers and operators cannot tell what needs attention in the first screen, and low-frequency diagnostic detail competes with routine health checks.

This change turns the page into a modular monitoring console: a compact health overview first, then task-specific modules for OpenAI, RAG, ES retrieval, dictionaries/sync, safety guardrails, and trends.

## What Changes

- Restructure the teacher `智能监控` route from a single long page into a top-level health overview plus module tabs/sections.
- Add a first-screen summary that shows the health of OpenAI, RAG/BGE, ES, outbox/index sync, dictionary assets, and guardrails without requiring scrolling.
- Move detailed OpenAI provider status, RAG runtime metrics, ES retrieval diagnostics, dictionary/outbox diagnostics, safety guardrail state, and usage trends into separate modules.
- Redesign the ES retrieval diagnostics module as a focused workbench for query input, normalized terms, recall routes, ranking results, and optional raw details.
- Redesign dictionary and outbox monitoring as a governance module that explains dictionary categories, asset versions/hashes, index document counts, sync status, failures, and retry affordances.
- Preserve the existing API boundaries and teacher-only diagnostic access; this change is a frontend UX/information-architecture refactor unless implementation discovers missing fields required to render existing diagnostics clearly.
- Keep provider credentials and feature-switch editing outside the monitoring page, linking to settings only when action is required.
- Add responsive layout requirements so the page works at normal desktop width, narrow laptop width, and smaller teacher-console viewports without card overflow, nested-card clutter, or hidden primary status.

## Capabilities

### New Capabilities

- `teacher-intelligent-monitoring-console`: Defines the modular teacher monitoring console for AI/RAG/ES health, query diagnostics, dictionary/outbox governance, guardrail status, and usage trends.

### Modified Capabilities

- `ai-access-configuration`: The former provider-centric AI access page remains credential/settings-owned, while the teacher route now frames AI/RAG/ES as monitoring-first and links to settings for edits.
- `react-ant-design-admin-console`: The teacher shell navigation and page layout requirements expand to cover the `智能监控` console as a tabbed/module-based operational page with clear first-screen status.
- `frontend-admin-maintainability`: The monitoring page must be split into route-local modules/hooks/components instead of growing the existing `AIConfigurationPage.tsx` monolith.

## Impact

- Teacher frontend route `/ai-config` and navigation label `智能监控`.
- `apps/web-teacher/src/features/ai-config` page composition, local components, hooks, styles, and tests.
- Existing admin APIs already used by the page: AI configuration/status, learning-assistant runtime, video-library index diagnostics, and video-library search diagnostics.
- Visual QA and responsive checks for the teacher monitoring page.
- No intended change to student APIs, ES mapping/query behavior, RAG runtime behavior, provider credential persistence, or chemistry dictionary semantics.
