## Why

The learning assistant admin test page is still a one-shot form: it hard-truncates answers in the backend, shows model output as plain text, hides multi-turn context, and makes per-turn guardrail/RAG behavior hard to inspect. At the same time, the corpus already has BGE-M3 embeddings, but the live RAG path still behaves like a keyword-first recall flow and the optional CPU model runtime is not separated from the main backend.

## What Changes

- Rebuild the admin learning assistant test surface into a multi-turn debug console with chat history, streaming output, Markdown rendering, and a per-turn diagnostics inspector.
- Remove the admin debug hard answer truncation; output length should be controlled by admin/request settings rather than the student mobile policy cap.
- Preserve the existing learning assistant RAG source path, then add an optional BGE-M3 query/vector recall path and BGE reranker path for merged candidate reranking.
- Add a separate CPU Docker service for BGE embedding/reranking. The main backend must work when this service is not started, especially when RAG is disabled.
- Rename the current AI configuration navigation/page toward AI access, keeping OpenAI-compatible provider credentials distinct from feature toggles and RAG runtime settings.
- Expose RAG query, recall, rerank, source, guardrail, and tool-call diagnostics in admin-facing debug results.

## Capabilities

### New Capabilities

- `learning-assistant-debug-console`: Admin-only multi-turn learning assistant test console, Markdown output, no admin hard truncation, and turn-level diagnostics.
- `hybrid-bge-rag-retrieval`: Optional BGE-M3 vector recall plus BGE reranking over existing sources, with fallback behavior and diagnostics.
- `ai-access-configuration`: AI provider access page naming/scope and separation from feature/RAG runtime controls.

### Modified Capabilities

- None.

## Impact

- Frontend: `apps/admin-web/src/App.tsx`, `apps/admin-web/src/api.ts`, `apps/admin-web/src/styles.css`, and package dependencies if Markdown rendering needs a library.
- Backend: learning assistant admin endpoints, agent request/response schemas, retrieval path, RAG diagnostics, and configuration settings.
- Infrastructure: `docker-compose.yml`, optional BGE CPU service image/files, and documented local rebuild behavior for backend changes.
- Tests/specs: OpenSpec validation, focused backend tests, TypeScript checking, and local Docker backend rebuild/route verification.
