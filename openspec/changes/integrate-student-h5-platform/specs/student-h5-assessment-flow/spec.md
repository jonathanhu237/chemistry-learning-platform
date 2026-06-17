## ADDED Requirements

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
