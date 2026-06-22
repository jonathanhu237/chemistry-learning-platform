## MODIFIED Requirements

### Requirement: AI access page naming and scope
The admin console SHALL present provider credentials as a settings concern and present the teacher AI/RAG/ES route as an intelligent monitoring concern rather than a broad mixed configuration page.

#### Scenario: Admin views navigation
- **WHEN** an authenticated admin or teacher-console user views the left navigation
- **THEN** the AI/RAG/ES operational entry SHALL be labeled with monitoring-oriented Chinese product wording such as `智能监控`
- **AND** it SHALL avoid implying that provider credentials, feature switches, dictionary editing, and all AI behavior are configured on that page.

#### Scenario: Admin opens intelligent monitoring page
- **WHEN** an admin or teacher-console user opens the AI/RAG/ES monitoring route
- **THEN** the page SHALL focus on read-only provider health, RAG health, ES health, dictionary/outbox state, retrieval diagnostics, guardrail state, and usage trends
- **AND** provider, model name, base URL, API key, connection-test mutation, and save behavior SHALL remain owned by the existing settings or credential-management surface.

#### Scenario: Admin needs to change provider credentials
- **WHEN** monitoring indicates that provider credentials are missing, stale, or failing
- **THEN** the monitoring page MAY link to the provider settings surface
- **AND** it SHALL not render inline credential-editing forms inside the monitoring modules.

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
