# catalog-point-natural-equation-authoring Specification

## Purpose
TBD - created by archiving change redesign-teacher-equation-natural-input. Update Purpose after archive.
## Requirements
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

### Requirement: Natural equation lines support explicit inline annotations
The system SHALL support `//` as a reserved inline annotation delimiter in natural multiline reaction equation input while preserving the existing one-line-per-equation contract.

#### Scenario: Teacher enters one annotated reaction line
- **WHEN** a teacher enters `Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-`
- **THEN** the system MUST treat the entire non-empty line as one reaction equation row
- **AND** it MUST parse only the text before `//` as the reaction equation candidate
- **AND** it MUST preserve the text after `//` as the row's inline annotation.

#### Scenario: Teacher enters multiple annotated and unannotated lines
- **WHEN** a teacher enters multiple non-empty reaction lines and one or more lines contain `//`
- **THEN** the system MUST keep the existing input order and create one reaction row per non-empty line
- **AND** each annotation MUST remain attached only to its own source line.

#### Scenario: Teacher enters an unannotated reaction line
- **WHEN** a teacher enters a reaction line without `//`
- **THEN** the system MUST keep the existing natural equation preview and save behavior for that row.

### Requirement: Annotation syntax is explicit rather than inferred from parentheses
The system SHALL NOT infer reaction annotations from parentheses alone because parentheses are valid chemistry notation and common prose punctuation.

#### Scenario: Equation core contains parentheses
- **WHEN** a teacher enters `Al(OH)3 + 3HCl -> AlCl3 + 3H2O`
- **THEN** the system MUST parse the parentheses as part of the equation core
- **AND** it MUST NOT create an inline annotation.

#### Scenario: Teacher wants a condition or note
- **WHEN** a teacher or AI assistant needs to attach condition text or explanatory prose to an equation row
- **THEN** the text MUST be placed after `//` on the same line
- **AND** the system MUST NOT require an additional line for that note.

### Requirement: AI equation assistance uses inline annotation syntax
The AI equation assistance workflow SHALL emit and preserve `//` inline annotations when generating or repairing natural equation text.

#### Scenario: AI converts prose notes into an annotation suffix
- **WHEN** AI assistance generates an equation with a condition, excess reagent note, medium note, or reagent-source explanation
- **THEN** it MUST keep the reaction as one line
- **AND** it SHOULD place the explanatory text after `//` instead of creating a second line.

#### Scenario: AI repairs only the equation core
- **WHEN** a saved or edited equation line already has a `//` annotation suffix and AI assistance suggests a core equation correction
- **THEN** accepting the correction MUST preserve the existing annotation suffix unless the teacher explicitly accepts annotation edits.

### Requirement: Principle mode switching is autosave-safe
The point content editor SHALL keep experiment-principle mode switching stable while autosave and detail refreshes are in flight.

#### Scenario: Teacher switches to an empty equation mode
- **WHEN** the teacher switches `实验原理` from text mode to `化学方程式` mode and the new equation input is empty
- **THEN** the editor MUST keep `化学方程式` selected immediately
- **AND** autosave MUST be allowed to persist the selected mode as draft content
- **AND** a stale detail refresh MUST NOT revert the editor back to text mode.

#### Scenario: Teacher switches to an empty text mode
- **WHEN** the teacher switches `实验原理` from equation mode to `文字描述` mode and the new text input is empty
- **THEN** the editor MUST keep `文字描述` selected immediately
- **AND** autosave MUST be allowed to persist the selected mode as draft content
- **AND** node status MUST report missing experiment principle rather than reverting the selected mode.

#### Scenario: Existing mode has content
- **WHEN** the teacher attempts to switch away from a non-empty principle mode
- **THEN** the editor MUST ask for explicit confirmation before discarding the inactive-mode content
- **AND** cancelling the confirmation MUST preserve the current mode and content.

#### Scenario: Autosave response arrives out of order
- **WHEN** an older autosave response or invalidation-triggered detail payload returns after a newer principle mode switch
- **THEN** the editor MUST ignore or defer the stale mode value for the active node
- **AND** it MUST not overwrite the teacher's current selected mode.

#### Scenario: Teacher selects a different node
- **WHEN** the selected catalog node changes
- **THEN** pending principle-mode guards MUST reset for the previous node
- **AND** the newly selected node MUST hydrate from its own saved detail normally.

### Requirement: Principle mode remains an input mode under experiment principle
Equation and text principle authoring SHALL remain two input modes for the same required experiment-principle field.

#### Scenario: Equation mode saves
- **WHEN** the teacher saves point content in `化学方程式` mode
- **THEN** the save payload MUST keep equation rows as the active experiment-principle source
- **AND** text-mode principle prose MUST not be required for that save.

#### Scenario: Text mode saves
- **WHEN** the teacher saves point content in `文字描述` mode
- **THEN** the save payload MUST keep principle prose as the active experiment-principle source
- **AND** equation rows MUST not be required for that save.

#### Scenario: Active principle source is empty
- **WHEN** the active principle source for the selected mode is empty
- **THEN** draft save MUST remain possible
- **AND** publication readiness MUST report `缺少实验原理`.

