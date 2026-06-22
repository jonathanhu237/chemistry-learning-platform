## MODIFIED Requirements

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

## ADDED Requirements

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
