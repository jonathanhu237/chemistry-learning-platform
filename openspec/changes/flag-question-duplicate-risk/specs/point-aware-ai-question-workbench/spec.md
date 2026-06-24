## ADDED Requirements

### Requirement: Duplicate-aware candidate generation
The point-aware AI question workbench SHALL annotate generated candidates with same-point duplicate-risk metadata.

#### Scenario: Candidate is generated
- **WHEN** the workbench stores a generated candidate and its backing draft
- **THEN** the backend SHALL evaluate duplicate risk against published questions, active drafts, and earlier candidates in the same generation batch for the same point
- **AND** it SHALL store the duplicate-risk result in the draft payload metadata.

#### Scenario: Teacher edits a draft candidate
- **WHEN** a teacher saves edits to a workbench draft candidate
- **THEN** the backend SHALL recompute duplicate risk for the edited payload
- **AND** the updated draft SHALL retain the latest duplicate-risk result.

#### Scenario: Candidate is published
- **WHEN** a teacher publishes a workbench candidate or its backing draft
- **THEN** the backend SHALL refresh duplicate-risk metadata before publication
- **AND** it SHALL allow publication even when duplicate risk is present.
