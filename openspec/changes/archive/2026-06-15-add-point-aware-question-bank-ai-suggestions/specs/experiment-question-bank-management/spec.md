## ADDED Requirements

### Requirement: Point-aware AI suggestion entry points
The teacher-facing point-aware question-bank page SHALL expose AI add and repair suggestion workflows that use the selected experiment and question metadata.

#### Scenario: Teacher opens the experiment question-bank page
- **WHEN** a teacher selects a formal experiment in question-bank management
- **THEN** the page SHALL offer an AI add-suggestion action for that experiment
- **AND** the action SHALL allow optional targeting of an available primary experiment point.

#### Scenario: Teacher opens a question detail surface
- **WHEN** a teacher views a point-aware question detail
- **THEN** the detail surface SHALL offer an AI repair-suggestion action for that question
- **AND** the action SHALL keep the current question read-only until a generated draft is explicitly published.

#### Scenario: AI suggestion drafts are returned
- **WHEN** add or repair suggestions are generated
- **THEN** the page SHALL show draft suggestions with validation status
- **AND** the teacher SHALL be able to publish or reject each draft without leaving the point-aware question-bank workflow.
