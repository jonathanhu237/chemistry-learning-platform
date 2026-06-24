## ADDED Requirements

### Requirement: Teacher-visible duplicate risk hints
The teacher question-bank management UI SHALL show concise duplicate-risk hints for draft questions without blocking teacher publication.

#### Scenario: Draft has duplicate risk
- **WHEN** a draft in the teacher review list has duplicate-risk metadata indicating possible duplication
- **THEN** the UI SHALL show a teacher-readable duplicate-risk tag
- **AND** it SHALL show the count and brief summary of similar same-point questions.

#### Scenario: Teacher publishes risky draft
- **WHEN** a teacher attempts to publish a draft with duplicate-risk metadata indicating possible duplication
- **THEN** the UI SHALL include the duplicate-risk warning in the publish confirmation
- **AND** the teacher SHALL still be able to confirm publication.

#### Scenario: Draft has no duplicate risk
- **WHEN** a draft has no detected duplicate risk
- **THEN** the UI SHALL NOT show duplicate-risk warnings for that draft.
