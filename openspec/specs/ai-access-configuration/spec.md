# ai-access-configuration Specification

## Purpose
TBD - created by archiving change upgrade-learning-assistant-debug-rag. Update Purpose after archive.
## Requirements
### Requirement: AI access page naming and scope
The admin console SHALL present the former AI access entry as an intelligent monitoring concern for AI, RAG, Elasticsearch, and chemistry retrieval, while keeping provider credentials and feature switches separated according to their existing ownership boundaries.

#### Scenario: Admin views navigation
- **WHEN** an authenticated admin views the left navigation
- **THEN** the AI/RAG/ES monitoring entry SHALL be labeled with Chinese product wording such as `智能监控` or `AI/RAG/ES 监控`
- **AND** it SHALL avoid implying that provider credentials, RAG feature switches, ES dictionary assets, and catalog authoring behavior are all edited on the same page.

#### Scenario: Admin opens monitoring page
- **WHEN** an admin opens the intelligent monitoring route
- **THEN** the page SHALL prioritize runtime status, health checks, dictionary asset state, index state, and retrieval diagnostics for the OpenAI-compatible provider, RAG/BGE, Elasticsearch, and chemistry search
- **AND** provider, model name, base URL, API key, connection testing, and save behavior SHALL remain visually separated as credential or settings concerns when they are reachable from this page.

#### Scenario: Admin adjusts runtime behavior
- **WHEN** an admin needs to change AI feature switches, RAG settings, ES analyzer assets, or chemistry dictionaries
- **THEN** the monitoring page SHALL either deep-link to the authoritative settings/import workflow or present a role-appropriate controlled action
- **AND** it SHALL NOT silently mutate feature behavior through diagnostic probes.

### Requirement: AI feature controls are separated from provider credentials
The system SHALL visually separate feature switches, provider credentials, and runtime monitoring.

#### Scenario: Admin reviews feature switches
- **WHEN** an admin reviews student assistant, RAG, analytics, or question-bank AI switches
- **THEN** those controls SHALL live in the system settings surface rather than the monitoring page
- **AND** they SHALL be grouped under feature/range wording distinct from provider credential forms and read-only monitoring modules.

#### Scenario: Admin reviews RAG runtime state
- **WHEN** the monitoring page shows hybrid RAG settings or service status
- **THEN** the UI SHALL present the section as read-only RAG runtime status
- **AND** it SHALL make clear whether the optional BGE service is enabled, reachable, degraded, or unnecessary because RAG is disabled.

### Requirement: Backend setting updates follow local Docker rebuild discipline
The project SHALL document that backend source changes require rebuilding the backend Docker image in the local Compose environment.

#### Scenario: Backend AI or RAG code changes locally
- **WHEN** a developer changes backend AI, RAG, or admin API source code under the Docker Compose environment
- **THEN** they SHALL rebuild and recreate the backend service with `docker compose up -d --build backend`
- **AND** they SHALL verify the changed route or setting against the running backend instead of relying only on Vite or browser refresh.

### Requirement: H5 feature switch propagation
The system SHALL propagate admin-managed learning feature switches to the student H5 app through a pull-based configuration endpoint and enforce them again at protected action endpoints.

#### Scenario: Admin disables student AI entry
- **WHEN** an admin disables the AI learning assistant entry in system settings
- **THEN** subsequent student app-config responses MUST mark the H5 assistant entry as disabled
- **AND** the authenticated student app shell MUST hide or disable the `问答` bottom-nav entry and move any active assistant route back to a safe tab
- **AND** student assistant request endpoints MUST reject stale requests without invoking the agent.

#### Scenario: Admin disables feedback entry
- **WHEN** an admin disables the feedback entry in system settings
- **THEN** subsequent student app-config responses MUST mark the H5 feedback entry as disabled
- **AND** the `我的` tab MUST hide or disable the feedback section
- **AND** student feedback submission endpoints MUST reject stale requests.

#### Scenario: Admin disables student AI capability
- **WHEN** an admin disables student AI capability in AI feature controls
- **THEN** subsequent student app-config responses MUST mark student AI capability as disabled
- **AND** the H5 assistant tab MUST not be available even if the general learning assistant entry remains enabled.

### Requirement: Intelligent monitoring sections are independently available
The intelligent monitoring page SHALL render AI, RAG, ES, dictionary, and retrieval-diagnostic sections independently so one unavailable subsystem does not hide the others.

#### Scenario: ES is unavailable but AI provider is healthy
- **WHEN** the ES diagnostics API reports an unavailable cluster or backend
- **THEN** the page MUST still show AI provider and RAG status when those data are available
- **AND** the ES section MUST show effective backend, index name, local fallback state, and the teacher-readable failure reason.

#### Scenario: Dictionary assets are stale or missing
- **WHEN** dictionary diagnostics report missing files, changed hashes, stale analyzer assets, or a mismatch between application dictionaries and ES/IK assets
- **THEN** the page MUST show the affected dictionary category and asset state
- **AND** it MUST indicate whether the issue affects query normalization, IK tokenization, synonym expansion, formula recall, or feature recall.

#### Scenario: Retrieval diagnostic is run from monitoring
- **WHEN** an admin submits a diagnostic query from the monitoring page
- **THEN** the page MUST show normalized query terms, strict chemical synonym expansion, non-synonym feature terms, recall-route counts, and ranked point-placement results
- **AND** it MUST label the diagnostic output as teacher/operator-only data.

