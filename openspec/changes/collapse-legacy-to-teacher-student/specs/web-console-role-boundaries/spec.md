## ADDED Requirements

### Requirement: Legacy web products have two role boundaries
The legacy branch SHALL enforce two web role boundaries: `teacher` for `web-teacher` and `student` for `web-student`.

#### Scenario: Teacher opens web-teacher
- **WHEN** an active authenticated user with `role='teacher'` opens `web-teacher`
- **THEN** the teacher product MUST allow access.

#### Scenario: Student opens web-teacher
- **WHEN** an authenticated user with `role='student'` opens `web-teacher`
- **THEN** the teacher product MUST reject access.

#### Scenario: Student opens web-student
- **WHEN** an active authenticated user with `role='student'` opens `web-student`
- **THEN** the student product MUST allow access.

#### Scenario: Teacher opens web-student
- **WHEN** an authenticated user with `role='teacher'` opens student-only authenticated flows
- **THEN** the student product or backend MUST reject access to student-only data.

### Requirement: Teacher accounts have universal legacy teacher access
All active `teacher` accounts SHALL have access to all legacy teacher product features.

#### Scenario: Teacher navigation is built
- **WHEN** any authenticated teacher views the teacher product navigation
- **THEN** the navigation MUST include the supported legacy teacher workflows
- **AND** it MUST NOT hide workflows behind per-teacher feature permissions, `admin` compatibility checks, or platform operations tokens.

#### Scenario: Teacher calls teacher API
- **WHEN** an authenticated teacher calls `/api/teacher/*`
- **THEN** the backend MUST authorize the request as a teacher-product request
- **AND** it MUST NOT require `admin`, `platform_admin`, `WEB_ADMIN_ACCESS_TOKEN`, or class-ownership scope.

## REMOVED Requirements

### Requirement: Web consoles have explicit product boundaries
**Reason**: The three-console model with `web-admin` no longer applies to the legacy branch.
**Migration**: Use the two-product `web-teacher` and `web-student` model.

### Requirement: Teacher accounts have universal teacher-console access
**Reason**: The requirement is replaced by universal access for canonical `teacher` accounts only.
**Migration**: Convert `admin` and compatible legacy teacher-console users to `teacher`.

### Requirement: Web-admin manages teacher accounts
**Reason**: The standalone token-protected account-management console is removed from the legacy branch.
**Migration**: Create or update teacher accounts through bootstrap/scripts for this version.

### Requirement: Learning assistant teacher entry is restored and visible
**Reason**: This belongs to the removed current teacher-console product line, not the focused legacy teacher product.
**Migration**: Keep only teacher workflows used by the legacy teacher product.

### Requirement: Console deployment remains explicit
**Reason**: The deployment model no longer includes three web consoles.
**Migration**: Validate only `web-teacher` and `web-student` frontend services for the legacy branch.

### Requirement: Web-admin governs teacher preview infrastructure
**Reason**: `web-admin` and its token-authorized preview governance workflows are removed from the legacy branch.
**Migration**: Remove `/api/web-admin/*` preview governance routes and do not expose preview infrastructure governance in this version.
