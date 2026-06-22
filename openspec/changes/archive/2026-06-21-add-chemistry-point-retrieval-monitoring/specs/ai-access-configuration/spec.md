## MODIFIED Requirements

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

## ADDED Requirements

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
