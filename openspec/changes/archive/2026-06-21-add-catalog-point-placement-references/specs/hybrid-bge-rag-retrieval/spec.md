## MODIFIED Requirements

### Requirement: Teacher workbench retrieval contract
The system SHALL expose hybrid RAG health and retrieval diagnostics for teacher-side question-bank AI workbench requests using canonical experiment point identity and placement context.

#### Scenario: Workbench checks RAG runtime
- **WHEN** the question-bank page renders AI workbench actions
- **THEN** it SHALL use the same runtime health contract as the learning assistant to decide whether RAG-backed AI actions are available
- **AND** it SHALL distinguish RAG disabled, BGE unavailable, query generation disabled, and healthy hybrid rerank states.

#### Scenario: Workbench builds an evidence package from a placement
- **WHEN** a teacher starts or continues an AI workbench session from a catalog placement under a healthy RAG runtime
- **THEN** the backend SHALL resolve the placement to its canonical experiment point before building point-specific evidence context
- **AND** the evidence package SHALL preserve the source placement id and breadcrumbs as context metadata.

#### Scenario: Workbench builds an evidence package from a canonical point
- **WHEN** a teacher starts or continues an AI workbench session from a canonical experiment point or existing question
- **THEN** the backend SHALL build an evidence package for the selected canonical point context, original question when present, and teacher prompt
- **AND** the package SHALL include source references and retrieval diagnostics when available.

#### Scenario: Workbench records reranked evidence
- **WHEN** hybrid BGE reranking succeeds for a workbench request
- **THEN** the evidence package SHALL preserve final evidence order, chunk identifiers, source metadata, canonical point id, source placement context where available, and rerank score where available
- **AND** the workbench SHALL show that the candidate was grounded in reranked RAG chunks.

#### Scenario: Workbench RAG fails closed
- **WHEN** hybrid RAG cannot provide healthy reranked evidence for a workbench request
- **THEN** the system SHALL block AI candidate generation rather than silently falling back to ungrounded local generation
- **AND** it SHALL return a diagnostic reason that the UI can display.

## ADDED Requirements

### Requirement: Catalog point evidence binds to canonical experiment points
The system SHALL bind catalog-point evidence state and selected chunk evidence to canonical experiment points rather than placement ids.

#### Scenario: Evidence refresh is requested from a placement
- **WHEN** a teacher or background job requests evidence refresh for a point placement
- **THEN** the backend MUST resolve the placement to its canonical experiment point
- **AND** it MUST create or update evidence state and selected chunk bindings for that canonical point.

#### Scenario: Canonical point has multiple placements
- **WHEN** a canonical experiment point has multiple active placements
- **THEN** one successful evidence refresh MUST satisfy shared evidence state for all placements targeting that canonical point
- **AND** the system MUST NOT duplicate evidence bindings merely because the experiment appears in multiple catalog paths.

#### Scenario: Placement path context affects retrieval query
- **WHEN** placement breadcrumbs provide useful chapter or category context for evidence refresh
- **THEN** the backend MUST include that source placement context as retrieval context metadata
- **AND** it MUST still store accepted evidence bindings against the canonical experiment point.

#### Scenario: Canonical point is archived
- **WHEN** a canonical experiment point is archived
- **THEN** the system MUST disable or archive its catalog-point evidence state
- **AND** it MUST preserve canonical RAG chunks and chunk embeddings because they are corpus resources, not point-owned placement resources.
