# catalog-point-ai-context-workbench Specification

## Purpose
TBD - created by archiving change catalog-point-ai-platform-roadmap. Update Purpose after archive.
## Requirements
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

### Requirement: Static evidence bindings are inspectable
The workbench SHALL display stored catalog-node evidence bindings when available.

#### Scenario: Static evidence exists
- **WHEN** catalog-node evidence bindings exist for a point
- **THEN** the workbench MUST show selected chunk ids, source titles, pages or sections, evidence role, review/selection status, and freshness state
- **AND** it MUST make clear that these chunks are fallback or supplemental evidence for AI, not student body copy.

#### Scenario: Static evidence is stale
- **WHEN** point context has changed since the latest evidence binding
- **THEN** the workbench MUST mark the binding as stale
- **AND** it MUST offer or link to a refresh action if the teacher has access to trigger it.

### Requirement: Dynamic RAG probe is supported
The workbench SHALL let teachers inspect dynamic RAG behavior for the selected point.

#### Scenario: Teacher runs RAG probe
- **WHEN** a teacher starts a dynamic RAG probe for a point
- **THEN** the backend MUST generate retrieval queries from the current catalog-node context
- **AND** the result MUST show generated queries, recall source, candidate count, final evidence, rerank scores when available, and runtime health.

#### Scenario: RAG probe fails
- **WHEN** dynamic RAG cannot run because query generation, vector recall, or BGE rerank is unavailable
- **THEN** the workbench MUST show the failed stage and teacher-readable reason
- **AND** it MUST NOT present ungrounded model output as if evidence was found.

### Requirement: Query strategy is visible and auditable
The system SHALL make the point-to-RAG query strategy inspectable to teachers or operators.

#### Scenario: Queries are generated
- **WHEN** RAG query generation runs for a point
- **THEN** diagnostics MUST show which point context fields contributed to the generated query variants
- **AND** they MUST include title, full path, normalized equations, phenomenon explanation, safety note, videos, and related context when those fields are present.

#### Scenario: Query generation uses fallback
- **WHEN** the AI provider cannot generate query variants
- **THEN** the system MUST fall back to deterministic query text from point context
- **AND** the workbench MUST record the fallback reason.

### Requirement: AI context workbench is teacher-only
Raw AI diagnostics SHALL be visible only in teacher/operator surfaces.

#### Scenario: Student opens point detail
- **WHEN** a student views a point page
- **THEN** the student API MUST NOT expose raw chunk ids, rerank scores, generated query variants, job payloads, or teacher-only diagnostics
- **AND** student pages MUST only show curated point learning content and allowed source summaries.

#### Scenario: Teacher exports or inspects diagnostics
- **WHEN** a teacher inspects AI context diagnostics
- **THEN** the system MUST label diagnostics as authoring/debug context
- **AND** it MUST not imply that raw evidence bindings are automatically published to students.

### Requirement: AI context aligns with learning assistant consumption
The point AI context workbench SHALL reflect the same context contracts used by the learning assistant and future question generation.

#### Scenario: Learning assistant consumes a point
- **WHEN** a student or teacher asks an AI question in point context
- **THEN** the assistant context MUST include structured catalog point context and available static evidence before supplemental dynamic RAG evidence
- **AND** diagnostics MUST distinguish fixed/static point evidence from supplemental RAG evidence.

#### Scenario: New point has no binding yet
- **WHEN** a newly created point is used with AI before static evidence refresh completes
- **THEN** the assistant MAY use dynamic RAG and structured point context if runtime policy allows
- **AND** diagnostics MUST clearly indicate that static evidence binding was absent.

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

