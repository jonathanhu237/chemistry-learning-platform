## ADDED Requirements

### Requirement: Catalog point jobs are controlled and observable
The system SHALL expose controlled job records for point indexing and point evidence work.

#### Scenario: Job is created
- **WHEN** the backend creates a point indexing or evidence job
- **THEN** the job MUST record catalog node id, job type, trigger source, status, attempts, timestamps, payload, result, and latest error
- **AND** job identity MUST be idempotent for repeated equivalent requests where duplicate work would be unsafe.

#### Scenario: Teacher views job state
- **WHEN** a teacher opens a point workbench or diagnostics surface
- **THEN** the backend MUST expose current ES index state and RAG evidence state for that point
- **AND** it MUST distinguish pending, running, succeeded, failed, stale, disabled, and unavailable states.

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
- **WHEN** point title, catalog path, normalized equations, phenomenon explanation, safety note, videos, or related context changes
- **THEN** the system MUST mark catalog-node evidence as stale or enqueue a refresh according to configured trigger policy
- **AND** teacher save/publish actions MUST not wait for high-precision BGE rerank completion.

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
