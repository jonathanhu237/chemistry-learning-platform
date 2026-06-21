## ADDED Requirements

### Requirement: Web consoles have explicit product boundaries
The system SHALL maintain separate web consoles for operations, teachers, and students.

#### Scenario: Operator opens web-admin
- **WHEN** an operator opens `web-admin`
- **THEN** the application MUST present only operational administration workflows
- **AND** teacher learning, catalog, question-bank, class, analytics, and AI workbench workflows MUST NOT be duplicated there.

#### Scenario: Teacher opens web-teacher
- **WHEN** a teacher account opens `web-teacher`
- **THEN** the application MUST expose the teacher console workflows including catalog management, classes, video resources, question bank, learning analytics, feedback, settings, and AI access/test surfaces
- **AND** teacher workflows MUST share the same product visual language as the rest of the platform.

#### Scenario: Student opens web-student
- **WHEN** a student opens `web-student`
- **THEN** the application MUST expose only student learning workflows
- **AND** it MUST NOT expose teacher diagnostics, raw RAG traces, teacher notes, or account-operation controls.

### Requirement: Teacher accounts have universal teacher-console access
All teacher accounts SHALL have access to all teacher-console features.

#### Scenario: Teacher navigation is built
- **WHEN** any authenticated teacher views the teacher console navigation
- **THEN** the navigation MUST include all teacher workflows
- **AND** it MUST NOT hide learning assistant, AI access, catalog, question-bank, or settings pages behind per-teacher feature permissions.

#### Scenario: Teacher calls teacher API
- **WHEN** an authenticated teacher calls a teacher-console API
- **THEN** the backend MUST authorize the request as a teacher-console request
- **AND** it MUST NOT reject the request because the teacher lacks a finer-grained admin role.

### Requirement: Web-admin manages teacher accounts
The operational admin console SHALL manage teacher accounts independently from teacher workflows.

#### Scenario: Operator creates teacher account
- **WHEN** an operator creates a teacher account in `web-admin`
- **THEN** the system MUST create credentials and teacher identity needed for `web-teacher`
- **AND** the new teacher MUST receive universal teacher-console access after authentication.

#### Scenario: Operator edits teacher account
- **WHEN** an operator resets password, disables, enables, renames, or deletes a teacher account
- **THEN** the operation MUST affect authentication and account lifecycle
- **AND** it MUST NOT mutate teacher-authored catalog, class, video, question, or AI content except through explicit ownership rules.

### Requirement: Learning assistant teacher entry is restored and visible
The teacher console SHALL expose learning-assistant and AI-related teacher/debug surfaces to every teacher account.

#### Scenario: Teacher views AI navigation
- **WHEN** any teacher opens `web-teacher`
- **THEN** learning assistant or AI access/test entries required for teacher operations MUST be visible
- **AND** they MUST use teacher-console routes rather than old `admin-only` route assumptions.

#### Scenario: Removed route is recovered
- **WHEN** a historical learning-assistant teacher page was removed or hidden by permission refactor
- **THEN** implementation MUST restore it through current feature-owned modules and typed API clients
- **AND** it MUST follow the current `web-teacher` shell rather than reintroducing deleted `admin-web` code wholesale.

### Requirement: Console deployment remains explicit
The three web consoles SHALL have independent app directories, build targets, and local ports.

#### Scenario: Compose stack starts web consoles
- **WHEN** the local Docker Compose stack starts frontend services
- **THEN** `web-student`, `web-teacher`, and `web-admin` MUST build from their own app directories
- **AND** each service MUST be reachable on its configured local port without route collision.
