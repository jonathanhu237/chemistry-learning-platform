## MODIFIED Requirements

### Requirement: React Ant Design admin shell

The teacher console SHALL be implemented as a React + TypeScript + Ant Design desktop web application named `web-teacher`.

#### Scenario: Authenticated teacher-console user opens web-teacher

- **GIVEN** an active teacher-console user with `role='admin'` or compatible legacy `role='teacher'` is authenticated
- **WHEN** they open the teacher console
- **THEN** the system SHALL render a React application shell with Ant Design `Layout`, top account controls, route-based content, and a left navigation menu
- **AND** the shell SHALL load route data through typed API clients rather than direct DOM mutation.

#### Scenario: Unauthenticated user opens teacher console

- **GIVEN** a user is not authenticated or their session has expired
- **WHEN** they open a teacher-console route
- **THEN** the system SHALL redirect them to the teacher-console login screen
- **AND** successful login SHALL return them to the intended teacher-console route when possible.

#### Scenario: Non-teacher-console role opens teacher console

- **GIVEN** a student or platform-admin user is authenticated
- **WHEN** they open a teacher-console route
- **THEN** the system SHALL reject the session for the teacher console.

### Requirement: Teacher workflow navigation

The teacher console SHALL expose navigation organized around teacher operations for the experiment-centered product direction without feature-tier branching between teacher-console roles.

#### Scenario: Teacher views navigation
- **GIVEN** a teacher-console user is logged in
- **WHEN** the teacher menu is displayed
- **THEN** the menu SHALL include dashboards for overview, classes and students, experiment management, question bank management, learning analytics, learning assistant, AI access, learning resources, feedback, and system settings
- **AND** the Classes and Students route SHALL use card-first class navigation rather than a table-first class list
- **AND** the Experiment Management route SHALL include video resource management inside experiment detail
- **AND** it SHALL NOT present course version management or video resources as primary teacher workflows.

#### Scenario: Teacher opens deprecated review workflow
- **GIVEN** a teacher previously used the generic question review workflow
- **WHEN** they look for question administration
- **THEN** the console SHALL route them to experiment question bank management
- **AND** it SHALL NOT expose generic "question review" as the main workflow.

#### Scenario: Legacy teacher views navigation
- **GIVEN** a legacy `role='teacher'` user is logged in
- **WHEN** the teacher menu is displayed
- **THEN** the navigation SHALL match the complete navigation available to `role='admin'`
- **AND** it SHALL NOT hide learning assistant or other teacher-console modules because of role.

### Requirement: Admin learning assistant test page
The teacher console SHALL provide a "learning assistant" page for all teacher-console accounts to test the student learning assistant guardrails.

#### Scenario: Teacher-console user opens learning assistant page
- **WHEN** an authenticated teacher-console user opens `/learning-assistant`
- **THEN** the page SHALL show a learning assistant test form with question input, optional student/chapter/experiment/knowledge-point context, RAG toggle, progress lookup toggle, and sample prompts
- **AND** it SHALL describe the test as a simulation of student learning-page chat.

#### Scenario: Legacy teacher operator views navigation
- **WHEN** an authenticated legacy teacher operator views the teacher-console navigation
- **THEN** the learning assistant test page SHALL be shown as a teacher workflow.

#### Scenario: Teacher-console user submits a test prompt
- **WHEN** a teacher-console user submits a learning assistant test prompt
- **THEN** the page SHALL call the admin learning assistant test API
- **AND** the API SHALL execute the request as student chat rather than as teacher AI.

#### Scenario: Guardrail result is returned
- **WHEN** the test API returns an assistant response
- **THEN** the page SHALL show the answer, mode, policy tag, guardrail decisions, source references, tool calls, and raw classification diagnostics.

#### Scenario: Student AI configuration is disabled
- **WHEN** the student AI assistant or student RAG feature switch affects the test request
- **THEN** the page SHALL show the current AI configuration status
- **AND** submission results SHALL reflect the same feature-switch behavior used by student chat.
