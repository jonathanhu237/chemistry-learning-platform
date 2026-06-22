# catalog-point-index-evidence-jobs Specification

## Purpose
TBD - created by archiving change catalog-point-ai-platform-roadmap. Update Purpose after archive.
## Requirements
### Requirement: Catalog point jobs are controlled and observable
The system SHALL expose controlled job records for point indexing and point evidence work, and SHALL surface their state as downstream consumption diagnostics in node status.

#### Scenario: Job is created
- **WHEN** the backend creates a point indexing or evidence job
- **THEN** the job MUST record catalog node id, job type, trigger source, status, attempts, timestamps, payload, result, and latest error
- **AND** job identity MUST be idempotent for repeated equivalent requests where duplicate work would be unsafe.

#### Scenario: Teacher views job state
- **WHEN** a teacher opens a point workbench or diagnostics surface
- **THEN** the backend MUST expose current ES index state and RAG evidence state for that point
- **AND** it MUST distinguish pending, running, succeeded, failed, stale, disabled, and unavailable states.

#### Scenario: Node status consumes job state
- **WHEN** a point status summary includes ES index state or RAG evidence state
- **THEN** the job state MUST be placed under async-consumption or sync-diagnostics status
- **AND** it MUST NOT be merged into core point content or binary video readiness.

#### Scenario: Sync work is not complete yet
- **WHEN** ES or RAG work is pending, running, or stale for a point
- **THEN** the point MUST remain editable and publishable according to its core readiness and visibility rules
- **AND** the job state MUST remain observable in diagnostics without replacing the point's primary content/video status.

### Requirement: ES sync is a first-class point job
The system SHALL manage student search document updates through controlled ES sync actions.

#### Scenario: Point becomes searchable
- **WHEN** a point is published or its student-searchable content changes
- **THEN** the system MUST enqueue or update an ES upsert job keyed by catalog node id
- **AND** the search document MUST be rebuilt from backend-owned point content and normalized chemistry fields.

#### Scenario: Point becomes unsearchable
- **WHEN** a point is unpublished, archived, deleted, or moved under an unpublished path
- **THEN** the system MUST enqueue or update an ES delete or disable job
- **AND** stale student search results MUST not remain accepted as synced state.

#### Scenario: Teacher manually refreshes ES
- **WHEN** a teacher triggers a manual ES refresh for a point or subtree
- **THEN** the backend MUST enqueue the corresponding ES jobs
- **AND** the UI MUST show progress and final result without requiring a page reload.

### Requirement: RAG evidence refresh is asynchronous
The system SHALL refresh catalog-node evidence bindings through asynchronous jobs rather than blocking teacher saves.

#### Scenario: Point context changes
- **WHEN** point title, catalog path, normalized equations, phenomenon explanation, safety note, video readiness, or related point context changes
- **THEN** the system MUST mark catalog-node evidence as stale or enqueue a refresh according to configured trigger policy
- **AND** teacher save/publish actions MUST not wait for high-precision BGE rerank completion.
- **AND** evidence refresh queries MUST NOT use teacher-only video resource titles, media file names, or media asset metadata as point semantics.

#### Scenario: Evidence refresh runs
- **WHEN** a RAG evidence refresh job runs
- **THEN** it MUST generate retrieval queries from catalog node context
- **AND** it MUST use the configured RAG/BGE pipeline to select candidate source chunks
- **AND** output bindings MUST target catalog node id or stable catalog seed key, not legacy `(experiment_id, point_key)`.

#### Scenario: BGE service is unavailable
- **WHEN** the BGE service is disabled, unreachable, or too slow during evidence refresh
- **THEN** the job MUST fail or defer with a diagnostic reason
- **AND** the point MUST remain editable and dynamically RAG-consumable when runtime RAG later becomes healthy.

### Requirement: Automatic and manual triggers are both supported
The system SHALL support automatic triggers for routine freshness and manual triggers for teacher/operator control.

#### Scenario: Automatic trigger policy runs
- **WHEN** point content is published, renamed, moved, or materially edited
- **THEN** the backend MUST apply configured automatic trigger policy for ES sync and RAG evidence freshness
- **AND** the policy MUST be visible or documented so teachers understand why a point is pending or stale.

#### Scenario: Manual trigger is requested
- **WHEN** a teacher or operator manually requests ES sync, RAG evidence refresh, retry, or delete
- **THEN** the backend MUST create an auditable job with trigger source `manual`
- **AND** the resulting status MUST be visible in the teacher workbench or operational diagnostics.

### Requirement: First implementation uses Postgres-backed jobs
The first implementation SHALL prefer a Postgres-backed outbox/job model unless scale requirements demand an external broker.

#### Scenario: Worker claims jobs
- **WHEN** a backend or worker process claims pending jobs
- **THEN** it MUST use database locking or equivalent safeguards to avoid duplicate concurrent execution
- **AND** failed jobs MUST remain retryable with attempts and error details.

#### Scenario: External broker is absent
- **WHEN** Redis, RabbitMQ, Celery, or RQ is not deployed
- **THEN** ES and RAG job orchestration MUST still work in the supported local stack
- **AND** future broker adoption MUST not change the public job API contract.

### Requirement: ES and RAG states remain secondary node-status signals
The system SHALL treat ES search indexing and AI/RAG evidence refresh as asynchronous consumption states rather than as core point readiness states.

#### Scenario: Core point is incomplete
- **WHEN** a point is missing required learning content or has no experiment video
- **THEN** ES and RAG job states MUST NOT become the primary reason shown in the default tree row
- **AND** the async states MUST remain visible in sync diagnostics.

#### Scenario: Published point has downstream failure
- **WHEN** a point is core-complete and student-visible but ES or RAG state is failed or unavailable
- **THEN** the node status MUST escalate the point to a sync-attention state
- **AND** the status detail MUST say the problem belongs to search or AI consumption rather than to point content authoring.

#### Scenario: Manual retry is available
- **WHEN** a teacher or operator can retry ES sync or RAG evidence refresh
- **THEN** the retry action MUST appear in the sync diagnostics surface
- **AND** it MUST NOT appear as a required step inside the default point content form.

#### Scenario: Student-facing consumption is delayed
- **WHEN** a newly published or edited point has not yet been consumed by ES or RAG jobs
- **THEN** the system MUST communicate that search or AI context may lag behind the saved content
- **AND** it MUST NOT claim that the point lacks its experiment video or learning content because downstream jobs are still processing.

### Requirement: ES sync fans out by point placement
Catalog point ES synchronization SHALL enqueue and process work for each active point placement affected by canonical point content, placement state, directory context, video readiness, or related-point changes.

#### Scenario: Canonical point content changes
- **WHEN** student-searchable content changes for a canonical point
- **THEN** ES sync jobs MUST be queued for all active placements of that canonical point
- **AND** each job MUST build or delete the placement document according to publication and visibility state.

#### Scenario: Directory path changes
- **WHEN** a directory title, parent, order, chapter, or visibility state changes in a way that affects descendant catalog paths
- **THEN** ES sync jobs MUST be queued for affected descendant point placements
- **AND** the rebuilt documents MUST reflect the new catalog path and directory-derived recall context.

#### Scenario: Video readiness or related-point title changes
- **WHEN** video readiness, active binding presence, or related point titles change for a point placement
- **THEN** ES sync jobs MUST be queued for affected point placement documents
- **AND** the resulting search document MUST reflect current point readiness and related-text metadata without indexing video resource titles or video file metadata.

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

### Requirement: Media asset archive queues affected point jobs
Catalog point indexing SHALL respond to media asset archive events through controlled point jobs.

#### Scenario: Archived asset removes active bindings
- **WHEN** a media asset archive event archives active catalog point video bindings
- **THEN** ES sync jobs MUST be queued or updated for every affected active point placement
- **AND** each job MUST rebuild or delete the document according to the point's current publication and visibility state.

#### Scenario: Archived asset changes video readiness
- **WHEN** a published point loses its only active ready video because a media asset was archived
- **THEN** the point readiness model MUST show missing video
- **AND** ES/RAG diagnostics MUST treat the change as downstream consumption work rather than upload processing work.

#### Scenario: Archive event is retried
- **WHEN** a media asset archive event is retried after partial failure
- **THEN** point jobs MUST remain idempotent for equivalent placement/action payloads
- **AND** retry MUST NOT create duplicate active bindings or duplicate live ES documents.

### Requirement: ES rebuild can be destructive
Catalog point ES synchronization SHALL support destructive rebuild when index semantics or mapping purity changes.

#### Scenario: ES purity migration is applied
- **WHEN** the implementation removes video resource semantic fields from the ES mapping and document builders
- **THEN** operators MUST be able to delete and recreate the student video-library ES index
- **AND** rebuilt documents MUST come from PostgreSQL point facts rather than old ES sources.

#### Scenario: Rebuild fails for some documents
- **WHEN** a destructive ES rebuild cannot index all eligible point placement documents
- **THEN** failed rows MUST be recorded in index-state diagnostics
- **AND** stale video-resource semantic fields MUST NOT be accepted as a synced state.
