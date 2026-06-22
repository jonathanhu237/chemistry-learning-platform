## ADDED Requirements

### Requirement: Web-admin governs teacher preview infrastructure
The operational admin console SHALL manage hidden preview classes and preview test students as platform infrastructure, separate from teacher workflows.

#### Scenario: Operator lists preview infrastructure
- **WHEN** an authenticated platform operator opens the web-admin preview infrastructure page
- **THEN** the page MUST list teacher-owned hidden preview classes and preview test students with owner teacher, status, created time, and last session metadata where available
- **AND** it MUST NOT expose teacher catalog editing, teacher class instruction workflows, or student learning pages.

#### Scenario: Operator resets a teacher preview student
- **WHEN** the operator resets a teacher's preview test student
- **THEN** the backend MUST invalidate or replace only the preview student's preview-owned state
- **AND** it MUST NOT mutate real instructional classes, real students, teacher-authored catalog content, or normal analytics records.

#### Scenario: Teacher opens web-admin
- **WHEN** a teacher-console user attempts to access web-admin preview infrastructure routes without the configured web-admin authorization
- **THEN** the frontend and backend MUST reject access
- **AND** the teacher MUST use the web-teacher preview shell instead.

#### Scenario: Student opens teacher preview infrastructure
- **WHEN** a student session attempts to access preview infrastructure routes
- **THEN** the backend MUST reject the request
- **AND** no preview class or teacher ownership metadata MUST be leaked.
