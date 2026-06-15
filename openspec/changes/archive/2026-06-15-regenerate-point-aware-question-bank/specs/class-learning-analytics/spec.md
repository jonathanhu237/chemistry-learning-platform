## ADDED Requirements

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
