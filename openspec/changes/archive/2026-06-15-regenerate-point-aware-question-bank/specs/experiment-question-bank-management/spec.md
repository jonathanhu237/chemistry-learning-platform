## ADDED Requirements

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
