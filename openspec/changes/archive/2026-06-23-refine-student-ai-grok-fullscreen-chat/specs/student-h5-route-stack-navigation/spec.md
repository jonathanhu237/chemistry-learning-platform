## MODIFIED Requirements

### Requirement: Root pages own list and center workflows
Each first-level root route SHALL own the browsing, center, account, or entry workflow for its destination rather than rendering an unrelated detail task as its only content. The AI root is a special root workflow: it owns the default/global AI conversation directly, while contextual AI handoffs from other pages remain second-level detail routes.

#### Scenario: Student opens learning root
- **WHEN** the student opens the `learn` root
- **THEN** the page MUST provide the periodic-table learning entry and recommendation guidance
- **AND** it MUST NOT render a selected-area chapter list, specific chapter, catalog directory, or point detail as root content unless that target is explicitly opened as a non-tab detail route.

#### Scenario: Student opens AI root
- **WHEN** the student opens the `ai` root
- **THEN** the page MUST provide the default/global AI conversation directly in the root route
- **AND** the page MUST provide root-only history access for saved AI conversations
- **AND** the page MUST NOT navigate to `/ai/chat` merely to start a default/global conversation.

#### Scenario: Contextual AI opens as detail
- **WHEN** a student opens AI from a point detail, chapter detail, element detail, video result, assessment report, or another contextual page
- **THEN** the app MUST push the shared `/ai/chat` detail route
- **AND** the detail route MUST accept optional context from the opening source without changing root tab identity
- **AND** the detail route MUST NOT show the root history action.

#### Scenario: Student opens assessment root
- **WHEN** the student opens the `assessment` root
- **THEN** the page MUST provide assessment-center content such as available assessments, reports, or mistake-review entry points
- **AND** answering a test or viewing a report MUST use the matching detail page.
