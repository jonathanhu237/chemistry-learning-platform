## ADDED Requirements

### Requirement: Teacher analytics include assessment report history
Teacher-facing student learning analytics SHALL include durable assessment report history for accessible students.

#### Scenario: Teacher opens an individual student report
- **WHEN** a teacher opens an individual student report for a class they can access
- **THEN** the backend SHALL include the student's durable assessment reports or provide a linked endpoint to list them
- **AND** the console SHALL distinguish pretest, smart assessment, custom assessment, and point assessment reports.

#### Scenario: Teacher opens a report from student analytics
- **WHEN** a teacher selects an assessment report from a student's report history
- **THEN** the console SHALL render the persisted report snapshot
- **AND** it SHALL not require recomputing report text or regenerating LLM output.

### Requirement: Teacher report display is structured-first
The teacher console SHALL present assessment reports as structured learning records before generated prose.

#### Scenario: Teacher scans a report list
- **WHEN** the teacher views report history
- **THEN** each report list item SHALL expose report type, completion time, score or correctness, and wrong-answer count
- **AND** it SHALL avoid showing long generated text in the list.

#### Scenario: Teacher reviews report detail
- **WHEN** the teacher opens report detail
- **THEN** score, correctness, involved experiments or points, mastery changes where available, and wrong answers SHALL be visible before generated summary or explanation text
- **AND** generated summary and wrong-answer explanation SHALL be available but folded or secondary by default.
