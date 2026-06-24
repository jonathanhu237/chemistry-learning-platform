## ADDED Requirements

### Requirement: Student assessment submissions hand off to durable reports
Student H5 assessment submission flows SHALL create and hand off to durable report detail for pretest, custom assessment, smart assessment, and point assessment completions.

#### Scenario: Pretest submission completes
- **WHEN** a student submits the final pretest answers and grading succeeds
- **THEN** the backend SHALL create a durable `pretest` report snapshot
- **AND** the student app SHALL be able to navigate to that report without exposing pretest internal staging as report structure.

#### Scenario: Smart assessment submission completes
- **WHEN** a student submits a smart assessment and grading succeeds
- **THEN** the backend SHALL create a durable `smart` report snapshot
- **AND** the student app SHALL navigate to durable report detail rather than relying on browser session storage.

#### Scenario: Custom assessment submission completes
- **WHEN** a student submits a custom assessment and grading succeeds
- **THEN** the backend SHALL create a durable `custom` report snapshot
- **AND** the report SHALL preserve the selected experiment range and wrong-answer details.

#### Scenario: Point assessment submission completes
- **WHEN** a student submits a point assessment started after learning a point
- **THEN** the backend SHALL create a durable `point` report snapshot
- **AND** the report SHALL preserve the assessed point context.

### Requirement: Assessment report text is generated at submission time
Covered student H5 assessment submissions SHALL generate report summary and wrong-answer explanation text during submission and persist the result for future views.

#### Scenario: Generated text is available immediately
- **WHEN** a covered assessment submission returns successfully
- **THEN** the returned or subsequently loaded report SHALL include persisted summary and wrong-answer explanation text
- **AND** future report views SHALL reuse persisted text instead of generating a new answer.

#### Scenario: No wrong answers exist
- **WHEN** a covered assessment has no wrong answers
- **THEN** the persisted wrong-answer explanation SHALL state that there are no wrong answers to review
- **AND** the report SHALL still be valid and visible in report history.
