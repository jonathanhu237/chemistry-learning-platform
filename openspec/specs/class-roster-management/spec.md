# class-roster-management Specification

## Purpose
Define class roster management for the teacher admin console, including card-first class navigation, selected-class roster operations, roster imports, student activation semantics, and per-class login settings.
## Requirements
### Requirement: Card-first class navigation

The admin console SHALL present class management as a card-first page.

#### Scenario: Teacher opens Classes and Students

- **GIVEN** a teacher or administrator is authenticated
- **WHEN** they open the Classes and Students route
- **THEN** the page SHALL display one card per class
- **AND** each class card SHALL show the class name, description, status, and student count
- **AND** class creation SHALL be represented as a dashed placeholder card in the same card grid rather than a standalone toolbar button.

#### Scenario: No classes exist

- **GIVEN** no class records are available
- **WHEN** the page loads
- **THEN** the page SHALL still show the dashed create-class placeholder card
- **AND** it SHALL avoid showing an empty table as the primary state.

#### Scenario: Teacher creates a class without technical identifiers

- **GIVEN** a teacher opens the create-class modal
- **WHEN** the teacher creates a class
- **THEN** the UI SHALL ask only for teacher-facing class information such as class name and optional description
- **AND** it SHALL NOT expose or require an internal class ID
- **AND** the backend SHALL generate any required internal class identifier.

### Requirement: Selected-class roster detail

The admin console SHALL show roster and class settings only after a class is selected.

#### Scenario: Teacher selects a class card

- **GIVEN** class cards are visible
- **WHEN** the teacher clicks a class card
- **THEN** a selected-class detail view SHALL open
- **AND** it SHALL show roster entries, class settings, login mode settings, roster import controls, and student management actions for that class
- **AND** the detail view SHALL prioritize the roster workflow before import and settings controls.

#### Scenario: Teacher sees class status

- **GIVEN** multiple classes exist
- **WHEN** the teacher reviews class cards or a selected-class detail view
- **THEN** the UI SHALL allow more than one class to be active at the same time
- **AND** it SHALL present class status as teacher-facing copy such as "使用中" or "已归档"
- **AND** it SHALL avoid implying that only one class can be enabled.

#### Scenario: Teacher closes the detail view

- **GIVEN** a selected-class detail view is open
- **WHEN** the teacher closes it
- **THEN** the page SHALL return to the card grid without losing the loaded class list.

#### Scenario: Teacher manages class context and roster

- **GIVEN** a selected-class detail view is open
- **WHEN** the teacher reviews the page
- **THEN** the top class management card SHALL remain as the selected-class context
- **AND** it SHALL summarize the class status, roster metrics, and current login rule
- **AND** the lower main area SHALL focus on the student roster table rather than settings panels.

#### Scenario: Teacher edits class settings

- **GIVEN** the selected-class detail view is open
- **WHEN** the teacher chooses to edit class settings
- **THEN** a dedicated settings modal SHALL show class basic information and class login rules together
- **AND** the class description field SHALL use a fixed-height non-resizable text area with a concise character limit
- **AND** saving the modal SHALL persist both class information and login-rule changes.

#### Scenario: Teacher imports a roster

- **GIVEN** the selected-class detail view is open
- **WHEN** the teacher chooses to import a roster
- **THEN** a dedicated import modal SHALL show append/upsert and overwrite choices
- **AND** the default selected-class page SHALL not reserve a separate full-width import section.

### Requirement: Roster import modes

The backend and admin console SHALL support both append/upsert import and one-time overwrite import for class rosters.

#### Scenario: Teacher imports roster with append mode

- **GIVEN** a class has existing roster entries
- **WHEN** the teacher imports a roster file in append/upsert mode
- **THEN** valid rows SHALL create new entries or update matching student names
- **AND** entries missing from the file SHALL remain enabled.

#### Scenario: Teacher imports roster with overwrite mode

- **GIVEN** a class has existing roster entries
- **WHEN** the teacher imports a roster file in overwrite mode
- **THEN** valid rows SHALL create or update entries
- **AND** active or pending entries missing from the file SHALL be disabled.

### Requirement: Student roster CRUD

The backend and admin console SHALL support simple student roster management for a selected class.

#### Scenario: Teacher adds a student

- **GIVEN** a selected class detail view is open
- **WHEN** the teacher creates a student with student number and name
- **THEN** the backend SHALL create a pending roster entry for that class
- **AND** the roster list SHALL refresh to show the new entry.

#### Scenario: Teacher edits a student

- **GIVEN** a roster entry exists
- **WHEN** the teacher edits the student number or name
- **THEN** the backend SHALL update the roster entry
- **AND** the change SHALL be visible in the selected-class roster list.

#### Scenario: Teacher disables a student

- **GIVEN** a roster entry exists
- **WHEN** the teacher disables the student in the current class
- **THEN** the backend SHALL disable the roster entry rather than physically deleting historical learning data.

#### Scenario: Teacher views current roster

- **GIVEN** a roster entry has been disabled
- **WHEN** the teacher opens the default roster view
- **THEN** the disabled student SHALL NOT appear in the current roster list
- **AND** the system SHALL keep the disabled student available from a separate disabled-students view.

#### Scenario: Teacher understands student activation

- **GIVEN** a student has been imported or manually added to a class roster
- **WHEN** the student has not yet completed first login and forced password change
- **THEN** the admin console SHALL show the student as not activated
- **AND** the student dialog SHALL NOT expose per-student default-password or self-registration choices.

### Requirement: Class login mode settings

The selected-class detail view SHALL expose login settings that can be controlled per class.

#### Scenario: Teacher reviews login settings

- **GIVEN** a selected class detail view is open
- **WHEN** login settings are shown
- **THEN** the system SHALL indicate that class login is controlled for the selected class roster
- **AND** it SHALL show whether an initial password is configured
- **AND** it SHALL clearly explain that these login rules affect only the selected class.

#### Scenario: Teacher updates login settings

- **GIVEN** a selected class detail view is open
- **WHEN** the teacher updates login settings
- **THEN** the backend SHALL persist the registration settings for that class
- **AND** the drawer SHALL refresh the displayed login state.

#### Scenario: Class has no custom login settings

- **GIVEN** a class has no class-level login settings
- **WHEN** login settings are loaded
- **THEN** the backend SHALL return settings inherited from the system default
- **AND** saving from the selected-class drawer SHALL create or update only that class's settings.

#### Scenario: Teacher configures initial password

- **GIVEN** a selected class detail view is open
- **WHEN** the teacher configures initial password behavior
- **THEN** the UI SHALL present friendly choices such as using the student number or setting a shared initial password
- **AND** it SHALL NOT require the teacher to edit internal password policy keys
- **AND** it SHALL keep initial-password policy at the class level rather than on individual student records.

### Requirement: Roster activation for student H5
Roster entries SHALL be the authoritative source for student H5 account activation.

#### Scenario: Pending roster student logs in
- **WHEN** a pending roster student completes first login with valid class login credentials
- **THEN** the system SHALL activate or link the corresponding student account
- **AND** the admin roster status SHALL remain compatible with existing activation displays.

#### Scenario: Duplicate active student identifiers exist
- **WHEN** migration or login detects duplicate active normalized student identifiers that would make account ownership ambiguous
- **THEN** the system SHALL fail safely instead of linking a student to the wrong roster entry.

### Requirement: Activation-aware roster password reset
The admin class roster SHALL make student activation and password-reset behavior explicit and consistent with the student H5 login flow.

#### Scenario: Teacher views pending roster student
- **WHEN** a roster student has not completed first login and forced password change
- **THEN** the admin console MUST show the student as not activated
- **AND** it MUST explain that the student will use the class initial-password rule for first login

#### Scenario: Teacher resets activated student password
- **WHEN** a teacher or admin resets an activated student's password from the selected class roster
- **THEN** the backend MUST update that student's account password
- **AND** it MUST mark the student to change password by default
- **AND** it MUST revoke active sessions for that student

#### Scenario: Teacher attempts pending-student password reset
- **WHEN** a teacher or admin attempts to reset a pending student without an activated account
- **THEN** the system MUST avoid creating a hidden per-student password policy
- **AND** it MUST guide the teacher to use the class-level initial-password setting for pending students

### Requirement: Teacher preview classes stay hidden from ordinary class workflows
System-managed teacher preview classes SHALL be excluded from ordinary teacher class and roster management while remaining available for platform administration.

#### Scenario: Teacher opens class management
- **WHEN** a teacher opens the normal Classes and Students page
- **THEN** hidden teacher-preview classes MUST NOT appear in the class card grid, selected-class list, roster import choices, or normal class counts
- **AND** the teacher MUST NOT be able to edit the preview class through ordinary class settings.

#### Scenario: Teacher preview class has a test student
- **WHEN** the backend creates or reuses a teacher-owned preview test student
- **THEN** that student MUST NOT appear in ordinary teacher roster tables, roster imports, password reset lists, or class login setting views
- **AND** normal roster workflows MUST continue to show only teacher-managed instructional classes.

#### Scenario: Class list API is requested by teacher console
- **WHEN** a teacher-console class list or roster endpoint is requested without an explicit platform-admin preview filter
- **THEN** the backend MUST exclude classes whose purpose is teacher preview
- **AND** this exclusion MUST be enforced server-side rather than relying only on frontend filtering.

#### Scenario: Hidden preview class is reset by platform operations
- **WHEN** a platform operator resets a teacher's preview class or test student through web-admin
- **THEN** the normal teacher class roster view MUST remain unaffected
- **AND** teacher-managed instructional classes and student rosters MUST NOT be mutated by that reset.
