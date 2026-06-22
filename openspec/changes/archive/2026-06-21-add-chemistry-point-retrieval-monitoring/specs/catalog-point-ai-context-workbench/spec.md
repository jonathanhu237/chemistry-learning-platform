## MODIFIED Requirements

### Requirement: Point page exposes AI-consumable context to teachers
The teacher point workbench SHALL show how the selected catalog point placement is consumed by student search, ES indexing, RAG evidence retrieval, and AI-assisted learning features.

#### Scenario: Teacher opens point retrieval diagnostics
- **WHEN** a teacher opens diagnostics for a selected point placement
- **THEN** the workbench MUST show placement node id, canonical point id, catalog path, point title, publication state, student-visible three-element content, normalized equation rows, and indexed/search-preview fields
- **AND** it MUST label the surface as point retrieval diagnostics or equivalent product wording rather than a broad generic AI context panel.

#### Scenario: Point has ES state
- **WHEN** the selected point has ES index-state records or recent ES jobs
- **THEN** the diagnostics MUST show desired action, current sync status, last synced time, retryability, error message when present, and recent job history
- **AND** it MUST indicate whether the point is expected to be student-searchable.

#### Scenario: Point has static or dynamic RAG evidence
- **WHEN** the selected point has bound evidence, generated query plans, dynamic RAG probes, or RAG failures
- **THEN** the diagnostics MUST show static evidence bindings separately from dynamic RAG probe output
- **AND** it MUST distinguish source/evidence state from ES search state.

#### Scenario: Teacher-only notes exist
- **WHEN** a selected point contains teacher-only notes or operational diagnostics
- **THEN** the diagnostics MUST identify which content is student-visible and indexed
- **AND** it MUST keep teacher-only notes, raw job data, and retrieval internals out of student-facing APIs.

## ADDED Requirements

### Requirement: Point diagnostics expose search preview and route probes
The point workbench SHALL help teachers understand why a selected point placement can or cannot be retrieved.

#### Scenario: Teacher views search preview document
- **WHEN** the point diagnostics surface renders search preview data
- **THEN** it MUST show the placement document fields intended for ES indexing, including title, path, principle, phenomenon explanation, safety note, aliases, formulae, reaction features, equation rows, condition tags, and related searchable text when available
- **AND** it MUST show whether the preview is based on published content, draft content, or unavailable content.

#### Scenario: Teacher probes a query from the selected point
- **WHEN** a teacher runs a query probe from the point diagnostics surface
- **THEN** the result MUST indicate whether the selected point placement was recalled
- **AND** it MUST show matched routes such as title/text, strict synonym, formula, equation row, condition, phenomenon/property, directory context, or fallback search text.

#### Scenario: Point is not retrievable
- **WHEN** a selected point placement is not retrievable through ES
- **THEN** diagnostics MUST show the likely reason, such as unpublished content, queued delete, pending upsert, failed job, disabled backend, unavailable ES, hidden placement, missing dictionary asset, or analyzer mismatch
- **AND** it SHOULD offer the authorized retry or refresh action when the state is retryable.
