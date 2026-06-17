## ADDED Requirements

### Requirement: Roster-backed student login
The system SHALL allow enabled roster students to log in to the student H5 app using class-controlled initial login rules.

#### Scenario: Student logs in from roster
- **WHEN** an enabled roster student submits a valid student identifier and initial credential
- **THEN** the backend SHALL create or reuse the linked student account
- **AND** it SHALL return an authenticated session with student id, class id, class name, and password-change state.

#### Scenario: Disabled roster entry attempts login
- **WHEN** a disabled roster entry attempts student H5 login
- **THEN** the backend SHALL reject the login
- **AND** it SHALL NOT activate a student account for that roster entry.

### Requirement: Forced first password change
The system SHALL require newly activated students to change their password before accessing normal student learning APIs.

#### Scenario: Newly activated student authenticates
- **WHEN** a student account is authenticated but marked as requiring password change
- **THEN** protected student learning APIs SHALL reject normal learning access
- **AND** the password-change endpoint SHALL remain available.

#### Scenario: Student changes password
- **WHEN** the authenticated student submits a valid new password
- **THEN** the backend SHALL update the password hash
- **AND** it SHALL clear the password-change requirement for future requests.

### Requirement: Student session identity
The system SHALL expose student-specific identity fields to authenticated student requests without weakening teacher/admin authentication.

#### Scenario: Student calls an authorized API
- **WHEN** an authenticated student calls a student API
- **THEN** the request context SHALL include the linked student id and current class id
- **AND** role checks SHALL restrict the route to the student role.

#### Scenario: Teacher calls a student-only API
- **WHEN** a teacher or administrator session calls a student-only API
- **THEN** the backend SHALL reject the request as unauthorized for that role.
