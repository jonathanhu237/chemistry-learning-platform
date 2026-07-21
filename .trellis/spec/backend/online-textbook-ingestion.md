# Online Textbook Ingestion and RAG Contract

## Scenario: Admin-managed online textbook processing

### 1. Scope / Trigger

Apply this contract when changing any of the following:

- `/api/admin/ai-configuration` textbook OCR, Embedding, or Rerank settings;
- textbook upload, worker, recovery, preview, quality, or publication behavior;
- the SYSU AIGW MinerU adapter or OpenAI-compatible Embedding/Rerank clients;
- the Elasticsearch textbook projection or active-corpus retrieval filter.

The online path owns uploaded PDF processing. PostgreSQL is the fact store, while Elasticsearch is the only vector store. Runtime ingestion must never add rows to `chunk_embeddings`.

### 2. Signatures

#### Admin APIs

```text
GET  /api/admin/ai-configuration
PUT  /api/admin/ai-configuration

GET  /api/admin/textbooks/upload-policy
POST /api/admin/textbooks                         # multipart: title, file, optional logical_textbook_key/version_label
GET  /api/admin/textbooks/{document_id}
GET  /api/admin/textbooks/{document_id}/pages
GET  /api/admin/textbooks/{document_id}/chunks
GET  /api/admin/textbooks/jobs/{job_id}
POST /api/admin/textbooks/jobs/{job_id}/retry
POST /api/admin/textbooks/jobs/{job_id}/cancel
POST /api/admin/textbooks/{document_id}/publish
POST /api/admin/textbooks/{document_id}/deactivate
DELETE /api/admin/textbooks/{document_id}
```

#### Persistence and projection identity

```text
source_documents.logical_textbook_key
source_documents.version_number
source_documents.publication_status
source_documents.active_projection_run_id

textbook_ingestion_jobs.config_snapshot
textbook_ingestion_jobs.quality_report
textbook_ingestion_jobs.outputs.projection_run_id

Elasticsearch identity/filter tuple:
(document_id, document_version, projection_run_id)
```

Each worker lease writes a run-scoped projection. Only the run recorded by the fenced `review_ready` transition may become active.

#### External provider calls

```text
OCR:       OpenAI-compatible chat completions with rendered page images
Embedding: OpenAI-compatible /embeddings
Rerank:    configured endpoint, for example /reranks for qwen3-rerank
```

### 3. Contracts

#### Runtime configuration

- The DB-backed `ai_configuration.textbook_rag` payload is authoritative for API, worker, recovery, publication, and retrieval. Environment variables are bootstrap defaults only.
- OCR, Embedding, and Rerank providers are independent admin-configurable roles. Do not hard-code a campus or cloud endpoint into the pipeline.
- Secrets are write-only. Read responses expose only `credential_configured` and a non-secret fingerprint; logs, jobs, API errors, and frontend state must not contain API keys.
- A job captures an immutable processing snapshot, including OCR `max_output_tokens`, OCR concurrency/retries/render DPI, Embedding dimension and `batch_size`, models, endpoints, and configuration fingerprints.
- Bootstrap environment keys include `TEXTBOOK_OCR_*`, `TEXTBOOK_EMBEDDING_BATCH_SIZE`, and `TEXTBOOK_RAG_{ELASTICSEARCH,EMBEDDING,RERANK}_*`. Keep `.env.example`, backend models, admin DTOs, frontend types/forms, and snapshot parsing synchronized.

#### MinerU page normalization

- Accept both official tokenized MinerU layout output and the SYSU AIGW stripped layout form. Stripped records must still pass coordinate and block-type validation.
- Preserve non-empty raw table text before stock post-processing. If cell/HTML tokens are absent, store searchable text and add `table_structure_lost`; do not invent cell boundaries.
- An empty table recognition result must retry through text recognition. It may terminate as `ocr_empty_table`; it must not silently delete the page's only searchable content.
- `finish_reason=length` is incomplete output. Retry with the configured output budget instead of accepting a truncated block.
- A page is exempt from the empty-page blocker only when the OCR adapter emits both `ocr_confirmed_blank_page` and `diagnostics.blank_page_detection.confirmed=true`. The current detector requires all strict luma, deviation, off-white-pixel, and dark-pixel thresholds to pass. A faint low-contrast page is not blank.

#### Embedding and Rerank responses

- If every item omits `index`, preserve sequential response order.
- If indexes are present, every item must have one and the indexes must form exactly `0..N-1`; reorder by index before returning values.
- Reject mixed indexed/sequential responses, non-integer/negative/out-of-range/duplicate indexes, missing indexes, and result-count mismatches. Never silently fill a missing embedding or Rerank score.

#### Publication and retrieval

- `review_ready` requires a publishable quality report, exact chunk/Embedding/index counts, matching model/dimension/profile metadata, and a verified projection run.
- Publishing changes source chunks to `content_status=published`, clears `review_required`, advances the corpus revision, and activates the exact run tuple.
- Retrieval must obtain the active corpus from PostgreSQL and filter Elasticsearch by exact active tuples. A staged, failed, inactive, old-version, or stale-worker run must be invisible.
- Text and metadata may exist in both PostgreSQL facts and the Elasticsearch projection, but dense vectors exist only in Elasticsearch.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| OCR is required but disabled or incomplete | Stay `awaiting_ocr` or fail; publication remains blocked |
| MinerU returns malformed/repeated layout or unresolved empty content | Persist diagnostics and fail/retry the page; never emit a publishable empty page |
| Strict blank detector passes | Persist the flag plus detector metrics; quality report lists `confirmed_blank_pages` |
| Page text is empty without both blank signals | Add it to `empty_pages`; `publishable=false` |
| Provider returns `finish_reason=length` | Retry within configured limits; reject persistent truncation |
| Embedding/Rerank indexes are incomplete or invalid | Raise a client error; do not continue to indexing/retrieval |
| Embedding dimension/profile differs from index metadata | Fail validation; do not mark the run `review_ready` |
| Indexed count differs from source chunk count | `index_verified=false`; publication is blocked |
| Worker loses its lease | Fence all subsequent state changes; its run can never become active |
| Online ingestion writes `chunk_embeddings` | Regression failure; remove the write path |
| API reads an existing secret | Return configured/fingerprint metadata only, never the secret |

### 5. Good / Base / Bad Cases

- Good: a scanned page is rendered, MinerU returns stripped layout plus plain table rows, the adapter preserves the rows, marks `table_structure_lost`, chunks them, and produces page-cited ES evidence.
- Base: a native-text PDF passes page quality checks and only rejected pages use OCR; the worker resumes from persisted OCR pages after retry.
- Good blank case: a physically blank page passes every strict pixel threshold, is recorded in `confirmed_blank_pages`, and does not create a chunk.
- Bad blank case: faint text is classified as blank based only on mean brightness. This loses content and must fail regression tests.
- Bad provider case: a Rerank response returns indexes `[0, 2]` for three inputs and code fills index `1` with zero. The client must reject the entire response.
- Bad lifecycle case: retrieval filters only by `document_id`, allowing an old version or abandoned run into candidates. It must filter by the full active tuple.

### 6. Tests Required

- `server/tests/test_platform_ai_configuration.py`: admin round trip, write-only secrets, OCR output budget, Embedding batch size, and effective DB-backed settings.
- `server/tests/test_textbook_mineru.py`: official/stripped layouts, fused delimiters, continuation tokens, truncated output retry, raw/empty table fallback, true blank pages at multiple DPI values, and faint-stroke rejection.
- `server/tests/test_textbook_quality.py`: only internally verified blank pages are exempt; unresolved/empty/searchable-page coverage remains blocking.
- `server/tests/test_textbook_rag.py`: sequential response compatibility and exhaustive invalid-index rejection for both Embedding and Rerank.
- `server/tests/test_textbook_ingestion_worker.py` and `test_textbook_recovery.py`: immutable snapshot propagation, lease fencing, resume behavior, and run cleanup boundaries.
- `server/tests/test_textbook_lifecycle.py` and `test_textbook_active_corpus.py`: publish preconditions, exact active run filters, corpus revision, and stale/inactive exclusion.
- `server/tests/test_textbook_ingestion_e2e.py`: upload through publish and retrieval, exact ES count, and zero new PostgreSQL `chunk_embeddings` rows.
- Frontend settings tests must assert form-to-DTO and DTO-to-form mapping for every configurable OCR/Embedding/Rerank field.

### 7. Wrong vs Correct

#### Wrong

```python
# Assumes provider order and hides a missing result.
scores = [float(row.get("score", 0.0)) for row in response["results"]]

# Treats any nearly white OCR image as disposable.
if mean_luma > 254.9:
    return blank_page()
```

#### Correct

```python
# Validate a complete index permutation, then reorder explicitly.
ordered = [None] * len(inputs)
for row in response["results"]:
    index = _validated_result_index(
        row["index"], expected_count=len(inputs), response_kind="rerank"
    )
    if ordered[index] is not None:
        raise TextbookRAGClientError("rerank response contains duplicate index")
    ordered[index] = float(row["relevance_score"])
if any(score is None for score in ordered):
    raise TextbookRAGClientError("rerank response is missing indexed results")

# Require the full detector contract and persist auditable diagnostics.
if blank_assessment.confirmed:
    flags = ["ocr_confirmed_blank_page"]
    diagnostics["blank_page_detection"] = blank_assessment.as_diagnostics()
```

The same principle applies at publication: validate live facts and the exact projection generation rather than trusting a status label or historical counter alone.
