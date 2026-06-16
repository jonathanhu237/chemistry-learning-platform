## Context

The current admin learning assistant page is useful for smoke testing, but it does not model the real student experience. It submits one prompt at a time, renders the response as plain text, stores only the latest result in the page, and does not make per-turn guardrails or retrieval behavior easy to inspect. The answer length issue is backend-driven: the agent policy hard-caps answers for the student/mobile use case, and the admin test endpoint currently inherits that cap.

The current RAG path already has structured sources and persisted embeddings. The database contains `source_chunks` and `chunk_embeddings` rows generated with BGE-M3 dimensions. However, live retrieval still primarily uses constrained source selection plus keyword scoring; the streaming fallback path searches with the original student question instead of a clearer generated retrieval query. The requested upgrade is not a corpus rebuild. It is a retrieval-runtime upgrade that adds one optional BGE service path on top of existing sources.

The existing Docker Compose backend bakes source into the image. Any backend code update must be deployed locally by rebuilding the backend image with `docker compose up -d --build backend`; a browser refresh, Vite reload, or plain container restart is insufficient. The new BGE runtime must follow the same explicit Docker service discipline, but it must remain optional when RAG is disabled.

## Goals / Non-Goals

**Goals:**

- Provide an admin-only multi-turn learning assistant debug console with a chat timeline, streaming assistant messages, Markdown display, context controls, and turn-level diagnostics.
- Let admin debug runs return full answers unless an admin/request setting asks for a shorter output. Preserve student-facing safety/length behavior separately.
- Preserve the existing RAG source path while adding AI-generated retrieval queries, BGE-M3 vector recall from existing embeddings, and BGE reranker scoring over merged candidates.
- Run embedding/reranking in a separate optional CPU Docker service. The backend must degrade to existing retrieval when the service is disabled, unavailable, or RAG is off.
- Rename/scope the current AI configuration surface as AI access, with provider credentials separated from feature switches and RAG runtime information.

**Non-Goals:**

- Rebuilding, rechunking, or reimporting the source corpus.
- Replacing the existing keyword/source-constrained retrieval path.
- Making the student mobile chat UI a full Markdown/diagnostics console.
- Requiring GPU hardware for the first implementation.
- Replacing the OpenAI-compatible provider configuration model.

## Decisions

### Decision: Use a three-pane debug console

The admin page will use a configuration/composer area, a multi-turn chat timeline, and a selected-turn inspector. This matches common agent demo/debug UIs: the main chat remains readable while run metadata lives beside it instead of being appended as a long raw block.

Alternatives considered:

- Keep the current form/result split and add sections under the result. This remains one-shot and makes multi-turn debugging awkward.
- Show only raw JSON. This is useful for developers but poor for teachers/admins who need to inspect answer quality first.

### Decision: Treat admin answer length separately from student policy

The backend will add an admin/request-level answer cap override. The learning assistant debug endpoint will default to no fixed hard truncation, while student-facing policy can retain its mobile-friendly limit.

Alternatives considered:

- Remove truncation globally. This risks changing the student experience and token-budget behavior.
- Keep truncation and only expand frontend display height. This does not solve the actual backend hard cut.

### Decision: Add BGE as an optional sidecar-style service

The BGE runtime will be a separate Docker Compose service with embedding and rerank HTTP endpoints. Backend configuration will point to that service when hybrid RAG is enabled. The backend will not depend on this service at container startup; when RAG is disabled, the BGE service does not need to run.

Alternatives considered:

- Install BGE dependencies into the main backend image. This increases image size, memory footprint, cold start time, and couples normal admin routes to ML runtime availability.
- Run BGE inside the frontend or browser. This is not appropriate for BGE reranking and would leak server-side retrieval concerns.

### Decision: Hybrid retrieval preserves existing recall and adds BGE rerank

Retrieval will merge candidates from the existing constrained/keyword recall and vector recall over `chunk_embeddings`. The reranker will score the merged candidate pool and the final evidence list will retain source metadata. If BGE fails, retrieval falls back to the existing source path and records a diagnostic.

Alternatives considered:

- Use only vector search. This can miss exact terms, section IDs, and teacher-provided source filters that the existing path handles well.
- Use only reranker without vector recall. That adds cost without improving recall diversity.

### Decision: Keep AI access distinct from feature controls

The current "AI配置" wording mixes provider credentials, feature switches, and future model-runtime status. The UI will present OpenAI-compatible provider access as "AI接入", keep student AI capability switches in the system settings surface, and show RAG runtime as read-only status on the AI access page. This lets teachers distinguish external API credentials from internal student-facing feature gates.

Alternatives considered:

- Add more controls to the same page without renaming. This keeps the current ambiguity.
- Split every AI concern into separate routes immediately. That adds navigation weight before the settings surface is large enough to justify it.

## Risks / Trade-offs

- [CPU BGE latency] Reranking on CPU can be slow, especially with large candidate pools. Mitigation: start with small recall/rerank limits, expose settings, and fall back gracefully.
- [Memory footprint] BGE-M3 plus BGE reranker can require significantly more RAM than the existing backend. Mitigation: isolate in an optional Docker service and keep it off when RAG is disabled.
- [Streaming diagnostics timing] Some diagnostics are only known at the end of a run. Mitigation: stream answer/status incrementally and send final structured diagnostics in the final event.
- [Markdown safety] Markdown rendering can accidentally enable unsafe HTML. Mitigation: render Markdown without raw HTML support.
- [Retrieval consistency] Hybrid results may differ from previous keyword-only answers. Mitigation: keep existing recall in the candidate pool and expose trace data for comparison.

## Migration Plan

1. Add and validate the OpenSpec artifacts for the new capabilities.
2. Extend backend request/response types for multi-turn history, admin answer cap control, and diagnostics.
3. Add hybrid retrieval hooks with fallback to the current retrieval path.
4. Add the optional BGE CPU Docker service under an explicit Compose profile or otherwise optional startup path. Document that RAG-off deployments do not require this service.
5. Rebuild the backend image with `docker compose up -d --build backend` after backend changes and verify changed routes against `/openapi.json` or focused HTTP checks.
6. Rebuild the frontend debug UI and AI access/settings surface.
7. Run targeted tests and TypeScript checks. Rollback can disable hybrid RAG, stop the BGE service, and return the frontend to the previous endpoint while leaving existing source data unchanged.

## Open Questions

- Exact production limits for vector recall, keyword recall, rerank pool size, and final evidence count should be tuned with teacher/admin testing.
- The first implementation can keep chat sessions local to the admin page; durable saved debug sessions can be added later if teachers need audit history across reloads.
