## ADDED Requirements

### Requirement: Point-aware question bank demo
The system SHALL support a small, non-published demo workflow for reviewing point-aware question bank data before full bank regeneration.

#### Scenario: Demo scope is selected
- **WHEN** the demo is run
- **THEN** it SHALL be limited to `EXP_19_1_01`
- **AND** it SHALL NOT mutate published student-facing question bank data.

#### Scenario: Existing draft questions are sampled
- **WHEN** existing draft questions are used in the demo
- **THEN** they SHALL be treated only as candidate material
- **AND** each sampled question SHALL be reviewed one by one against canonical source evidence.

#### Scenario: Point-aware demo artifact is produced
- **WHEN** the demo review completes
- **THEN** it SHALL produce assessment point, reviewed question, and review report artifacts
- **AND** the artifacts SHALL show question-level video point key bindings, option-level video point key bindings where applicable, source audit decisions, and quality outcomes.

#### Scenario: Demo question is unsuitable
- **WHEN** a candidate question is too simple or poorly grounded
- **THEN** the review artifact SHALL mark it as rewrite or reject
- **AND** every rewrite SHALL include a concrete proposed rewritten question.

#### Scenario: Demo fill blank stays objective
- **WHEN** a proposed replacement uses `fill_blank`
- **THEN** it SHALL be answerable with a short phone-friendly accepted answer
- **AND** it SHALL NOT rely on AI semantic grading to decide correctness.
