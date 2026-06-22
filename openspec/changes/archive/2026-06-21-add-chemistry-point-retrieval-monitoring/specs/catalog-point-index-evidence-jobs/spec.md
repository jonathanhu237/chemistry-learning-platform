## ADDED Requirements

### Requirement: ES sync fans out by point placement
Catalog point ES synchronization SHALL enqueue and process work for each active point placement affected by canonical point content, placement state, directory context, media bindings, or related-point changes.

#### Scenario: Canonical point content changes
- **WHEN** student-searchable content changes for a canonical point
- **THEN** ES sync jobs MUST be queued for all active placements of that canonical point
- **AND** each job MUST build or delete the placement document according to publication and visibility state.

#### Scenario: Directory path changes
- **WHEN** a directory title, parent, order, chapter, or visibility state changes in a way that affects descendant catalog paths
- **THEN** ES sync jobs MUST be queued for affected descendant point placements
- **AND** the rebuilt documents MUST reflect the new catalog path and directory-derived recall context.

#### Scenario: Media binding or related-point title changes
- **WHEN** bound videos or related point titles change for a point placement
- **THEN** ES sync jobs MUST be queued for affected point placement documents
- **AND** the resulting search document MUST reflect current student-visible video and related-text metadata.

### Requirement: Save and publish preserve student-search safety
Catalog point indexing SHALL respect draft, publish, unpublish, archive, and visibility semantics through job-backed eventual consistency.

#### Scenario: Teacher saves draft content
- **WHEN** a teacher saves draft point content or edits student-searchable content before publication
- **THEN** the system MUST queue deletion or hiding of affected active placement documents from student ES search
- **AND** monitoring MUST show that the placement is not expected to be student-searchable until publication queues an upsert.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes valid point content
- **THEN** the system MUST queue upsert jobs for affected active point placements
- **AND** the index-state table MUST show pending, running, synced, failed, disabled, or unavailable state per placement.

#### Scenario: Teacher unpublishes or archives content
- **WHEN** a point is unpublished, archived, hidden, or otherwise made unavailable to students
- **THEN** the system MUST queue delete jobs for affected placement documents
- **AND** student search MUST converge to no longer returning those placements.

### Requirement: Global ES diagnostics summarize job and index state
The system SHALL provide teacher/admin diagnostics that summarize ES configuration, cluster/index health, dictionary asset state, document counts, published-content counts, and job/index-state counts.

#### Scenario: Admin opens ES diagnostics
- **WHEN** an admin requests index diagnostics
- **THEN** the response MUST include effective backend, target index, analyzer configuration, local fallback state, ES health when available, indexed document count when available, and mapping/analyzer version metadata when available
- **AND** it MUST include sync-status counts from the point index-state tables.

#### Scenario: Published count and indexed count differ
- **WHEN** published point placement counts differ from indexed ES document counts
- **THEN** diagnostics MUST show enough state to distinguish pending jobs, failed jobs, disabled backend, unavailable ES, hidden/unpublished records, and known stale index state
- **AND** it SHOULD expose controlled retry or rebuild actions to authorized teachers/operators.

#### Scenario: Direct database changes bypass domain services
- **WHEN** point content or catalog placement data changes outside the domain service and outbox path
- **THEN** the system MUST NOT assume ES is current
- **AND** diagnostics MUST direct operators to a controlled rebuild or resync workflow.

### Requirement: RAG evidence jobs remain separate but co-monitored
RAG evidence refresh and ES indexing SHALL remain separate job concerns while the monitoring surface presents their status together.

#### Scenario: ES is synced but RAG evidence is stale
- **WHEN** ES index state is synced and RAG evidence state is stale, failed, or unavailable
- **THEN** monitoring MUST show the two states separately
- **AND** it MUST NOT imply that successful ES indexing guarantees RAG evidence freshness.

#### Scenario: RAG refresh succeeds but ES sync fails
- **WHEN** RAG evidence refresh succeeds and ES sync fails for the same point placement
- **THEN** monitoring MUST show the successful RAG state and failed ES state independently
- **AND** retry actions MUST target the correct job type.
