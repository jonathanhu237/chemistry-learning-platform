# ai-access-configuration Specification

## Purpose
TBD - created by archiving change upgrade-learning-assistant-debug-rag. Update Purpose after archive.
## Requirements
### Requirement: AI access page naming and scope
The admin console SHALL present OpenAI-compatible provider credentials as an AI access concern rather than a broad mixed AI configuration page.

#### Scenario: Admin views navigation
- **WHEN** an authenticated admin views the left navigation
- **THEN** the AI provider entry SHALL be labeled as AI access using Chinese product wording such as `AI接入`
- **AND** it SHALL avoid implying that all AI feature behavior is configured on that page.

#### Scenario: Admin opens AI access page
- **WHEN** an admin opens the AI access route
- **THEN** the page SHALL focus the primary form on provider, model name, base URL, API key, connection testing, and save behavior for the OpenAI-compatible API.

### Requirement: AI feature controls are separated from provider credentials
The system SHALL visually separate feature switches and RAG runtime controls from OpenAI-compatible provider credentials.

#### Scenario: Admin reviews feature switches
- **WHEN** an admin reviews student assistant, RAG, analytics, or question-bank AI switches
- **THEN** those controls SHALL live in the system settings surface rather than the AI access credential page
- **AND** they SHALL be grouped under feature/range wording distinct from the provider credential form.

#### Scenario: Admin reviews RAG runtime state
- **WHEN** the AI access page shows hybrid RAG settings or service status
- **THEN** the UI SHALL present the section as read-only RAG status
- **AND** it SHALL make clear whether the optional BGE service is enabled, reachable, or unnecessary because RAG is disabled.

### Requirement: Backend setting updates follow local Docker rebuild discipline
The project SHALL document that backend source changes require rebuilding the backend Docker image in the local Compose environment.

#### Scenario: Backend AI or RAG code changes locally
- **WHEN** a developer changes backend AI, RAG, or admin API source code under the Docker Compose environment
- **THEN** they SHALL rebuild and recreate the backend service with `docker compose up -d --build backend`
- **AND** they SHALL verify the changed route or setting against the running backend instead of relying only on Vite or browser refresh.

