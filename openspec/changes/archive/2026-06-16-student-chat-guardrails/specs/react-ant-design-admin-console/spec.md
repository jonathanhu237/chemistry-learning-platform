## ADDED Requirements

### Requirement: Admin learning assistant test page
The admin console SHALL provide an admin-only "学习助手" page for testing the student learning assistant guardrails.

#### Scenario: Admin opens learning assistant page
- **WHEN** an authenticated admin opens `/admin/learning-assistant`
- **THEN** the page SHALL show a learning assistant test form with question input, optional student/chapter/experiment/knowledge-point context, RAG toggle, progress lookup toggle, and sample prompts
- **AND** it SHALL describe the test as a simulation of student learning-page chat.

#### Scenario: Teacher operator views navigation
- **WHEN** an authenticated teacher operator views the admin console navigation
- **THEN** the "学习助手" test page SHALL NOT be shown as a teacher workflow.

#### Scenario: Admin submits a test prompt
- **WHEN** an admin submits a learning assistant test prompt
- **THEN** the page SHALL call the admin learning assistant test API
- **AND** the API SHALL execute the request as student chat rather than as teacher AI.

#### Scenario: Guardrail result is returned
- **WHEN** the test API returns an assistant response
- **THEN** the page SHALL show the answer, mode, policy tag, guardrail decisions, source references, tool calls, and raw classification diagnostics.

#### Scenario: Student AI configuration is disabled
- **WHEN** the student AI assistant or student RAG feature switch affects the test request
- **THEN** the page SHALL show the current AI configuration status
- **AND** submission results SHALL reflect the same feature-switch behavior used by student chat.
