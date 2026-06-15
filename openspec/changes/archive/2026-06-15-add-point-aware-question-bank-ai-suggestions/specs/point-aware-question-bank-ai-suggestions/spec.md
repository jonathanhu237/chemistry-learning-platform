## ADDED Requirements

### Requirement: Point-aware suggestion context
The system SHALL build AI question-bank suggestions from the current formal experiment and point-aware question metadata.

#### Scenario: Teacher requests new questions for an experiment
- **WHEN** a teacher requests AI suggestions from the selected experiment question-bank page
- **THEN** the request SHALL include the formal experiment id
- **AND** it MAY include one selected experiment video point key
- **AND** generated suggestions SHALL preserve primary point keys, source audit metadata, option diagnostic links where applicable, and generation lineage.

#### Scenario: Teacher requests a repair for an existing question
- **WHEN** a teacher requests an AI repair suggestion from a question detail view
- **THEN** the request SHALL include the original question id
- **AND** the suggestion context SHALL include the original stem, answer, explanation, primary point keys, source audit, and option diagnostic links
- **AND** the returned draft SHALL record lineage back to the original question id.

### Requirement: Non-mutating suggestion drafts
AI suggestions SHALL be stored as teacher-reviewable drafts and SHALL NOT directly mutate the published default bank.

#### Scenario: Suggestion generation succeeds
- **WHEN** AI add or repair suggestions are generated
- **THEN** each suggestion SHALL be stored as an experiment question draft
- **AND** the published question bank SHALL remain unchanged until a teacher explicitly publishes a draft.

#### Scenario: Teacher rejects a suggestion
- **WHEN** a teacher rejects a generated suggestion draft
- **THEN** the draft SHALL be marked rejected
- **AND** no published question SHALL be changed.

### Requirement: Metadata-preserving publication
Publishing a generated suggestion SHALL preserve point-aware diagnostic metadata.

#### Scenario: Teacher publishes a generated suggestion
- **WHEN** a generated suggestion draft is published
- **THEN** the inserted generated question SHALL retain point-aware metadata including point keys, source audit, option links, coverage tags, quality flags, and review lineage
- **AND** the inserted question SHALL be stored outside the imported default bank unless an explicit promotion process later moves it.

### Requirement: Deterministic objective suggestion policy
AI suggestions SHALL remain objective and deterministic.

#### Scenario: Suggestion is validated
- **WHEN** a generated suggestion is validated
- **THEN** its type SHALL be `single_choice`, `true_false`, or `fill_blank`
- **AND** its answer SHALL be machine-gradable without AI semantic judging.
