# point-context-learning-assistant Specification

## Purpose
TBD - created by archiving change point-context-learning-assistant. Update Purpose after archive.
## Requirements
### Requirement: Structured point context request
The learning assistant SHALL accept optional structured video-point context in addition to the student question.

#### Scenario: Prompt suggestion sends point context
- **WHEN** a student or admin selects a video-point prompt suggestion
- **THEN** the request SHALL include the selected `chapter_id`, `experiment_id`, and `point_key`
- **AND** the backend SHALL preserve the original student-facing question text.

#### Scenario: Free-form question without point context
- **WHEN** a student sends a free-form question from a chapter page without selecting a point
- **THEN** the request SHALL still include the selected `chapter_id`
- **AND** the assistant SHALL continue to answer using chapter context and optional RAG behavior.

### Requirement: Fixed point evidence package
The learning assistant SHALL assemble a fixed point evidence package whenever structured point context is provided.

#### Scenario: Point context has manually reviewed evidence
- **WHEN** a request includes an `experiment_id` and `point_key`
- **THEN** the backend SHALL resolve the experiment point metadata
- **AND** it SHALL load the manual-reviewed point evidence binding for that `(experiment_id, point_key)`
- **AND** it SHALL hydrate reviewed `experiment_chunk_ids` and `theory_chunk_ids` from `source_chunks` for the fixed evidence package.

#### Scenario: RAG is disabled for a point request
- **WHEN** a point-context request is submitted with RAG lookup disabled
- **THEN** the assistant SHALL still receive the fixed point evidence package
- **AND** it SHALL answer from point evidence and reliable chemistry knowledge without claiming supplemental RAG evidence was used.

#### Scenario: RAG is enabled for a point request
- **WHEN** a point-context request is submitted with RAG lookup enabled
- **THEN** the fixed point evidence package SHALL be available before supplemental retrieval
- **AND** hybrid RAG SHALL only add broader supporting evidence rather than replacing the fixed point context.

#### Scenario: Point reviewed evidence is weak but available
- **WHEN** the selected point evidence has review grade `weak_but_best_available`
- **THEN** the assistant SHALL still receive the reviewed point evidence
- **AND** diagnostics SHALL expose the review grade
- **AND** the assistant SHALL avoid overstating the strength or completeness of that evidence.

#### Scenario: Point evidence is unavailable
- **WHEN** the backend cannot find a manual-reviewed evidence binding for the selected point
- **THEN** the assistant SHALL keep the structured point metadata in context
- **AND** it SHALL NOT query question-bank `source_audit` as a fallback fixed evidence source
- **AND** it SHALL avoid claiming a specific textbook source that was not found.

### Requirement: Point context diagnostics
The learning assistant response SHALL expose point-context diagnostics for admin inspection.

#### Scenario: Admin inspects point-context turn
- **WHEN** an admin selects a turn that included `point_key`
- **THEN** diagnostics SHALL show the resolved chapter, experiment, point key, point title when available, point evidence count, manual review flag, and review grade
- **AND** diagnostics SHALL distinguish fixed point evidence from supplemental RAG evidence.

### Requirement: Atom-selected point context enters fixed point assistant flow
The learning assistant SHALL treat a point selected from the Atom root picker as structured point context for the assistant request.

#### Scenario: Atom root sends selected point context
- **WHEN** the student submits a question from the Atom root chat after selecting a concrete point placement
- **THEN** the assistant request MUST include the selected point's structured context fields
- **AND** the backend point-context flow MUST be able to resolve fixed point evidence from the provided experiment, point, placement, source node, or equivalent ids when available.

#### Scenario: Selected point has partial metadata
- **WHEN** the selected point context is missing optional metadata such as related knowledge ids or experiment identity
- **THEN** the assistant request MUST still include the available point title, summary, chapter identity, placement or source node identity, and catalog path
- **AND** the assistant MUST avoid claiming missing fixed evidence as if it were resolved.

### Requirement: One chat uses one selected point context
The learning assistant SHALL keep one selected point context stable for a root Atom chat after the first user message.

#### Scenario: Follow-up question in bound chat
- **WHEN** a student asks a follow-up question in a root Atom chat that was started with a selected point
- **THEN** the assistant request MUST continue to include the same selected point context
- **AND** recent visible conversation turns MUST remain associated with that point context.

#### Scenario: Attempted mid-chat point change
- **WHEN** a root Atom chat already has at least one submitted user message with selected point context
- **AND** the student attempts to choose a different point
- **THEN** the app MUST prevent silent context replacement for that chat
- **AND** the student MUST be directed to start a new Atom chat before using the different point context.

### Requirement: Directory browsing does not create fixed point evidence
The learning assistant SHALL only enter fixed point-context behavior when a concrete point placement is selected.

#### Scenario: Student opens directories in picker
- **WHEN** the student navigates catalog directories inside the Atom picker
- **THEN** directory navigation MUST NOT create or send fixed point evidence context by itself
- **AND** only selecting a concrete point row MUST bind point context to the chat.

#### Scenario: Search matches directory text
- **WHEN** a picker search recalls points through matching directory or catalog-path text
- **THEN** selecting a concrete descendant point result MUST bind that point placement
- **AND** selecting the directory context alone MUST NOT bind fixed point evidence.
