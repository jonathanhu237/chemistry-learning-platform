## ADDED Requirements

### Requirement: Legacy competition profile uses canonical teacher and student products
The legacy competition profile SHALL be implemented by canonical `web-teacher` and `web-student` products that share the backend and core data.

#### Scenario: Legacy profile is inspected
- **WHEN** a maintainer inspects the implemented legacy profile
- **THEN** it MUST expose a teacher product identified as `web-teacher`
- **AND** it MUST expose a student product identified as `web-student`
- **AND** both products MUST use the same backend API and database
- **AND** the profile MUST NOT require `web-teacher-old`, `web-student-old`, `web-backoffice`, `web-admin`, a legacy database, a legacy seed corpus, or a backend fork.

### Requirement: Legacy teacher profile has global teacher access
The legacy teacher product SHALL treat teacher access as global teaching administration for the old competition profile.

#### Scenario: Teacher opens legacy teacher product
- **WHEN** an authenticated teacher opens `web-teacher`
- **THEN** the teacher MUST be able to access legacy experiment management, AI question generation, teacher review, question bank, classes, analytics, and reports supported by this profile
- **AND** access MUST NOT be scoped by teacher ownership or class assignment.

#### Scenario: Recommended learning points are managed
- **WHEN** a teacher opens the legacy teacher product
- **THEN** they MUST be able to mark or unmark published experiment point nodes as `推荐学习`
- **AND** this action MUST be available as global teaching administration rather than teacher-owned content.

## REMOVED Requirements

### Requirement: Legacy competition profile is a separate product profile
**Reason**: The legacy profile is no longer a separate optional `*-old` profile beside current products on the legacy branch.
**Migration**: Use canonical `web-teacher` and `web-student`.

### Requirement: Legacy runtime validation uses an old-only compose boundary
**Reason**: The default Compose runtime is already the legacy runtime; no separate old-only compose entrypoint is needed.
**Migration**: Validate the default `web-teacher`, `web-student`, `backend`, and `postgres` runtime.

### Requirement: Legacy student navigation exposes four first-level modules
**Reason**: The requirement names `web-student-old`; the canonical student product is now `web-student`.
**Migration**: Preserve the same four-module old student navigation under `web-student`.

### Requirement: Legacy student enhancement preserves shared data boundaries
**Reason**: The old wording allows "teacher or admin"; canonical teacher access is now `teacher` only.
**Migration**: Preserve shared data boundaries while using `teacher` as the only teaching-management identity.
