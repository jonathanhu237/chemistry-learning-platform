## MODIFIED Requirements

### Requirement: Teacher workflow navigation
The teacher console SHALL expose navigation organized around teacher operations for the experiment-centered product direction without feature-tier branching between teacher-console roles.

#### Scenario: Teacher views navigation
- **GIVEN** a teacher-console user is logged in
- **WHEN** the teacher menu is displayed
- **THEN** the menu SHALL include dashboards for overview, classes and students, experiment management, question bank management, learning analytics, learning assistant, intelligent monitoring, learning resources, feedback, and system settings
- **AND** the Classes and Students route SHALL use card-first class navigation rather than a table-first class list
- **AND** the Experiment Management route SHALL include video resource management inside experiment detail
- **AND** it SHALL NOT present course version management or video resources as primary teacher workflows.

#### Scenario: Teacher opens deprecated review workflow
- **GIVEN** a teacher previously used the generic question review workflow
- **WHEN** they look for question administration
- **THEN** the console SHALL route them to experiment question bank management
- **AND** it SHALL NOT expose generic "question review" as the main workflow.

#### Scenario: Legacy teacher views navigation
- **GIVEN** a legacy `role='teacher'` user is logged in
- **WHEN** the teacher menu is displayed
- **THEN** the navigation SHALL match the complete navigation available to `role='admin'`
- **AND** it SHALL NOT hide learning assistant, intelligent monitoring, or other teacher-console modules because of role.

## ADDED Requirements

### Requirement: Operational monitoring route layout
The teacher console SHALL support dense operational pages that use Ant Design modules, tabs, tags, alerts, tables/lists, and responsive grids without becoming landing pages or monolithic card stacks.

#### Scenario: Intelligent monitoring route opens
- **WHEN** a teacher opens the `智能监控` route
- **THEN** the page SHALL render the operational content directly after the page title
- **AND** it SHALL use tabs or equivalent module navigation for detailed diagnostics rather than a single long card stack.

#### Scenario: Monitoring page contains many diagnostic panels
- **WHEN** the page needs to show OpenAI, RAG, ES, dictionary, outbox, guardrail, and trend diagnostics
- **THEN** related panels SHALL be grouped inside named modules
- **AND** the default view SHALL prioritize status and next action over exhaustive detail.

#### Scenario: Monitoring page is viewed on narrow laptop widths
- **WHEN** the left shell navigation and page content compete for horizontal space
- **THEN** the monitoring route SHALL stack or wrap module content without requiring horizontal page scrolling
- **AND** primary actions such as refresh, search diagnostics, and module navigation SHALL remain reachable.
