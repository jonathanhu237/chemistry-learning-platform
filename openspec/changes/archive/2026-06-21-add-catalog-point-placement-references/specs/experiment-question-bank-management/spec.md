## MODIFIED Requirements

### Requirement: Point-aware question bank browsing
The teacher-facing question bank page SHALL present point-aware question data by experiment and canonical experiment point while preserving placement-aware chapter/path context.

#### Scenario: Teacher opens the point-aware question bank page
- **WHEN** a teacher opens question bank management after point-aware question data is available
- **THEN** the console SHALL show formal experiments or catalog contexts as the primary navigation according to the current product flow
- **AND** each point-aware row SHALL resolve questions by canonical experiment point id rather than by placement id alone.

#### Scenario: Teacher filters point-aware questions
- **WHEN** a teacher selects an experiment, chapter, placement path, or canonical experiment point in question-bank management
- **THEN** the console SHALL list current published questions linked to the matching canonical point ids
- **AND** it SHALL preserve placement/chapter context in labels, breadcrumbs, and filters where available.

#### Scenario: Teacher scans question coverage
- **WHEN** point-aware question metadata is available
- **THEN** the question list SHALL show canonical point titles, placement context where relevant, and evidence status for each question
- **AND** it SHALL visually distinguish multi-point questions without exposing internal migration notes.

#### Scenario: Same canonical point appears in multiple placements
- **WHEN** a canonical experiment point is reused under multiple catalog paths
- **THEN** the question bank MUST avoid counting the same canonical point question as separate independent point coverage merely because it has multiple placements
- **AND** any placement-based counts MUST be labeled as placement/context coverage rather than canonical question identity.

### Requirement: Point-aware question detail evidence
The teacher-facing question detail view SHALL expose source and diagnostic metadata using canonical point identity and placement context.

#### Scenario: Teacher opens a point-aware question
- **WHEN** a teacher opens a question detail surface
- **THEN** the console SHALL show stem, options, deterministic answer, explanation, linked experiment, canonical primary points, source placement context where available, source audit status, and source references.

#### Scenario: Teacher opens a single-choice question
- **WHEN** a single-choice question has option-level diagnostic links
- **THEN** the detail surface SHALL show each option's diagnostic role and linked canonical point or note in a teacher-readable format
- **AND** it SHALL show placement context only when it helps explain the question's chapter/path origin.

#### Scenario: Teacher opens a fill-blank question
- **WHEN** a fill-blank question has accepted answer aliases
- **THEN** the detail surface SHALL show deterministic accepted answers for teacher inspection
- **AND** it SHALL not imply that AI semantic judging is used.

#### Scenario: Teacher launches repair from point-aware detail
- **WHEN** a teacher launches AI repair from the point-aware detail surface
- **THEN** the repair session SHALL receive the same source evidence, canonical point ids, placement context, answer data, and option diagnostics shown in the detail surface
- **AND** the workbench SHALL keep that original detail available throughout the repair conversation.

### Requirement: Point-aware AI suggestion entry points
The teacher-facing point-aware question-bank page SHALL expose AI add and repair suggestion workflows that use selected canonical experiment points and placement context.

#### Scenario: Teacher opens the experiment question-bank page
- **WHEN** a teacher selects a formal experiment, chapter path, or catalog placement in question-bank management
- **THEN** the page SHALL offer an AI add-suggestion action for the resolved canonical experiment point or selected context
- **AND** the action SHALL preserve source placement context when the teacher started from a specific placement.

#### Scenario: Teacher opens a question detail surface
- **WHEN** a teacher views a point-aware question detail
- **THEN** the detail surface SHALL offer an AI repair-suggestion action for that question
- **AND** the action SHALL keep the current question read-only until a generated draft is explicitly published.

#### Scenario: AI suggestion drafts are returned
- **WHEN** add or repair suggestions are generated
- **THEN** the page SHALL show draft suggestions with validation status
- **AND** every generated draft tied to point-specific evidence SHALL reference canonical experiment point ids rather than placement ids alone.

### Requirement: Point-aware diagnostic release evidence
The system SHALL keep release evidence for point-aware question banks inspectable by administrators and teachers using canonical point identity.

#### Scenario: Release bank is audited
- **WHEN** an administrator inspects an imported or generated point-aware default bank
- **THEN** the system SHALL expose or preserve validation evidence showing question count, experiment coverage, canonical point bindings, placement contexts where available, source refs, source audit status, option links, and deterministic answer shape.

#### Scenario: Teacher inspects a migrated question
- **WHEN** a teacher opens a migrated question detail
- **THEN** the console SHALL show the linked experiment, canonical primary point titles, placement context where available, evidence status, source references, answer, explanation, and option-level diagnostic links where available.

#### Scenario: Placement is removed after question creation
- **WHEN** a placement associated with a question's source context is later removed
- **THEN** the question MUST continue to resolve through its canonical experiment point binding
- **AND** the removed placement context MUST remain audit metadata rather than the live question identity.
