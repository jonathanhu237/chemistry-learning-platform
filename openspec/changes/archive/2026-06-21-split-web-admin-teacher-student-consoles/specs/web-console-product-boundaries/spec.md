## ADDED Requirements

### Requirement: Three web consoles have explicit product boundaries
The platform SHALL expose three independent web consoles named `web-admin`, `web-teacher`, and `web-student`.

#### Scenario: Services use canonical names and ports
- **WHEN** the default local or production-like service topology is inspected
- **THEN** the student frontend service MUST be named `web-student` and expose port `5173`
- **AND** the teacher frontend service MUST be named `web-teacher` and expose port `5174`
- **AND** the platform operations frontend service MUST be named `web-admin` and expose port `5175`.

#### Scenario: Product ownership is unambiguous
- **WHEN** a maintainer inspects frontend packages, Compose services, or documentation
- **THEN** `web-teacher` MUST identify the teacher console that owns experiment, question-bank, AI, settings, class, resource, analytics, feedback, and learning-assistant workflows
- **AND** `web-admin` MUST identify the platform operations console for teacher-account management only
- **AND** `web-student` MUST identify the student H5 frontend.

### Requirement: Console access boundaries are separated
The backend and frontend guards SHALL enforce access boundaries for the three web consoles.

#### Scenario: Configured token opens web-admin
- **WHEN** an operator opens `web-admin` with the configured access token
- **THEN** the console MUST allow access to the platform teacher-account workbench.

#### Scenario: Missing or invalid token opens web-admin
- **WHEN** an operator opens `web-admin` without the configured access token
- **THEN** the console MUST reject access
- **AND** protected `/api/web-admin/*` endpoints MUST return an authorization failure.

#### Scenario: Teacher-console user opens web-teacher
- **WHEN** an active authenticated user with `role='admin'` or legacy `role='teacher'` opens `web-teacher`
- **THEN** the console MUST allow access to all teacher-console workflows.

#### Scenario: Platform or student user opens web-teacher
- **WHEN** an authenticated user with `role='platform_admin'` or `role='student'` opens `web-teacher`
- **THEN** the teacher console MUST reject the session.

### Requirement: Teacher-console role compatibility does not affect feature visibility
The teacher console SHALL treat active `admin` and legacy `teacher` users as full teacher-console users.

#### Scenario: Legacy teacher opens teacher console
- **WHEN** an active legacy `role='teacher'` user is authenticated in `web-teacher`
- **THEN** learning assistant, AI access, settings, experiment catalog, question bank, classes, analytics, resources, media, and feedback navigation MUST be available according to the same route list as `role='admin'`.

#### Scenario: New teacher-console account is created
- **WHEN** a web-admin token request creates a teacher-console account
- **THEN** the backend MUST store it in `app_users` with `role='admin'`
- **AND** it MUST NOT create new `role='teacher'` rows.
