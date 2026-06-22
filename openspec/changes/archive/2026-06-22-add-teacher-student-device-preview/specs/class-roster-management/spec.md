## ADDED Requirements

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
