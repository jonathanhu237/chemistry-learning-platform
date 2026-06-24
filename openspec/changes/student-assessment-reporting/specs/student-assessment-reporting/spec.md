## ADDED Requirements

### Requirement: Durable assessment report snapshots
The system SHALL create a durable assessment report snapshot for every completed student `pretest`, `custom`, `smart`, and `point` assessment.

#### Scenario: Report is created on assessment completion
- **WHEN** a student successfully submits a covered assessment
- **THEN** the backend SHALL persist one report record associated with the student, class, report type, and source assessment session
- **AND** the report SHALL include score, correct count, total count, correctness rate, involved experiments or points, mastery changes where available, wrong answers, generated summary text, generated wrong-answer explanation text, and completion timestamp.

#### Scenario: Report content is fixed after submission
- **WHEN** a stored report is viewed after prompts, catalog titles, question content, or explanations have changed
- **THEN** the report SHALL render from the persisted snapshot
- **AND** it SHALL NOT silently change historical report content.

#### Scenario: LLM generation fails during submission
- **WHEN** grading succeeds but report LLM generation fails or is unavailable
- **THEN** the assessment submission SHALL still complete successfully
- **AND** the persisted report SHALL contain deterministic fallback summary and wrong-answer explanation content with generation metadata indicating fallback status.

### Requirement: Report generation prompts
The system SHALL support configurable report-generation prompts with defaults, fixed template variables, and class-level overrides.

#### Scenario: Global defaults are used
- **WHEN** a class has no report prompt override
- **THEN** report generation SHALL use the global report summary prompt and global wrong-answer explanation prompt
- **AND** both prompts SHALL have system-provided defaults that can be restored.

#### Scenario: Class override is used
- **WHEN** a class has report prompt overrides
- **THEN** reports for students in that class SHALL use the class-level summary and wrong-answer explanation prompts
- **AND** the report snapshot SHALL preserve enough prompt metadata to identify the prompt source used for generation.

#### Scenario: Prompt variables are constrained
- **WHEN** a teacher edits report prompts
- **THEN** the system SHALL expose only a fixed set of supported variables for report context
- **AND** it SHALL reject or safely ignore unsupported template variables rather than allowing arbitrary database field access.

### Requirement: Student report history and detail
The student H5 app SHALL expose assessment report history and detail through durable report APIs.

#### Scenario: Student opens report history
- **WHEN** an authenticated student opens the report history entry from `我的`
- **THEN** the app SHALL show all of that student's persisted assessment reports ordered by completion time
- **AND** each list item SHALL identify report type, score or correctness, completion time, and a concise title.

#### Scenario: Student opens report detail
- **WHEN** a student selects a report from history or completes an assessment
- **THEN** the app SHALL load report detail from persisted backend data
- **AND** it SHALL show structured score, correctness, involved experiments or points, mastery changes where available, wrong answers, report summary, and wrong-answer explanation.

#### Scenario: Student refreshes report detail
- **WHEN** a student refreshes a report detail route or opens it on another device
- **THEN** the app SHALL still load the report from the backend
- **AND** it SHALL NOT require browser session storage to render the report.

### Requirement: Teacher report visibility
The teacher console SHALL allow authorized teachers to view the same assessment report snapshots for students in classes they can access.

#### Scenario: Teacher opens student report history
- **WHEN** a teacher opens a student report view for an accessible class and student
- **THEN** the console SHALL show that student's persisted assessment reports
- **AND** it SHALL preserve existing class/student access controls.

#### Scenario: Teacher opens assessment report detail
- **WHEN** a teacher selects an assessment report
- **THEN** the console SHALL show the same persisted report snapshot available to the student
- **AND** it SHALL prioritize structured score, correctness, experiments or points, wrong answers, and mastery data over generated text.

#### Scenario: Teacher views generated text
- **WHEN** the report contains generated summary or wrong-answer explanation text
- **THEN** the teacher console SHALL make the text available in a secondary or folded section by default
- **AND** it SHALL NOT require a new LLM call to view historical report text.
