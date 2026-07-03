## ADDED Requirements

### Requirement: Legacy branch has two canonical identities
The legacy branch SHALL use exactly two canonical application identities: `teacher` and `student`.

#### Scenario: Role constraint is inspected
- **WHEN** the active database schema for the legacy branch is inspected after migrations
- **THEN** `app_users.role` MUST allow `teacher` and `student`
- **AND** it MUST NOT allow `admin` or `platform_admin`.

#### Scenario: Existing role data is migrated
- **WHEN** the role-collapse migration is applied to a database containing `admin` or `platform_admin` users
- **THEN** those users MUST be converted to `teacher`
- **AND** active student users MUST remain `student`.

### Requirement: Teacher identity is global in this legacy version
The legacy branch SHALL treat `teacher` as a global teaching-administrator identity with full teacher-product access.

#### Scenario: Teacher opens teacher product
- **WHEN** an active authenticated user with `role='teacher'` opens `web-teacher`
- **THEN** the app MUST allow access to the teacher product
- **AND** all teacher workflows in this legacy version MUST be available without per-teacher feature permissions.

#### Scenario: Teacher data access is evaluated
- **WHEN** a teacher requests classes, roster entries, analytics, reports, catalog content, question-bank content, or legacy recommendation settings
- **THEN** the backend MUST authorize the request as global teacher access
- **AND** it MUST NOT filter data by teacher ownership, teacher-class assignment, or tenant scope in this version.

#### Scenario: Multi-teacher isolation is requested
- **WHEN** a future requirement needs each teacher to see only their own classes or students
- **THEN** it MUST be implemented as a separate change
- **AND** it MUST NOT be inferred from the `teacher` identity in this legacy version.

### Requirement: Student identity is self-scoped
The legacy branch SHALL treat `student` as the learner identity that can access only student-facing workflows and the authenticated student's own data.

#### Scenario: Student opens student product
- **WHEN** an active authenticated user with `role='student'` opens `web-student`
- **THEN** the app MUST allow access to student learning, video, assessment, and report workflows
- **AND** it MUST NOT expose teacher product navigation or management workflows.

#### Scenario: Student attempts teacher access
- **WHEN** an authenticated student attempts to call `/api/teacher/*` or open `web-teacher`
- **THEN** the backend or frontend guard MUST reject the request.

### Requirement: Obsolete platform and admin identities are not public contracts
The legacy branch SHALL remove `admin` and `platform_admin` from public auth, frontend, API, seed, and documentation contracts.

#### Scenario: Public contracts are searched
- **WHEN** maintainers inspect README, Compose files, environment examples, frontend code, route inventory, and active OpenSpec requirements for canonical identity names
- **THEN** they MUST find `teacher` and `student`
- **AND** they MUST NOT find `admin` or `platform_admin` documented as supported legacy identities.

#### Scenario: Token operations access is attempted
- **WHEN** a request attempts to use the retired `WEB_ADMIN_ACCESS_TOKEN` or `/api/web-admin/*` surface
- **THEN** the legacy runtime MUST NOT register that token operations contract as a supported route.
