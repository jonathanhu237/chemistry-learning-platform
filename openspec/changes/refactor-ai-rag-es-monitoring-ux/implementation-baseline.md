## Baseline

- Source screenshot: user-provided capture of the existing `AI/RAG/ES 监控` page, showing the first screen already occupied by OpenAI and RAG panels while ES retrieval begins below the fold.
- Current route: `/ai-config`, navigation label `智能监控`.
- Current implementation before refactor: `apps/web-teacher/src/features/ai-config/AIConfigurationPage.tsx`, 791 lines.
- Current feature CSS before refactor: `apps/web-teacher/src/features/ai-config/ai-config.css`, 1062 lines.

## Data Inventory

- `GET /api/admin/ai-configuration`: provider health, model, API key configured state, status message, usage trends, recent request/error counts, last request summary, student AI policy state, and fallback RAG runtime.
- `GET /api/admin/learning-assistant/runtime`: RAG runtime, BGE health, BGE metrics, model load state, warmup state, memory, uptime, and request counters.
- `GET /api/admin/video-library/index/diagnostics`: ES settings, index name, mapping version, chemistry field readiness, document count, dictionary/analyzer metadata, published content count, and outbox sync status counts.
- `GET /api/admin/video-library/search/diagnostics`: query terms, normalized chemistry fields, route metadata, ranked point-placement results, score, and matched routes.

## Field Sufficiency

- Overview: existing endpoints cover OpenAI, RAG, ES, dictionary, outbox, guardrail, and quick ES diagnostics.
- OpenAI module: existing AI configuration payload is sufficient.
- RAG module: existing learning-assistant runtime payload is sufficient.
- ES retrieval module: existing search diagnostics payload is sufficient for query terms, routes, results, and secondary raw query-plan disclosure.
- Dictionary/outbox module: existing index diagnostics payload is sufficient.
- Guardrail module: existing AI configuration payload is sufficient.
- Trend module: existing AI status `usage_trends` is sufficient.

## Missing Fields

No backend fields are required for the first UX refactor. Raw ES DSL/analyzer token details can remain omitted unless a later diagnostics enhancement explicitly adds them; the current query-plan JSON is enough for a secondary raw disclosure.
