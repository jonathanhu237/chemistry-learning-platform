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

### Requirement: Video point correctness analytics
The system SHALL aggregate student question outcomes by experiment video point when point-aware question bindings are available.

#### Scenario: Student answers a point-aware question
- **WHEN** a student submits an answer to a question with primary video point keys
- **THEN** the learning event SHALL preserve the question id, experiment id, correctness, and referenced video point keys
- **AND** class analytics SHALL be able to aggregate correctness by video point.

#### Scenario: Question has multiple point keys
- **WHEN** a question references multiple video point keys
- **THEN** analytics SHALL attribute the answer outcome to each referenced point
- **AND** it SHALL keep the original question id so drill-down can explain the shared attribution.

#### Scenario: Video point has no answered questions
- **WHEN** a formal experiment video point has no student question attempts
- **THEN** class analytics SHALL show no-data or zero-attempt status for that point
- **AND** it SHALL NOT hide the point from coverage reporting.

### Requirement: Option-level misconception analytics
The system SHALL use option-level diagnostic links to explain incorrect single-choice answers when available.

#### Scenario: Student selects a diagnostic distractor
- **WHEN** a student chooses an incorrect single-choice option with a diagnostic option link
- **THEN** analytics SHALL record the selected option label and diagnostic role
- **AND** teacher reports SHALL be able to group mistakes by misconception or adjacent point.

#### Scenario: Student selects an unrelated distractor
- **WHEN** a student chooses an incorrect option marked `unrelated_distractor` or `weak_distractor`
- **THEN** analytics SHALL preserve the selected option
- **AND** it SHALL avoid overstating a specific misconception that the option does not support.

### Requirement: Point-aware weak point reporting
The system SHALL combine question correctness, video point bindings, and existing chapter/KP context for teacher-facing weak point reports.

#### Scenario: Teacher reviews weak experiment points
- **WHEN** point-aware question attempts exist for a class
- **THEN** the backend SHALL summarize weak video points by attempt count, incorrect rate, linked experiment, and representative questions
- **AND** it SHALL allow drill-down to affected students and selected wrong options where available.

#### Scenario: Theory KP mapping is absent
- **WHEN** a point-aware question has video point links but no theory KP mapping
- **THEN** analytics SHALL still include it in experiment point reporting
- **AND** it SHALL mark theory KP attribution as unmapped rather than dropping the result.

### Requirement: Point-aware weak experiment point display
The admin analytics console SHALL display point-aware weak experiment points when point-aware question attempts are available.

#### Scenario: Teacher opens weak-point analytics
- **WHEN** point-aware attempt data exists for a class
- **THEN** the console SHALL show weak experiment video points with experiment identity, attempt count, incorrect count, and incorrect rate
- **AND** it SHALL keep legacy question/KP weak-point rows available as secondary context.

#### Scenario: Teacher reviews a weak experiment point
- **WHEN** selected wrong-option diagnostic links are available
- **THEN** the console SHALL show teacher-readable option diagnostic roles and representative question stems
- **AND** it SHALL not overstate a specific misconception for unrelated distractors.

### Requirement: Readable student learning path
The student report section in analytics SHALL present point-aware attempts and weak video points as structured UI instead of raw JSON.

#### Scenario: Teacher selects a student
- **WHEN** the selected student's report loads
- **THEN** the console SHALL show the student's weak experiment video points, recent attempts, and timeline in readable cards or tables
- **AND** it SHALL include point titles and correctness where available.

