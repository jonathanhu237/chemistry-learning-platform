## ADDED Requirements

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
