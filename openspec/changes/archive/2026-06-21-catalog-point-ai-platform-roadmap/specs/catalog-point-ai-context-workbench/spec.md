## ADDED Requirements

### Requirement: Point page exposes AI-consumable context to teachers
The teacher point workbench SHALL show how the selected catalog point will be consumed by AI.

#### Scenario: Teacher opens AI context tab
- **WHEN** a teacher opens the AI context view for a point
- **THEN** the page MUST show the point title, full catalog path, node id, normalized point content, normalized equations, related point context, video context, and current publication state
- **AND** it MUST distinguish student-facing content from teacher-only teaching note and AI diagnostics.

#### Scenario: Point has no static evidence binding
- **WHEN** a point has no stored catalog-node evidence binding
- **THEN** the workbench MUST show that static fallback evidence is missing
- **AND** it MUST still explain that dynamic RAG can consume the point when RAG runtime is healthy.

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
