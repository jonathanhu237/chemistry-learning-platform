# student-h5-assessment-flow Specification

## Purpose
Define student H5 pretest, posttest, explanation caching, mastery update, and recommendation safety behavior.
## Requirements
### Requirement: Student pretest session lifecycle
The system SHALL let students start, continue, and submit pretest sessions using server-side session records.

#### Scenario: Student starts a pretest
- **WHEN** an authenticated student starts a pretest
- **THEN** the backend SHALL create or return the current open pretest session
- **AND** it SHALL return questions without exposing hidden answer keys.

#### Scenario: Student submits a pretest
- **WHEN** a student submits answers for an open pretest session
- **THEN** the backend SHALL grade the answers
- **AND** it SHALL persist the completed session and item outcomes for later learning context.

### Requirement: Student posttest session lifecycle
The system SHALL let students start, continue, and submit posttest sessions after learning activity.

#### Scenario: Student starts a posttest
- **WHEN** an authenticated student starts a posttest for an available experiment context
- **THEN** the backend SHALL create or return an eligible posttest session
- **AND** it SHALL return questions without exposing hidden answer keys.

#### Scenario: Student submits a posttest
- **WHEN** a student submits answers for an open posttest session
- **THEN** the backend SHALL grade the answers
- **AND** it SHALL persist score, item outcomes, and mistake details for review.

### Requirement: Cached student assessment explanations
The system SHALL provide cached posttest summaries and wrong-answer explanations without requiring repeated AI generation for unchanged completed attempts.

#### Scenario: Student requests posttest summary
- **WHEN** a completed posttest has a cached AI summary
- **THEN** the backend SHALL return the cached summary
- **AND** it SHALL NOT regenerate it unless cache invalidation rules require regeneration.

#### Scenario: Student requests mistake explanation
- **WHEN** a completed posttest contains wrong answers eligible for review
- **THEN** the backend SHALL return generated or cached explanations only for the student's submitted mistakes
- **AND** it SHALL NOT reveal answers for unrelated unsubmitted assessment items.

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
- **AND** the returned learning payload MUST still use the seed-backed profile, catalog chapter, and point grouping contract.

#### Scenario: Mastery data is missing
- **WHEN** no experiment mastery evidence exists or the mastery query is unavailable
- **THEN** the recommendation logic MUST fall back to existing seed, pretest-area, and default profile behavior.
