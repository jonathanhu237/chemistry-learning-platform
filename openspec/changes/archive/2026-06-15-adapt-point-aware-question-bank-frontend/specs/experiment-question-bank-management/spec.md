## ADDED Requirements

### Requirement: Point-aware experiment question bank browsing
The teacher-facing question bank page SHALL present the imported point-aware default bank by experiment and video point while preserving read-only browsing.

#### Scenario: Teacher opens the point-aware question bank page
- **WHEN** a teacher opens question bank management after a point-aware default bank has been imported
- **THEN** the console SHALL show formal experiments as the primary navigation
- **AND** each experiment row SHALL show published question count and question type composition.

#### Scenario: Teacher filters point-aware questions
- **WHEN** a teacher selects an experiment
- **THEN** the console SHALL list current published questions for that experiment
- **AND** it SHALL allow filtering by question type, primary experiment point, and keyword.

#### Scenario: Teacher scans question coverage
- **WHEN** point-aware question metadata is available
- **THEN** the question list SHALL show primary point titles and evidence status for each question
- **AND** it SHALL visually distinguish multi-point questions without exposing internal rebuild notes.

### Requirement: Point-aware question detail evidence
The teacher-facing question detail view SHALL expose the source and diagnostic metadata needed to audit the imported bank.

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

## MODIFIED Requirements

### Requirement: Experiment-linked question storage

The system SHALL keep student-facing questions linked to experiment units internally while presenting teacher management by formal experiment and experiment video point when point-aware metadata is available.

#### Scenario: Teacher opens question bank management

- **GIVEN** the formal experiment catalog and point-aware default bank are available
- **WHEN** a teacher opens question bank management
- **THEN** the console SHALL show question bank status by formal experiment
- **AND** it SHALL allow drilling into experiment details while retaining chapter linkage on each question where available.

#### Scenario: Question belongs to an experiment

- **GIVEN** a question is saved for student practice or testing
- **WHEN** the question is stored
- **THEN** it SHALL reference at least one formal experiment unit when the question is experiment-derived
- **AND** it MAY reference related theory chapters or KC/KP nodes for grounding and analytics.

### Requirement: Two-column question bank workspace
The system SHALL keep the question bank main page as a focused two-column workspace aligned with the existing admin console interaction model.

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
- **THEN** the console SHALL open a focused modal or drawer-like surface
- **AND** the surface SHALL show read-only question details, answer, explanation, linked experiment, status, primary points, source evidence, and option-level diagnostics where available
- **AND** it SHALL NOT expose direct manual save controls for changing the question content.

#### Scenario: Teacher filters by point
- **WHEN** a teacher chooses a primary experiment point filter
- **THEN** the current experiment question list SHALL show only questions linked to that point
- **AND** clearing the filter SHALL restore the selected experiment's question list.

## REMOVED Requirements

### Requirement: Chapter-first question bank overview
**Reason**: The imported production bank is now organized around formal experiments, video points, source evidence, and option diagnostics. A chapter-first page hides the primary quality and analytics metadata needed for release.

**Migration**: Keep chapter endpoints available for compatibility, but use the point-aware experiment question bank workspace as the primary teacher browsing path.
