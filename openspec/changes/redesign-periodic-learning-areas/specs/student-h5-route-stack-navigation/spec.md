## MODIFIED Requirements

### Requirement: Root pages own list and center workflows
Each first-level root route SHALL own the browsing, center, account, or entry workflow for its destination rather than rendering a detail task as its only content.

#### Scenario: Student opens learning root
- **WHEN** the student opens the `learn` root
- **THEN** the page MUST provide the periodic-table learning entry and a separate smart recommendation card
- **AND** the periodic-table entry MUST remain a selector for learning areas rather than an inline chapter list
- **AND** it MUST NOT render a selected-area chapter list, specific chapter, catalog directory, or point detail as root content unless that target is explicitly opened as a non-tab detail route.

#### Scenario: Student opens AI root
- **WHEN** the student opens the `ai` root
- **THEN** the page MUST provide an AI center such as new chat entry, chat history, or suggested prompt entry points
- **AND** entering an actual conversation MUST use the shared AI chat detail page.

#### Scenario: Student opens assessment root
- **WHEN** the student opens the `assessment` root
- **THEN** the page MUST provide assessment-center content such as available assessments, reports, or mistake-review entry points
- **AND** answering a test or viewing a report MUST use the matching detail page.
