# experiment-question-bank-management Specification

## Purpose
Define chapter-first teacher management of the objective question bank, including experiment-linked storage, default AI seeding, read-only browsing, assistant-generated proposals, and teacher confirmation before live bank changes.
## Requirements
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

### Requirement: One-time default AI question bank import

The system SHALL support default AI-generated question bank seeding as a controlled backend or administrator operation, not as a normal teacher upload workflow.

#### Scenario: Default bank is seeded

- **GIVEN** a validated default question bank file or seed dataset exists
- **WHEN** an administrator or deployment process imports it
- **THEN** the system SHALL create or update experiment-linked objective questions
- **AND** it SHALL record import source, import time, operator or process, and validation result.

#### Scenario: Teacher opens the question bank page

- **GIVEN** a teacher has access to the question bank management page
- **WHEN** the page renders
- **THEN** it SHALL NOT expose manual JSON import as a normal teacher workflow.

#### Scenario: Import file contains unsupported questions

- **GIVEN** an import file contains non-objective questions or malformed answers
- **WHEN** the import is validated
- **THEN** the system SHALL reject the invalid items with row-level errors
- **AND** it SHALL not silently publish invalid questions.

### Requirement: Objective question type constraint

Student-facing question banks SHALL support only objective question types for the first delivery.

#### Scenario: Question is saved

- **GIVEN** a question is seeded or accepted from an AI change proposal
- **WHEN** the question is saved for student use
- **THEN** its type SHALL be one of `single_choice`, `true_false`, or `fill_blank`
- **AND** the stored answer structure SHALL be machine-gradable.

#### Scenario: Fill blank answer is saved

- **GIVEN** a fill blank question has one or more accepted answers
- **WHEN** the answer is stored
- **THEN** the system SHALL store normalized accepted answers and matching rules
- **AND** the grading API SHALL be able to evaluate the response without manual review.

### Requirement: Teacher prompt-based RAG generation

The system SHALL support teacher prompt-based question bank assistance using RAG as optional grounding.

#### Scenario: Teacher requests question bank help

- **GIVEN** a teacher enters a natural-language request for a chapter, experiment, or existing question
- **WHEN** they submit the request to the question bank assistant
- **THEN** the backend SHALL retrieve relevant experiment material and optional theory KC/KP chunks
- **AND** it SHALL ask the configured LLM to return a structured change proposal.

#### Scenario: RAG evidence is available

- **GIVEN** the assistant retrieved source chunks
- **WHEN** a proposal is presented
- **THEN** each proposed question or repair SHALL preserve source references, prompt text, model metadata, generation time, and operator
- **AND** the admin console SHALL show evidence references where available.

#### Scenario: RAG evidence is insufficient

- **GIVEN** the selected chapter or experiment has little or no indexed experiment material
- **WHEN** assistance is requested
- **THEN** the backend MAY use related theory RAG chunks as support
- **AND** it SHALL warn the teacher that experiment source coverage is limited.

### Requirement: Human confirmation before publication

AI-generated or AI-repaired questions SHALL require teacher preview and confirmation before becoming student-facing bank changes.

#### Scenario: Assistant returns a change proposal

- **GIVEN** assistance succeeds
- **WHEN** proposed changes are presented to the teacher
- **THEN** the teacher SHALL be able to accept, reject, or request another AI revision
- **AND** no generated or repaired question SHALL be published automatically without confirmation.

#### Scenario: Teacher applies a proposal

- **GIVEN** a proposed change passes validation
- **WHEN** the teacher confirms the change
- **THEN** the system SHALL apply the change to the current question bank
- **AND** it SHALL retain generation lineage for audit and later quality review.

### Requirement: Read-only question browsing
The system SHALL allow teachers to inspect current question bank content without exposing normal manual creation, import, or edit controls.

#### Scenario: Teacher views chapter question details
- **WHEN** a teacher opens a chapter's question bank details
- **THEN** the console SHALL list questions for that chapter
- **AND** it SHALL show question type, stem, answer, explanation, linked experiments, status, and source evidence where available.

#### Scenario: Teacher filters chapter questions
- **WHEN** a teacher filters chapter questions by type, status, linked experiment, or keyword
- **THEN** the console SHALL return matching current-bank questions only
- **AND** it SHALL preserve the chapter context.

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

### Requirement: Point-aware question bank demo
The system SHALL support a small, non-published demo workflow for reviewing point-aware question bank data before full bank regeneration.

#### Scenario: Demo scope is selected
- **WHEN** the demo is run
- **THEN** it SHALL be limited to `EXP_19_1_01`
- **AND** it SHALL NOT mutate published student-facing question bank data.

#### Scenario: Existing draft questions are sampled
- **WHEN** existing draft questions are used in the demo
- **THEN** they SHALL be treated only as candidate material
- **AND** each sampled question SHALL be reviewed one by one against canonical source evidence.

#### Scenario: Point-aware demo artifact is produced
- **WHEN** the demo review completes
- **THEN** it SHALL produce assessment point, reviewed question, and review report artifacts
- **AND** the artifacts SHALL show question-level video point key bindings, option-level video point key bindings where applicable, source audit decisions, and quality outcomes.

#### Scenario: Demo question is unsuitable
- **WHEN** a candidate question is too simple or poorly grounded
- **THEN** the review artifact SHALL mark it as rewrite or reject
- **AND** every rewrite SHALL include a concrete proposed rewritten question.

#### Scenario: Demo fill blank stays objective
- **WHEN** a proposed replacement uses `fill_blank`
- **THEN** it SHALL be answerable with a short phone-friendly accepted answer
- **AND** it SHALL NOT rely on AI semantic grading to decide correctness.

### Requirement: Point-aware default bank review
The system SHALL support replacing the default experiment question bank with a validated point-aware reviewed version of the existing bank.

#### Scenario: Full reviewed artifact is produced
- **WHEN** the existing 2,310-question bank is reviewed
- **THEN** the artifact SHALL cover all published formal experiments selected for the default bank
- **AND** every accepted experiment-derived question SHALL bind to one or more existing experiment video point keys.

#### Scenario: Existing draft bank is used as the primary review source
- **WHEN** the current 2,310-question bank is inspected during review
- **THEN** every old question SHALL receive a review decision of `keep`, `rewrite`, or `reject`
- **AND** no old question SHALL be preserved without source audit, quality review, and point-key binding
- **AND** every `rewrite` or `reject` decision SHOULD include a concrete replacement question unless the source evidence is insufficient.

#### Scenario: Reviewed bank is imported
- **WHEN** an administrator imports the reviewed default bank
- **THEN** the backend SHALL validate the artifact before mutating the active bank
- **AND** it SHALL record bank version, import source, validation report, import time, and operator or process.

#### Scenario: Validation fails
- **WHEN** any accepted item has invalid type, invalid answer shape, missing point keys, unresolved point keys, missing source audit, or unsupported evidence
- **THEN** the import SHALL fail with item-level errors
- **AND** it SHALL NOT partially publish the invalid bank.

### Requirement: Objective reviewed question quality
The reviewed default bank SHALL keep student-facing questions objective, deterministic, and suitable for the mobile learning client.

#### Scenario: Reviewed question is accepted
- **WHEN** a kept or replacement question is accepted
- **THEN** its type SHALL be one of `single_choice`, `true_false`, or `fill_blank`
- **AND** its answer SHALL be machine-gradable without AI semantic judging.

#### Scenario: Fill blank question is accepted
- **WHEN** a regenerated fill-blank question is accepted
- **THEN** every accepted answer SHALL be a short token or short phrase suitable for phone input
- **AND** the grading rules SHALL be deterministic after normalization.

#### Scenario: Fill blank is too complex
- **WHEN** a fill-blank candidate expects a reagent combination, full equation, multi-clause explanation, or free-form reasoning
- **THEN** it SHALL be rewritten as single choice, true/false, or a short deterministic fill blank
- **AND** the original candidate SHALL NOT be accepted unchanged.

#### Scenario: Question is too shallow
- **WHEN** a candidate only tests direct formula recitation, one-step reagent recall, or a final order without experimental reasoning
- **THEN** it SHALL be rewritten or rejected
- **AND** the review artifact SHALL record the quality flag.

### Requirement: Review coverage audit
The system SHALL produce a coverage and quality audit for the reviewed bank before import.

#### Scenario: Coverage audit runs
- **WHEN** the reviewed artifact is validated
- **THEN** the audit SHALL summarize counts by formal experiment, video point, question type, coverage tag, and review decision
- **AND** it SHALL list experiments or video points with no accepted questions.

#### Scenario: Source audit runs
- **WHEN** the reviewed artifact is validated
- **THEN** the audit SHALL summarize canonical evidence usage, supporting theory usage, insufficient-evidence rejections, and unresolved source references.

#### Scenario: Admin browses reviewed questions
- **WHEN** the question bank page displays imported reviewed questions
- **THEN** existing read-only browsing SHALL show linked experiment, point titles, source status, answer, explanation, and review lineage where available
- **AND** it SHALL NOT expose normal manual edit or upload controls.

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

