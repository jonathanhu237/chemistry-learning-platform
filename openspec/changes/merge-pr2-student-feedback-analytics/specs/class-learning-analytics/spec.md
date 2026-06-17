## ADDED Requirements

### Requirement: Experiment mastery analytics
Class analytics SHALL expose experiment-level mastery state for teacher review.

#### Scenario: Teacher opens class experiment mastery dashboard
- **WHEN** a teacher opens class analytics for a class with student experiment mastery evidence
- **THEN** the dashboard response MUST include per-student experiment mastery state, score, evidence count, and attempt count where available
- **AND** experiments without evidence MUST remain visible with a no-evidence or default score state rather than being hidden.

#### Scenario: Teacher reviews student report
- **WHEN** a teacher opens an individual student analytics report
- **THEN** the report MUST include experiment mastery entries where available
- **AND** it MUST preserve existing attempts, weak points, weak video points, and timeline context.

### Requirement: Experiment family grouped analytics
The admin analytics console SHALL group related formal experiments by experiment family or parent experiment for class-level scanning.

#### Scenario: Class matrix uses experiment groups
- **WHEN** a class has multiple published experiments belonging to the same parent experiment or family
- **THEN** the class matrix MUST be able to show grouped experiment-family columns
- **AND** each group MUST preserve access to underlying experiment evidence and lowest-score detail.

#### Scenario: Experiment has no family metadata
- **WHEN** a published experiment has no explicit family metadata
- **THEN** analytics MUST place it in a stable fallback group
- **AND** the teacher-facing label MUST remain readable.

### Requirement: Feedback attachments appear in admin feedback workflow
The admin feedback workflow SHALL expose feedback attachment counts and attachment metadata for feedback records created by students.

#### Scenario: Admin views feedback list
- **WHEN** a feedback record has one or more attachments
- **THEN** the admin feedback list or detail view MUST show the attachment count
- **AND** attachment presence MUST not hide status, handler, feedback type, or student/class snapshot fields.

#### Scenario: Admin opens feedback detail
- **WHEN** an admin opens a feedback record with attachments
- **THEN** the detail response MUST include attachment metadata sufficient for display or download authorization
- **AND** the system MUST enforce existing feedback visibility rules before returning attachment metadata or files.
