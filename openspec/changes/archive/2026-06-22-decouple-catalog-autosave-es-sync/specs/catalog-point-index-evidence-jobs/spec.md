## MODIFIED Requirements

### Requirement: Save and publish preserve student-search safety
Catalog point indexing SHALL respect autosave, draft, published, unpublish, archive, and visibility semantics through job-backed eventual consistency.

#### Scenario: Teacher saves unpublished draft content
- **WHEN** a teacher saves point content for a point that has not been published or is not currently student-visible
- **THEN** the system MUST persist the content without creating a student-searchable upsert solely because content exists
- **AND** monitoring MUST show that the placement is not expected to be student-searchable until an explicit publish action makes it visible.

#### Scenario: Teacher edits already published content
- **WHEN** a teacher saves student-searchable content for a point whose content and placement are already published
- **THEN** the system MUST keep the point/content publication state published
- **AND** it MUST mark affected active placement documents stale or pending for ES upsert rather than queueing ES delete solely because a save occurred.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher explicitly publishes valid point content that was previously not student-visible
- **THEN** the system MUST queue upsert jobs for affected active point placements
- **AND** the index-state table MUST show pending, running, synced, failed, disabled, or unavailable state per placement.

#### Scenario: Teacher unpublishes or archives content
- **WHEN** a point is unpublished, archived, hidden, or otherwise made unavailable to students
- **THEN** the system MUST queue delete jobs for affected placement documents immediately
- **AND** student search MUST converge to no longer returning those placements.

## ADDED Requirements

### Requirement: ES sync coalesces soft edits
Catalog point ES synchronization SHALL coalesce routine content and context edits before executing ES writes.

#### Scenario: Soft edit affects a search document
- **WHEN** a routine autosave or direct persisted edit changes student-searchable point title, catalog path, principle, reaction equations, phenomenon explanation, safety note, related point text, or video readiness
- **THEN** the backend MUST mark affected placement index state stale or pending
- **AND** it MUST insert or update an idempotent `es_upsert` job for each affected active placement rather than creating duplicate jobs for equivalent open work.

#### Scenario: Quiet window is applied
- **WHEN** a soft-edit ES upsert job is created or updated
- **THEN** the job MUST normally be scheduled no earlier than 30 seconds after the most recent soft edit for that placement/action
- **AND** new soft edits inside that quiet window MUST merge into the same open job and push the run time forward.

#### Scenario: Continuous edits continue for a long time
- **WHEN** soft edits continue repeatedly without a 30 second quiet period
- **THEN** the system MUST still allow the current document state to be synchronized at least once within 3 minutes of the first unsynced soft edit
- **AND** later edits after that sync MAY start a new coalescing window.

#### Scenario: Hard visibility change occurs
- **WHEN** a point is unpublished, archived, deleted, hidden by path visibility, manually refreshed, manually deleted from ES, retried, or included in a destructive rebuild
- **THEN** the backend MUST enqueue the required ES work immediately with `run_after` at or near the current time
- **AND** the hard-change job MUST not wait for the autosave quiet window.

### Requirement: ES sync uses backend document hashes
Catalog point ES synchronization SHALL avoid unnecessary writes by comparing backend-owned student-search document hashes.

#### Scenario: Searchable projection does not change
- **WHEN** a save changes only teacher-only notes, UI metadata, whitespace that normalizes away, AI temporary state, or other data excluded from the student-search document
- **THEN** the backend MUST NOT require an ES write for that save
- **AND** existing synced index state MUST remain valid unless another indexed field changed.

#### Scenario: ES job executes after multiple edits
- **WHEN** a coalesced ES upsert job is claimed by a worker
- **THEN** the worker MUST rebuild the current student-search document from backend-owned catalog, point-content, chemistry, related-link, and video-readiness data
- **AND** it MUST not rely on stale text copied into the original job payload.

#### Scenario: Rebuilt document hash matches indexed hash
- **WHEN** the worker recomputes the current document hash and it matches the last indexed hash for that placement
- **THEN** the worker MUST mark the index state synced without writing the document again to ES
- **AND** diagnostics MUST be able to show that the job completed as a no-op.

#### Scenario: Rebuilt document hash differs
- **WHEN** the worker recomputes the current document hash and it differs from the last indexed hash for that placement
- **THEN** the worker MUST write the current document to ES
- **AND** it MUST update document hash, analyzer version where available, indexed timestamp, attempts, and latest error state according to the result.

### Requirement: RAG evidence freshness remains separate from ES sync
Catalog point evidence refresh SHALL remain independently observable and configurable even when ES sync is delayed or coalesced.

#### Scenario: Point context changes through autosave
- **WHEN** autosaved content or context changes affect RAG evidence inputs
- **THEN** the backend MUST mark evidence stale or schedule refresh according to the configured trigger policy
- **AND** the teacher save response MUST not wait for BGE retrieval, reranking, or evidence refresh completion.

#### Scenario: ES sync succeeds while evidence is stale
- **WHEN** a point's ES state becomes synced but RAG evidence remains stale, pending, failed, disabled, or unavailable
- **THEN** diagnostics MUST show those states independently
- **AND** the system MUST NOT imply that ES success guarantees RAG evidence freshness.
