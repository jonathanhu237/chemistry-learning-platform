## MODIFIED Requirements

### Requirement: AI-assisted question bank changes
The system SHALL provide a context-preserving AI workbench for adding, repairing, checking, and disabling question bank items.

#### Scenario: Teacher asks the assistant to add questions
- **WHEN** a teacher requests new objective questions for a chapter, linked experiment, or selected experiment point
- **THEN** the assistant SHALL open or create a workbench session with the selected experiment and point context
- **AND** it SHALL use available experiment material and theory RAG context to propose structured objective candidate questions
- **AND** the proposed questions SHALL remain outside the live bank until confirmed.

#### Scenario: Teacher asks the assistant to repair a question
- **WHEN** a teacher requests a fix for an existing question
- **THEN** the assistant SHALL open or create a repair workbench session anchored to that original question
- **AND** the workbench SHALL keep the original stem, answer, explanation, source evidence, point bindings, and option diagnostics visible while the teacher prompts AI
- **AND** the assistant SHALL propose replacement or correction candidates with answer, explanation, and source rationale
- **AND** it SHALL not mutate the live question until the teacher confirms a valid proposal.

#### Scenario: Teacher asks for another AI revision
- **WHEN** a teacher sends an additional prompt after receiving an AI candidate
- **THEN** the assistant SHALL continue the same workbench session
- **AND** it SHALL preserve prior teacher prompts, assistant responses, generated candidates, and candidate statuses.

#### Scenario: Teacher asks the assistant to inspect coverage
- **WHEN** a teacher requests a coverage check for a chapter, formal experiment, or selected experiment point
- **THEN** the assistant SHALL summarize question coverage by objective type and linked experiments or experiment points
- **AND** it SHALL identify likely gaps without changing the bank.

### Requirement: Two-column question bank workspace
The system SHALL keep the question bank main page as a focused two-column workspace aligned with the existing admin console interaction model, while opening AI repair/create work in a context-preserving workbench rather than a detached generation drawer.

#### Scenario: Teacher opens the question bank page
- **WHEN** a teacher opens question bank management
- **THEN** the main workspace SHALL show experiment bank navigation on the left
- **AND** it SHALL show the selected experiment's question list on the right
- **AND** it SHALL NOT show permanent question-detail, import, or manual edit cards below the list.

#### Scenario: Teacher selects an experiment
- **WHEN** a teacher selects an experiment from the experiment bank
- **THEN** the right pane SHALL update to that experiment's question list
- **AND** the filters and experiment counts SHALL remain in the experiment context.

#### Scenario: Teacher opens an existing question
- **WHEN** a teacher opens a question from the current experiment list
- **THEN** the console SHALL open a focused modal, drawer-like surface, or workbench entry surface
- **AND** the surface SHALL show read-only question details, answer, explanation, linked experiment, status, primary points, source evidence, and option-level diagnostics where available
- **AND** it SHALL NOT expose direct manual save controls for changing the question content.

#### Scenario: Teacher starts AI repair from question detail
- **WHEN** a teacher chooses AI repair from a question detail surface
- **THEN** the console SHALL open the AI question workbench for that question
- **AND** the workbench SHALL show the original question context and AI conversation together
- **AND** the console SHALL NOT show AI repair as a detached form that hides or obscures the original question being repaired.

#### Scenario: Teacher starts AI creation from experiment context
- **WHEN** a teacher chooses AI creation for the selected experiment or point
- **THEN** the console SHALL open the AI question workbench in create mode
- **AND** the workbench SHALL show selected experiment, point, source coverage, and generated candidates in one continuous surface.

#### Scenario: Teacher filters by point
- **WHEN** a teacher chooses a primary experiment point filter
- **THEN** the current experiment question list SHALL show only questions linked to that point
- **AND** clearing the filter SHALL restore the selected experiment's question list.

### Requirement: Point-aware question detail evidence
The teacher-facing question detail view SHALL expose the source and diagnostic metadata needed to audit the imported bank and start a context-preserving AI repair.

#### Scenario: Teacher opens a point-aware question
- **WHEN** a teacher opens a question detail surface
- **THEN** the console SHALL show stem, options, deterministic answer, explanation, linked experiment, primary points, source audit status, and source references.

#### Scenario: Teacher opens a single-choice question
- **WHEN** a single-choice question has option-level diagnostic links
- **THEN** the detail surface SHALL show each option's diagnostic role and linked point or note in a teacher-readable format.

#### Scenario: Teacher opens a fill-blank question
- **WHEN** a fill-blank question has accepted answer aliases
- **THEN** the detail surface SHALL show deterministic accepted answers for teacher inspection
- **AND** it SHALL not imply that AI semantic judging is used.

#### Scenario: Teacher launches repair from point-aware detail
- **WHEN** a teacher launches AI repair from the point-aware detail surface
- **THEN** the repair session SHALL receive the same source evidence, point keys, answer data, and option diagnostics shown in the detail surface
- **AND** the workbench SHALL keep that original detail available throughout the repair conversation.
