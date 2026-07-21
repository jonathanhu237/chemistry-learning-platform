# 在线教材 RAG 摄取实施计划

## Phase 1: Contracts and schema

- Define textbook document/version, ingestion job, processing fingerprint, quality report and lifecycle contracts.
- Add migrations for document version/lifecycle fields and `textbook_ingestion_jobs`, including claim/lease indexes and state constraints.
- Define blob store, PDF extractor, OCR provider, chunker, embedder and ES projector interfaces.
- Add configuration models for upload limits, storage root, quality thresholds and OCR HTTP settings.
- Add migration/compatibility tests proving existing canonical source documents and chunks remain readable.

## Phase 2: Upload and job orchestration

- Add authorized admin APIs to upload/list/get textbooks and create/cancel/retry processing jobs.
- Implement durable local blob storage with checksum-based duplicate detection, atomic placement and path containment.
- Implement PostgreSQL job claiming, leases, retry policy, cancellation and structured progress events.
- Add a standalone worker entrypoint and development/Compose wiring; do not run long processing inside API requests.
- Add API and service tests for validation, authorization, duplicate upload and job recovery.

## Phase 3: Extraction, OCR and structure

- Implement streaming page extraction with PyMuPDF/`pymupdf4llm`.
- Implement page quality scoring and persist per-page diagnostics.
- Implement the provider-neutral HTTP OCR adapter, normalized response contract, idempotency, retry and redacted errors.
- Implement the SYSU AIGW MinerU adapter first using the `mineru` alias and the official page-image/two-stage request contract; keep a fake provider for deterministic tests and preserve the provider-neutral contract.
- Normalize both official tokenized MinerU layout output and the verified AIGW stripped `x1 y1 x2 y2 type` format. Add fixtures for valid blocks, unknown types, invalid bounds, repetitions and empty output so malformed layouts cannot reach chunking.
- Capture table recognition output before the stock MinerU post-processor. Preserve non-empty plain-text/LaTeX tables, retry empty table output once as text recognition, and emit `table_structure_lost` rather than inventing row/column structure.
- Remove overlapping container blocks (`list`, `image_block`, `equation_block`) from embedding text when their child blocks are present, while retaining parent/child metadata for structure and preview.
- Implement only the SYSU MinerU adapter in the MVP. Keep the provider-neutral interface so Baidu PaddleOCR-VL can be evaluated later if new evidence shows the campus endpoint is insufficient; do not build or operate two adapters preemptively.
- Use free/test quota on a bounded representative page set before any full-book submission. Record quality, latency, API limits and projected cost, then require an explicit full-book-processing action.
- Convert the completed 14-page benchmark into redacted/synthetic contract fixtures; do not commit textbook page images, raw API responses or credentials. Keep an opt-in live integration check behind environment-provided AIGW credentials.
- Merge native and OCR page results deterministically.
- Implement header/footer cleanup, hierarchy recognition, table/equation preservation and chemistry quality flags.
- Test native extraction against 《无机化学（下册）（第二版）》 and HTTP OCR against 《无机化学实验（第四版）》, using bounded page subsets during development and full-book runs for the release gate.

## Phase 4: Chunk facts and review gate

- Implement structure-aware chunks with stable IDs, hashes, page spans and parent/neighbor metadata.
- Upsert `source_documents` and `source_chunks` idempotently in bounded transactions.
- Implement document/chunk quality reports and publish-blocking thresholds.
- Add admin APIs and UI for processing progress, chapter/chunk preview, diagnostics and retry.
- Add unit and integration tests for unchanged, changed and removed chunks during reprocessing.

## Phase 5: Embedding and single ES vector projection

- Extract the existing ES mapping/indexing code into a reusable application service.
- Batch Embedding with retry, model/dimension validation and fingerprint-based reuse.
- Bulk index staged document versions into the existing hybrid text/vector index.
- Ensure online ingestion never writes `chunk_embeddings`; add a regression check for this boundary.
- Validate ES counts, failed items, index metadata and representative retrieval before marking the job `review_ready`.

## Phase 6: Publication and lifecycle

- Implement publish, deactivate, replace and explicit delete flows.
- Make retrieval filter by active document versions so publishing can switch versions atomically.
- Mark dependent catalog point evidence stale and enqueue refresh work after publication/deactivation.
- Remove staged/orphan ES documents after failed, cancelled or superseded jobs.
- Add audit records and tests covering rollback, retry and partial ES/OCR failures.

## Phase 7: End-to-end UX and verification

- Complete the teacher/admin textbook management page with upload, progress, preview, publish, test, deactivate and delete actions.
- Add an end-to-end test: upload PDF -> process -> preview -> publish -> hybrid retrieve with page citation.
- Add a scanned-PDF test that proves selective OCR and a provider-unavailable test that proves publication is blocked.
- Run full-book acceptance for both primary textbooks and compare chapter/page coverage plus representative retrieval results against the existing canonical chunks.
- Verify that publishing the two online versions excludes the corresponding seed-derived versions from retrieval and that rollback restores them without reimporting JSONL.
- Run backend tests, frontend typecheck/tests/build, architecture validation and production readiness checks.
- Document deployment storage, worker startup, OCR configuration, retry/rebuild and incident recovery.

## Validation Focus

- No request waits for full-document processing.
- No vectors are written to PostgreSQL by the new path.
- Reprocessing is idempotent and does not leak ES documents.
- A partially processed version is never visible to retrieval.
- Every retrieved chunk can be traced to document version, section and PDF page range.
- OCR secrets are redacted and uploaded paths cannot escape the configured storage root.

## Validation Commands

- Fast backend loop: `python -m pytest server/tests -q`
- Backend dependency boundaries: `python scripts/validate_backend_architecture.py`
- Teacher UI boundaries and correctness: `cd apps/web-teacher && npm run validate:boundaries && npm run typecheck && npm test && npm run build`
- Compose definition after worker/storage wiring: `docker compose config`
- Full repository release gate: `python scripts/validate_production_readiness.py`
- Opt-in live MinerU contract check to add during Phase 3: `SYSU_MINERU_LIVE_TEST=1 python -m pytest server/tests/test_textbook_ingestion_mineru_live.py -q`; credentials are supplied only through the environment and the test skips by default.

## Rollback Points

- Schema additions are backward compatible; existing offline seed import remains available during rollout.
- Online retrieval activation is guarded by document-version publication state and can be disabled without deleting facts.
- ES projections are rebuildable from PostgreSQL chunks; originals remain intact unless explicitly deleted.
- `chunk_embeddings` removal is a separate follow-up only after consumer verification.
