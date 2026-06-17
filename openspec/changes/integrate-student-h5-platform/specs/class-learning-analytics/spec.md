## ADDED Requirements

### Requirement: Student H5 assessment records feed analytics
Student H5 pretest, posttest, and learning activity records SHALL preserve enough student, class, experiment, question, correctness, and point context for analytics.

#### Scenario: Student completes an H5 assessment
- **WHEN** a student submits a pretest or posttest through the H5 app
- **THEN** the stored record SHALL be associated with the student and class
- **AND** question-level correctness SHALL remain available for later analytics.

#### Scenario: Student reviews learning content
- **WHEN** student H5 activity is recorded for an experiment
- **THEN** the activity SHALL remain attributable to the experiment and the student's current class context.
