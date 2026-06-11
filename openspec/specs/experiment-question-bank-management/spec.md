# experiment-question-bank-management Specification

## Purpose
Define chapter-first teacher management of the objective question bank, including experiment-linked storage, default AI seeding, read-only browsing, assistant-generated proposals, and teacher confirmation before live bank changes.
## Requirements
### Requirement: Experiment-linked question storage

The system SHALL keep student-facing questions linked to experiment units internally while presenting teacher management by theory chapter.

#### Scenario: Teacher opens question bank management

- **GIVEN** the formal experiment catalog and theory chapters are available
- **WHEN** a teacher opens question bank management
- **THEN** the console SHALL show question bank status by theory chapter
- **AND** it SHALL allow drilling into chapter details while retaining experiment linkage on each question.

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

### Requirement: Chapter-first question bank overview
The system SHALL present the teacher-facing question bank by theory chapter rather than by experiment bank.

#### Scenario: Teacher opens question bank management
- **WHEN** a teacher opens the question bank management page
- **THEN** the console SHALL show theory chapters as the primary rows or cards
- **AND** each chapter SHALL show counts for total questions, choice questions, true/false questions, fill-blank questions, enabled questions, and disabled questions.

#### Scenario: Chapter has experiment-linked questions
- **WHEN** a question is linked to an experiment that is bound to a theory chapter
- **THEN** the chapter overview SHALL count the question under that chapter even if the question has no direct chapter id stored.

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
The system SHALL provide an AI assistant for adding, repairing, checking, and disabling question bank items.

#### Scenario: Teacher asks the assistant to add questions
- **WHEN** a teacher requests new objective questions for a chapter or linked experiment
- **THEN** the assistant SHALL use available experiment material and theory RAG context to propose structured objective questions
- **AND** the proposed questions SHALL remain outside the live bank until confirmed.

#### Scenario: Teacher asks the assistant to repair a question
- **WHEN** a teacher requests a fix for an existing question
- **THEN** the assistant SHALL propose a replacement or correction with answer, explanation, and source rationale
- **AND** it SHALL not mutate the live question until the teacher confirms the proposal.

#### Scenario: Teacher asks the assistant to inspect coverage
- **WHEN** a teacher requests a coverage check for a chapter
- **THEN** the assistant SHALL summarize question coverage by objective type and linked experiments
- **AND** it SHALL identify likely gaps without changing the bank.

### Requirement: Two-column question bank workspace
The system SHALL keep the question bank main page as a focused two-column workspace aligned with the existing admin console interaction model.

#### Scenario: Teacher opens the question bank page
- **WHEN** a teacher opens question bank management
- **THEN** the main workspace SHALL show chapter bank navigation on the left
- **AND** it SHALL show the selected chapter's question list on the right
- **AND** it SHALL NOT show permanent question-detail or assistant cards below the list.

#### Scenario: Teacher selects a chapter
- **WHEN** a teacher selects a chapter from the chapter bank
- **THEN** the right pane SHALL update to that chapter's question list
- **AND** the filters, add-question action, and chapter counts SHALL remain in the chapter context.

#### Scenario: Teacher opens an existing question
- **WHEN** a teacher opens a question from the current chapter list
- **THEN** the console SHALL open a focused modal or drawer-like surface
- **AND** the surface SHALL show read-only question details, answer, explanation, linked experiment, status, and source evidence
- **AND** it SHALL include assistant actions for repair or disable proposals scoped to that question
- **AND** it SHALL NOT expose direct manual save controls for changing the question content.

#### Scenario: Teacher starts adding a question
- **WHEN** a teacher chooses to add questions for the selected chapter
- **THEN** the console SHALL open a focused modal or drawer-like surface
- **AND** the assistant SHALL be scoped to the selected chapter and optional linked experiment
- **AND** generated questions SHALL remain preview proposals until a confirmation flow applies them.
