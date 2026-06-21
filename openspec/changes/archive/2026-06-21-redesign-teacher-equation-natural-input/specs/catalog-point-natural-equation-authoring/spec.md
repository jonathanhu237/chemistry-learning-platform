## ADDED Requirements

### Requirement: Natural multiline equation input
The system SHALL support natural multiline reaction equation input for catalog point content while preserving backend-normalized structured equation records.

#### Scenario: Teacher submits multiline equation text
- **WHEN** a teacher enters multiple non-empty lines of reaction text
- **THEN** the system MUST treat each non-empty line as one reaction equation candidate
- **AND** the backend MUST preserve each original line as raw teacher input.

#### Scenario: Teacher enters loosely formatted chemistry
- **WHEN** a teacher enters reaction text with missing spaces, ASCII arrows, Unicode arrows, or equals signs
- **THEN** the backend MUST normalize reaction separators and spacing into canonical display text
- **AND** it MUST preserve the original raw line for audit and future parser improvements.

#### Scenario: Teacher enters inconsistent element casing
- **WHEN** a teacher enters likely chemical formulae with inconsistent casing such as `CL2`, `h2`, or `hcl`
- **THEN** the backend MUST attempt deterministic element-symbol canonicalization using a known periodic-table symbol set
- **AND** it MUST return a teacher-readable warning when casing was corrected or uncertain.

#### Scenario: Teacher enters common Chinese substance names
- **WHEN** a teacher enters common high-school chemistry names such as 氯气, 氢气, 氯化氢, 盐酸, 溴水, 碘, 淀粉, 氢氧化钠, or 硫酸铜
- **THEN** the backend MUST map recognized aliases to canonical formula candidates
- **AND** it MUST return the alias mapping in preview diagnostics without discarding the teacher's wording.

### Requirement: Debounced preview is authoritative but non-destructive
The teacher frontend SHALL provide near-real-time backend preview for natural equation text without silently rewriting teacher input.

#### Scenario: Teacher pauses after typing
- **WHEN** the teacher changes the multiline equation text and then stops typing briefly
- **THEN** the frontend MUST request backend preview after a debounce interval
- **AND** it MUST show the latest matching preview without requiring a primary manual check action.

#### Scenario: Preview response arrives out of order
- **WHEN** an older preview response returns after a newer input value exists
- **THEN** the frontend MUST ignore the stale response
- **AND** it MUST NOT show preview results that do not correspond to the current text area value.

#### Scenario: Preview suggests a correction
- **WHEN** the backend can confidently normalize or balance a candidate differently from the raw input
- **THEN** the preview MUST show the suggested canonical equation as a candidate
- **AND** the teacher MUST explicitly accept the suggestion before the raw input is replaced.

#### Scenario: Preview cannot understand a line
- **WHEN** the backend cannot parse a reaction candidate
- **THEN** the preview MUST show a concise Chinese explanation near that line
- **AND** it MUST NOT generate formulae, participants, reaction features, or AI/ES/RAG hints from that invalid line.

### Requirement: Backend correction and balancing suggestions
The backend SHALL return deterministic correction and balancing suggestions when it can do so safely.

#### Scenario: Simple imbalance is detected
- **WHEN** the backend recognizes reactants and products but detects an imbalance that can be balanced with simple integer coefficients
- **THEN** the backend MUST return a suggested balanced display equation
- **AND** it MUST mark the existing raw equation as needing teacher confirmation rather than invalidating the whole point.

#### Scenario: Correction is uncertain
- **WHEN** casing, aliases, species boundaries, or coefficients are ambiguous
- **THEN** the backend MUST return a warning with the uncertainty
- **AND** it MUST avoid silently changing persisted raw input.

#### Scenario: Save point content
- **WHEN** point content is saved from natural equation input
- **THEN** the frontend MUST submit raw row inputs derived from the current multiline text
- **AND** the backend MUST normalize those rows during save for AI, ES, RAG, and validation consumers.

### Requirement: Explicit AI equation assistance
The system SHALL provide AI-assisted equation drafting only as an explicit teacher action.

#### Scenario: Teacher asks AI to fix current equations
- **WHEN** a teacher invokes AI assistance for the current reaction text
- **THEN** the system MUST send relevant point context and current raw equations to the AI provider
- **AND** it MUST return draft equation candidates rather than directly saving them.

#### Scenario: Teacher asks AI to generate from point context
- **WHEN** a teacher invokes AI assistance with phenomenon explanation, safety note, title, or catalog path context
- **THEN** the system MUST produce one or more draft reaction equation candidates with short Chinese rationale
- **AND** each candidate MUST require teacher acceptance before being inserted into the editor.

#### Scenario: AI candidate is accepted
- **WHEN** a teacher accepts an AI-generated or AI-corrected candidate
- **THEN** the candidate MUST be inserted into the natural multiline input
- **AND** the backend preview/normalization MUST run before the candidate can become saved structured equation content.

#### Scenario: AI is unavailable
- **WHEN** AI provider configuration, quota, or runtime health is unavailable
- **THEN** deterministic preview and save MUST continue to work
- **AND** the UI MUST show AI assistance as unavailable without blocking manual equation authoring.
