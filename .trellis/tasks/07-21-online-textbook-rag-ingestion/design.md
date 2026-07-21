# 在线教材 RAG 摄取技术设计

## Architecture

```text
Teacher Admin
  -> Upload API
  -> Textbook blob storage
  -> source_documents + textbook_ingestion_jobs (PostgreSQL)
  -> ingestion worker
       1. native PDF extraction
       2. per-page quality gate
       3. HTTP OCR fallback for rejected pages
       4. structure normalization and chemistry enrichment
       5. stable chunk generation
       6. source_chunks upsert
       7. batch Embedding
       8. Elasticsearch bulk projection
       9. index validation
  -> review and publish
  -> stale/refresh catalog point evidence
  -> existing hybrid retrieval + Rerank
```

The upload request performs only validation, durable file placement and job creation. A separate server-side worker owns long-running processing. This keeps the feature online for the user without coupling processing lifetime to an HTTP request or browser session.

## MVP Corpus Profile

The first release is optimized and accepted against two authoritative books:

| Textbook | PDF profile | Initial extraction route |
| --- | --- | --- |
| 《无机化学（下册）（第二版）》 | 299 pages; text layer on all pages; equations and some cover text need quality checks | Native PyMuPDF extraction, selective OCR only for rejected pages |
| 《无机化学实验（第四版）》 | 240 pages; 239 image-only scan pages; clear Chinese body text with figures, tables and formulae | HTTP OCR for scanned pages |

Only textual RAG content is in MVP scope. Figure numbers, captions and surrounding explanations remain textual evidence, but the ingestion pipeline does not infer the semantics of apparatus drawings or other illustrations.

## Storage Boundaries

### Original files

Introduce a small blob-store abstraction. The initial implementation uses a configured persistent filesystem root and path-containment checks. Its API should allow a future S3-compatible implementation without changing ingestion services.

### PostgreSQL facts

Reuse `source_documents` and `source_chunks` as canonical facts. Add explicit textbook version/lifecycle fields where they are queried or constrained; do not hide all lifecycle state in JSON metadata. Add a dedicated `textbook_ingestion_jobs` table for stage, progress, attempts, cancellation, error details and immutable processing configuration snapshots.

Each upload creates a distinct document version. A stable logical textbook key connects versions, while only one version is active unless the administrator intentionally publishes multiple editions as separate sources.

The two online versions supersede the matching seed-derived canonical documents at publication time. Existing offline chunks remain available as regression fixtures and rollback versions, but retrieval filters prevent simultaneous recall from both generations.

### Elasticsearch projection

Use the existing textbook RAG index contract and add document/version/publication fields needed for filtering. Elasticsearch remains the only location containing dense vectors. PostgreSQL `chunk_embeddings` is a retired compatibility artifact and receives no writes from the online pipeline.

Index a new version before activation. Every worker lease generation writes run-scoped physical ES IDs and a `projection_run_id`; the fenced `review_ready` transition persists that verified run in PostgreSQL. Retrieval filters online documents by the exact `(document_id, document_version, active_projection_run_id)` tuple so PostgreSQL can switch both version and generation atomically after ES validation. A late request from a reclaimed worker may leave an inert historical run, but it cannot overwrite or enter the active projection. Canonical seed documents retain their explicitly registered immutable ES `doc_id` because the legacy precomputed bundle has no version/run fields.

## Processing Contracts

### PDF extractor

The native extractor returns one normalized page record per PDF page:

- page number and dimensions
- plain text and Markdown
- heading/paragraph/table/image blocks when available
- extracted image references
- extractor version and diagnostics

PyMuPDF/`pymupdf4llm` is the primary implementation; `pdfplumber` may be used selectively for table diagnostics. Pages are processed incrementally to bound memory use.

### Page quality gate

Quality is evaluated per page rather than per document. Signals include text length/density, printable character ratio, replacement/control characters, repeated header/footer patterns, suspicious whitespace, and optional parser block coverage. Thresholds are configuration and are captured in the job snapshot.

Rejected pages are sent to OCR. Good native pages never incur OCR cost.

### OCR provider

Define a provider-neutral async HTTP client. The request carries document/job/page identity, an idempotency key and a rendered page image or provider-supported PDF page. The normalized response contains page number, text/Markdown, blocks with coordinates, confidence, warnings and optional asset references.

Provider timeouts, rate limits and transient failures are retryable. Authentication errors, unsupported files and persistent low-confidence output are terminal or require administrator action. The OCR credential remains deployment-managed. The existing DB-backed textbook RAG settings are the authoritative runtime resolver for upload readiness, workers, publication/recovery and retrieval, with environment values as bootstrap defaults. The UI and job records expose only configured status/fingerprints, never raw credentials.

#### Provider recommendation

Use the SYSU AIGW `mineru` alias as the first provider. The gateway catalog describes it as `MinerU2.5-Pro-2604-1.2B` and tags it `本地`/`网络中心`; an authenticated synthetic request independently returned `model: mineru2.5-pro-2604-1.2b`. This resolves the model-version ambiguity, while the gateway's retention, request logging, concurrency and SLA remain operational questions rather than inferred guarantees.

This endpoint is raw OpenAI-compatible page-image inference, not the whole-document MinerU Precision Extract API. The worker renders PDF pages locally and invokes the official two-stage MinerU flow: layout detection first, then cropped text/table/equation recognition. Use the lightweight official HTTP client or its request contract so CPU-only workers do not load the 1.2B model locally. The orchestration layer remains responsible for page mapping, retries, cross-page normalization and final Markdown/block construction.

There is one verified gateway compatibility deviation. Although the official client sends `skip_special_tokens=false`, AIGW returns layout lines such as `080 050 560 083 title` without MinerU's `<|box_start|>`/`<|ref_start|>` tokens. Detection itself was coherent on a synthetic chemistry page, but the stock `mineru-vl-utils` parser rejects the response. The SYSU adapter must accept this strict five-field line format, validate coordinate bounds and block types, and also retain support for the official tokenized format. Malformed or repeated full-page layouts fail the page quality gate instead of being published. Keep this compatibility code isolated so it can be removed if the gateway deployment is corrected.

The same token stripping affects tables. The model returns useful row text, values and LaTeX for all tested tables, but without the HTML/cell boundary tokens expected by the official post-processor; stock `mineru-vl-utils` consequently replaces the table content with an empty string. Capture the raw model response before stock post-processing. If it is non-empty but unstructured, persist it as table text with `table_structure_lost`; if the table prompt is empty, retry the crop once with Text Recognition. Never infer missing cell boundaries silently. Native-text PDFs continue to prefer `pdfplumber`/PyMuPDF table extraction, so this degradation primarily affects scanned pages.

Before full-book processing, submit only a bounded representative page set and compare the normalized output against rendered pages. The set must cover body text, hierarchy, chemical formulae, a table, an experiment procedure, questions and a figure caption. The provider-neutral boundary remains, but the MVP implements only the SYSU MinerU adapter. Baidu AI Cloud Document Parsing (PaddleOCR-VL) is a follow-up only if later reliability or quality evidence invalidates the MinerU gate; the system never runs both providers permanently or indexes duplicate outputs.

#### Representative-page result

The approved benchmark used seven pages from each primary textbook (14 total). Every page completed successfully. Total measured processing time was 45.76 seconds, averaging 3.27 seconds per page with bounded block-level concurrency; this is a connectivity/latency signal, not a full-book throughput or SLA guarantee.

Across the set, all 13 detected equation blocks produced LaTeX, all nine detected table blocks produced non-empty raw content, and figure captions, experiment steps, thinking questions and printed page numbers were readable. The seven text-layer pages had an average normalized sequence similarity of approximately 0.915 against PyMuPDF extraction after reinserting raw table text. Observed errors included `l` versus `1` in one physical-state marker, uncertainty markers in a faint arithmetic layout, and fused table cells. The result passes the MVP text-RAG gate. Exact structured-table reconstruction is explicitly outside MVP scope; fused/flat tables remain visible through `table_structure_lost` quality diagnostics.

Alibaba Cloud Document Mind large-model parsing is the domestic fallback: it supports local-file or URL submission, up to 15,000 pages/150 MB, Markdown/layout output, Chinese VLM OCR and optional formula enhancement. Mistral OCR and Mathpix are secondary overseas candidates; both expose document APIs and structured Markdown, while Mathpix is explicitly STEM/formula-oriented. They require separate network, account, data-location and Chinese-quality evaluation.

Retain self-hosted PaddleOCR-VL on Apple Silicon only as a future privacy fallback. Official documentation verifies M4 local inference and manual full-API deployment, but Docker Compose deployment is not currently supported on that hardware. It is not the default MVP path.

### Chunker and enricher

Chunk by structural blocks with configurable size and overlap. Tables, equations and short safety notices should remain intact where possible. Store parent/previous/next relations, page span, section path and content type. Extract chemistry entities opportunistically, but never discard source text when enrichment fails.

Stable chunk identity combines document version, structural locator and normalized content hash. The content hash plus processing fingerprint enables idempotent reprocessing and Embedding reuse.

## Job State and Recovery

Recommended states:

```text
uploaded
  -> extracting
  -> awaiting_ocr / ocr
  -> structuring
  -> chunking
  -> embedding
  -> indexing
  -> review_ready
  -> ready
```

Any running state can transition to `failed` or `cancelled`. A retry starts from the earliest invalidated artifact rather than blindly repeating all stages. Workers claim jobs using PostgreSQL row locking and leases; stale leases can be reclaimed. Stage outputs are committed in bounded transactions. OCR-complete pages are checkpointed by processing fingerprint, while ES side effects are isolated by lease generation. Publication validates the live run/model/dimension/fingerprint/count rather than trusting historical job counters.

## Publication and Downstream Consistency

Publishing requires a completed quality report and verified ES projection. The transaction switches the active textbook version and creates outbox/job rows that mark affected catalog evidence stale. Evidence refresh may proceed asynchronously and must not roll back the textbook publication.

Deactivation immediately removes the version from retrieval filters. ES physical deletion and file cleanup may happen asynchronously. Destructive file deletion requires an explicit action and audit record.

## Security and Operations

- Restrict upload, retry, publish, deactivate and delete operations to authorized teacher/admin roles.
- Validate MIME using content, not filename alone; set upload size/page limits and never execute embedded PDF content.
- Keep uploaded files and generated assets under a configured root with path containment.
- Do not expose storage paths, provider secrets or raw exception traces to the frontend.
- Attach teacher authorization to Markdown assets only after exact trusted-origin and protected-path validation; textbook/OCR content is untrusted input.
- Exclude the runtime textbook storage root from Git and Docker build contexts.
- Emit structured metrics for stage latency, OCR use/cost, parser quality, Embedding batches, ES failures and retrieval smoke checks.

## Compatibility and Migration

Existing canonical JSONL data can be represented as already-processed source document versions and used for regression tests. The online path should share the same chunk-to-ES projection service as the current indexing script; the script becomes an operator wrapper, not a separate implementation.

For the first two textbooks, use the existing canonical chunks as a golden comparison set for chapter coverage, page ranges, chemistry entities and representative retrieval queries. Do not copy the preprocessed JSONL into the new upload path or treat matching old chunk IDs as proof that the new pipeline succeeded.

Do not drop `chunk_embeddings` in the first migration. Stop all new writes, verify consumers and data retention, then remove the table and pgvector-specific index in a separate cleanup change.

## Key Trade-offs

- Native extraction plus selective OCR reduces cost and latency but requires a reliable page quality gate.
- A PostgreSQL job queue is simpler and matches current project patterns; a distributed queue is deferred until measured throughput requires it.
- Keeping chunk text in PostgreSQL and an ES search projection duplicates searchable text, but preserves a clear fact/projection boundary while maintaining only one vector copy.
- Provider-neutral OCR adds a small adapter layer but prevents the ingestion domain from being coupled to one gateway response shape or the developer laptop.
- The campus MinerU endpoint avoids local model inference and is tagged as locally hosted, but its current special-token stripping requires a compatibility parser and its retention/SLA still need operational confirmation. Baidu is not implemented in the MVP; the provider-neutral contract keeps that follow-up possible without changing ingestion facts or vectors.
- Flat scanned-table text is an accepted MVP degradation because the release target is text-first RAG. Exact row/column semantics can be added after AIGW fixes its output or a later table-specific evaluation justifies another provider.
