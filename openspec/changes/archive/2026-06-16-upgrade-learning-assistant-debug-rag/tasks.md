## 1. Spec and Baseline

- [x] 1.1 Validate the OpenSpec change before implementation.
- [x] 1.2 Inspect current learning assistant, AI access, and retrieval code paths to preserve existing behavior.

## 2. Backend Agent and Retrieval

- [x] 2.1 Extend learning assistant request/response types for conversation history, admin answer length control, and retrieval diagnostics.
- [x] 2.2 Remove backend hard truncation for admin debug runs while preserving student policy behavior.
- [x] 2.3 Add AI-generated retrieval query support with fallback to the original user question.
- [x] 2.4 Add hybrid retrieval that merges existing keyword/source recall with BGE vector recall and optional BGE reranking.
- [x] 2.5 Return turn-level diagnostics for guardrails, tool calls, generated queries, recall, rerank, and final evidence.

## 3. Optional BGE CPU Service

- [x] 3.1 Add a separate BGE embedding/reranking HTTP service implementation.
- [x] 3.2 Package the BGE service as an optional Docker Compose service that is not required when RAG is disabled.
- [x] 3.3 Add backend configuration for enabling hybrid RAG and pointing at the BGE service URL.

## 4. Frontend Debug Console and AI Access

- [x] 4.1 Add frontend API types and streaming handling for multi-turn responses and diagnostics.
- [x] 4.2 Rebuild the learning assistant page as a multi-turn chat debug console with Markdown rendering and selected-turn inspector.
- [x] 4.3 Rename/scope the AI provider page as AI access and separate provider credentials from feature/RAG controls.

## 5. Validation and Local Runtime

- [x] 5.1 Run OpenSpec validation for the change.
- [x] 5.2 Run frontend typecheck/build and focused backend tests or compile checks.
- [x] 5.3 Rebuild the backend Docker image with `docker compose up -d --build backend` and verify changed routes against the running backend.

## 6. RAG Observability Polish

- [x] 6.1 Add per-stage RAG timing, candidate counts, rerank-applied flags, and ranked final evidence diagnostics.
- [x] 6.2 Add BGE sidecar process/runtime metrics and expose them through an admin-only learning assistant runtime endpoint.
- [x] 6.3 Show rerank status, timing, source ranks/scores, and BGE runtime performance in the learning assistant debug console.
- [x] 6.4 Add BGE startup warmup and surface warmup readiness in the learning assistant debug console.
