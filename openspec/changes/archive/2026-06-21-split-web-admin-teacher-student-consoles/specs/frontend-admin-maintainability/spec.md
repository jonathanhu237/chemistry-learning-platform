## ADDED Requirements

### Requirement: Frontend apps keep product-specific ownership
The repository SHALL keep `web-admin`, `web-teacher`, and `web-student` frontend source, package metadata, and build scripts product-specific.

#### Scenario: Teacher app owns teacher workflows
- **WHEN** a developer edits experiment catalog, question bank, learning assistant, AI access, settings, classes, resources, media, analytics, or feedback workflows
- **THEN** the code MUST live under the `web-teacher` app
- **AND** it MUST NOT import or depend on `web-admin` account-management modules.

#### Scenario: Platform app owns account management
- **WHEN** a developer edits teacher-account list, create, status update, display-name update, password reset, or disable/delete behavior
- **THEN** the code MUST live under the `web-admin` app
- **AND** it MUST NOT import teacher experiment, question-bank, AI, settings, media, analytics, learning-assistant, or student-H5 feature modules.

#### Scenario: Student app remains independent
- **WHEN** a developer edits student learning, assessment, assistant, feedback, auth, or catalog behavior
- **THEN** the code MUST live under the `web-student` app or its shared student modules
- **AND** service/package naming MUST NOT refer to the app as `student-web`.

### Requirement: Teacher shell avoids role-based feature forks
The teacher frontend SHALL avoid product-obsolete feature visibility branches based on `admin` versus legacy `teacher` roles.

#### Scenario: Route registry is evaluated
- **WHEN** the teacher route registry and navigation model are loaded
- **THEN** learning assistant, AI access, settings, experiment catalog, question bank, resources, classes, analytics, feedback, and media routes MUST be available to teacher-console users
- **AND** route visibility MUST NOT depend on an `adminOnly` flag for those modules.

#### Scenario: Teacher auth guard evaluates role
- **WHEN** an active `admin` or legacy `teacher` account opens `/learning-assistant`
- **THEN** the guard MUST allow the route
- **AND** it MUST NOT redirect the user away because the role is `teacher`.
