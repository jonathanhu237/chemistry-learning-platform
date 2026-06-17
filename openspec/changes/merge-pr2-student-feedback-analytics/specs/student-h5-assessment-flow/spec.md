## ADDED Requirements

### Requirement: Assessments update experiment mastery
Student H5 pretest and posttest submissions SHALL update experiment-level mastery evidence when submitted answers can be associated with formal experiments.

#### Scenario: Pretest submission records experiment mastery
- **WHEN** a student submits a completed pretest with graded question attempts linked to formal experiments
- **THEN** the backend MUST update experiment-level mastery state for those experiments
- **AND** it MUST preserve evidence kind and evidence identifier metadata for later analytics.

#### Scenario: Posttest submission records experiment mastery
- **WHEN** a student submits a completed posttest with graded question attempts linked to formal experiments
- **THEN** the backend MUST update experiment-level mastery state for those experiments
- **AND** the posttest report MUST be able to show experiment-level mastery changes where available.

#### Scenario: Experiment mastery table is unavailable before migration
- **WHEN** a local or test database lacks the experiment mastery table
- **THEN** student assessment submission MUST fail gracefully or skip optional mastery updates according to existing compatibility barriers
- **AND** core pretest/posttest completion MUST remain reliable.

### Requirement: Experiment mastery informs learning recommendation safely
The student H5 learning recommendation logic SHALL be allowed to use experiment mastery as an optional signal without replacing seed-backed current-chapter selection.

#### Scenario: Mastery data exists for candidate chapters
- **WHEN** experiment mastery data exists for a student's candidate chapter experiments
- **THEN** the recommendation logic MAY choose the weakest relevant current-family chapter profile
- **AND** the returned learning payload MUST still use the seed-backed profile and chapter experiment grouping contract.

#### Scenario: Mastery data is missing
- **WHEN** no experiment mastery evidence exists or the mastery query is unavailable
- **THEN** the recommendation logic MUST fall back to existing seed, pretest-area, and default profile behavior.
