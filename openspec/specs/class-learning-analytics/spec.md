# class-learning-analytics Specification

## Purpose
Define class and student learning analytics over chapter and experiment activity, question correctness, weak knowledge points, and teacher report exports.
## Requirements
### Requirement: Experiment-centered learning progress

The system SHALL track student learning progress by class, student, chapter, and experiment unit.

#### Scenario: Student completes experiment learning activity

- **GIVEN** a student watches a video, opens experiment material, answers practice questions, or completes a test
- **WHEN** the activity is recorded
- **THEN** the backend SHALL associate the event with the student, class, experiment unit, and related chapter when available
- **AND** the event SHALL be available for teacher analytics.

#### Scenario: Experiment has no student activity

- **GIVEN** an experiment unit is published
- **WHEN** no student in a class has completed related learning activity
- **THEN** the class dashboard SHALL display zero completion rather than hiding the experiment.

### Requirement: Class dashboard

The admin console SHALL provide a class-level dashboard for teachers to understand learning status.

#### Scenario: Teacher opens class analytics

- **GIVEN** a teacher selects a class
- **WHEN** the class analytics page loads
- **THEN** the console SHALL show class size, active students, experiment completion, average question score, missing students, and recent activity
- **AND** it SHALL allow filtering by experiment and time range.

#### Scenario: Teacher reviews experiment matrix

- **GIVEN** a class has multiple students and experiments
- **WHEN** the teacher opens the experiment completion matrix
- **THEN** each row SHALL represent a student
- **AND** each published experiment unit SHALL appear as a column with status, completion, score, or no-data markers.

### Requirement: Individual learning path

The system SHALL provide an individual student learning path for teacher review.

#### Scenario: Teacher opens a student report

- **GIVEN** a teacher selects a student
- **WHEN** the report loads
- **THEN** it SHALL show the student's class, published experiments, completion states, attempts, scores, weak points, and chronological learning timeline
- **AND** it SHALL distinguish completed, in-progress, not-started, and needs-attention experiments.

#### Scenario: Student changes class

- **GIVEN** a student is moved to another class
- **WHEN** their learning report is opened
- **THEN** historical activity SHALL remain associated with the student
- **AND** class-level aggregations SHALL use the student's current class membership unless a historical report explicitly requests the previous class.

### Requirement: Question correctness and weak KP analysis

The system SHALL summarize question correctness and weak theory knowledge points from experiment attempts.

#### Scenario: Teacher reviews weak points

- **GIVEN** students have answered experiment questions
- **WHEN** the teacher opens weak point analytics
- **THEN** the backend SHALL aggregate incorrect rates by experiment, question, chapter, and related KC/KP reference
- **AND** the console SHALL display prioritized weak points with drill-down to affected students and questions.

#### Scenario: Question has no KC/KP reference

- **GIVEN** a question is tied to an experiment but not mapped to a KC/KP node
- **WHEN** weak point analytics are generated
- **THEN** the system SHALL still include the question in experiment-level correctness
- **AND** it SHALL mark theory KP analysis as unmapped rather than dropping the result.

### Requirement: Teacher report export

The system SHALL allow teachers to export class and student learning reports.

#### Scenario: Teacher exports a class report

- **GIVEN** a teacher has selected a class, experiment filters, and time range
- **WHEN** they request export
- **THEN** the system SHALL generate a report containing the same core metrics shown in the dashboard
- **AND** it SHALL include enough identifiers for offline teaching follow-up: class, student number, student name, experiment code, completion, score, and weak point summary.
