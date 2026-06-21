## ADDED Requirements

### Requirement: Rendered candidates are the adoption surface
The system SHALL present every adoptable reaction equation candidate as rendered chemistry notation rather than as ordinary suggestion text.

#### Scenario: Candidate can be adopted
- **WHEN** the system offers a parser-derived or AI-derived reaction candidate
- **THEN** the UI MUST render the candidate using canonical chemistry display fields such as `canonical_mhchem` or `canonical_display`
- **AND** the primary action MUST let the teacher adopt the rendered reaction, not copy a plain text suggestion.

#### Scenario: Raw replacement text exists
- **WHEN** a candidate has raw replacement text for input-row replacement
- **THEN** the UI MUST keep that raw text secondary to the rendered equation
- **AND** it MUST NOT make raw text the main visual object teachers choose from.

#### Scenario: Candidate cannot be normalized
- **WHEN** a parser or AI candidate cannot be normalized into a valid or warning reaction preview
- **THEN** the system MUST NOT expose that candidate as adoptable
- **AND** it MUST keep the current teacher input unchanged.

### Requirement: Parser and AI suggestions are unified per row
The system SHALL attach deterministic parser suggestions and AI suggestions to the same reaction row review context.

#### Scenario: Parser suggests a correction for a row
- **WHEN** backend preview returns a deterministic correction or balancing suggestion for a reaction row
- **THEN** that suggestion MUST appear inside the same row's candidate area
- **AND** it MUST be labeled as a system-sourced candidate.

#### Scenario: AI suggests a correction for a row
- **WHEN** AI assistance returns a candidate with a `row_order` matching an existing reaction row
- **THEN** the UI MUST attach the candidate to that row's candidate area
- **AND** it MUST NOT render the candidate in a separate full-width AI suggestion list.

#### Scenario: Parser and AI suggest the same candidate
- **WHEN** parser and AI candidates normalize to the same canonical reaction for the same row
- **THEN** the UI MUST de-duplicate the candidate
- **AND** it SHOULD show a merged source label such as `系统 + AI`.

#### Scenario: AI generates an unmatched candidate
- **WHEN** AI assistance returns a valid candidate without a matching `row_order`
- **THEN** the UI MUST show it as a compact supplemental candidate inside the reaction review panel
- **AND** adopting it MUST append it as a new multiline input row before preview runs again.

### Requirement: AI assistance is a single contextual workflow
The equation editor SHALL expose AI assistance as one contextual candidate-generation workflow instead of separate fix and generate modes.

#### Scenario: Input exists
- **WHEN** the teacher has entered one or more reaction lines
- **THEN** the primary AI action MUST be presented as `AI 校对全部`
- **AND** the AI request MUST include current input, parser preview results, and point context.

#### Scenario: Input is empty
- **WHEN** the equation editor has no reaction lines and point context is available
- **THEN** the primary AI action MUST be presented as `AI 生成候选`
- **AND** generated candidates MUST still require teacher adoption before entering the multiline input.

#### Scenario: Row needs help
- **WHEN** a reaction row is invalid, warning, or needs confirmation
- **THEN** the row MAY expose a local AI action near that row
- **AND** candidates returned from that action MUST be attached back to the same row when possible.

### Requirement: Candidate adoption is explicit and non-persistent
The system SHALL update the equation input only after explicit teacher adoption and SHALL rely on the normal save flow for persistence.

#### Scenario: Teacher adopts a row candidate
- **WHEN** the teacher selects `采用这个反应式` for a row-attached candidate
- **THEN** the UI MUST replace the corresponding multiline input row with the candidate replacement text
- **AND** it MUST request backend preview again for the updated input.

#### Scenario: Teacher adopts a supplemental candidate
- **WHEN** the teacher adopts a valid candidate without an existing row
- **THEN** the UI MUST append it as a new multiline input row
- **AND** it MUST request backend preview again for the updated input.

#### Scenario: Candidate is adopted
- **WHEN** a rendered candidate is adopted
- **THEN** the system MUST NOT automatically save, publish, index, or expose the point to students
- **AND** persistence MUST continue through the existing point content save action.

### Requirement: Review stays compact for teacher workflow
The reaction review UI SHALL prioritize rendered equations and statuses while keeping diagnostics available but secondary.

#### Scenario: Row is reviewed normally
- **WHEN** a row has rendered current understanding and no blocking error
- **THEN** the UI MUST show the rendered reaction and status prominently
- **AND** formula token lists, raw text, parser warnings, and AI rationale MUST be visually secondary or collapsible.

#### Scenario: Row has diagnostics
- **WHEN** parser warnings, errors, corrections, formula tokens, or AI rationale exist
- **THEN** the teacher MUST be able to inspect them from the row context
- **AND** those diagnostics MUST NOT push adoptable rendered candidates far away from the row.

#### Scenario: Narrow viewport
- **WHEN** the teacher uses the editor on a narrow viewport
- **THEN** row actions and candidate actions MUST remain adjacent to their row or candidate
- **AND** text or controls MUST NOT overlap.

### Requirement: Backend normalizes AI candidates before display
The backend SHALL normalize AI-assisted reaction candidates before the frontend can render them as adoptable options.

#### Scenario: AI returns candidate text
- **WHEN** the AI provider returns a candidate reaction string
- **THEN** the backend MUST run that candidate through the same reaction normalization pipeline used for preview/save
- **AND** the assist response MUST include normalized display fields for valid or warning candidates.

#### Scenario: AI returns invalid candidate text
- **WHEN** an AI candidate cannot be parsed into a usable reaction row
- **THEN** the backend MUST exclude it from adoptable candidates
- **AND** deterministic preview and manual authoring MUST remain available.

#### Scenario: AI is unavailable
- **WHEN** AI provider settings, quota, network, or runtime health prevent AI assistance
- **THEN** parser preview and deterministic row suggestions MUST continue to work
- **AND** the UI MUST avoid implying that manual equation authoring is blocked.
