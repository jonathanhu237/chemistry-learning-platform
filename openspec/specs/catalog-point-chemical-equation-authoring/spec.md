# catalog-point-chemical-equation-authoring Specification

## Purpose
TBD - created by archiving change catalog-point-ai-platform-roadmap. Update Purpose after archive.
## Requirements
### Requirement: Teachers can author multiple reaction equations
The point content editor SHALL allow teachers to enter zero, one, or many chemical reaction equations for a point whose principle mode is equation.

#### Scenario: Teacher adds reaction equations
- **WHEN** a teacher selects equation principle mode
- **THEN** the form MUST allow adding, editing, reordering, and deleting multiple reaction equation rows
- **AND** each row MUST preserve the raw teacher-entered equation text.

#### Scenario: Teacher previews an equation
- **WHEN** a teacher edits an equation row
- **THEN** the frontend SHOULD show a rendered chemistry preview when backend or local mhchem rendering can understand the value
- **AND** preview failure MUST NOT be treated as authoritative parsing failure unless the backend returns that validation result.

#### Scenario: Teacher enters only text principle
- **WHEN** a teacher selects text principle mode
- **THEN** the system MUST accept text principle content without requiring reaction equation rows
- **AND** stored equation rows MUST not be consumed as active principle equations unless equation mode is selected.

### Requirement: Frontend equation editing is assistive, not authoritative
The frontend SHALL provide helper controls for equation entry but SHALL NOT be the source of truth for chemical parsing.

#### Scenario: Teacher uses helper buttons
- **WHEN** a teacher enters an equation
- **THEN** the UI MAY provide helper buttons for plus signs, arrows, reversible arrows, states, gas, precipitate, charges, and common reagents
- **AND** these helpers MUST only modify raw input text submitted to the backend.

#### Scenario: Frontend and backend disagree
- **WHEN** frontend preview and backend normalization produce different interpretations
- **THEN** the backend result MUST be treated as authoritative for saving, validation, AI, ES, and RAG
- **AND** the UI MUST show backend warnings or errors to the teacher.

### Requirement: Backend owns reaction normalization
The backend SHALL parse, normalize, validate, and derive structured reaction data from teacher-entered equations.

#### Scenario: Equation rows are submitted
- **WHEN** point content containing reaction equations is saved or previewed
- **THEN** the backend MUST return normalized records containing raw text, canonical display text, canonical mhchem when available, plain search text, and validation status
- **AND** the backend MUST record warnings for parse uncertainty, unsupported notation, or suspected imbalance.

#### Scenario: Species are recognized
- **WHEN** the backend can recognize reactants, products, states, charges, conditions, gas markers, or precipitate markers
- **THEN** it MUST expose those derived fields for AI/ES/RAG consumers
- **AND** it MUST preserve raw teacher text so future parser improvements do not destroy authored content.

#### Scenario: Equation is invalid
- **WHEN** the backend cannot parse an equation row
- **THEN** it MUST return a teacher-readable validation message
- **AND** it MUST NOT generate misleading formulae, reaction features, or evidence-query hints from that row.

### Requirement: Equation content feeds AI, ES, and RAG through backend-derived fields
AI, ES, and RAG consumers SHALL use backend-normalized reaction fields rather than raw frontend-only interpretation.

#### Scenario: ES search document is built
- **WHEN** a published point with reaction equations is indexed
- **THEN** the search document MUST include backend-derived formulae, aliases, reaction participants, reaction features, canonical equation text, and point path context
- **AND** it MUST NOT depend on raw UI preview markup.

#### Scenario: RAG query context is built
- **WHEN** dynamic RAG query generation prepares point context
- **THEN** it MUST include the normalized reaction records alongside point title, full catalog path, phenomenon explanation, safety note, videos, and related point context
- **AND** it MUST preserve enough raw text for the LLM to recover chemistry meaning when parser confidence is low.

#### Scenario: AI answer or question generation consumes point content
- **WHEN** AI receives point context
- **THEN** it MUST receive normalized equations and derived chemistry terms in a structured context block
- **AND** it MUST not rely on student-facing prose alone for reaction information.

### Requirement: Legacy single-equation content is migrated safely
The system SHALL migrate existing single `principle_equation` values into the new multi-equation model.

#### Scenario: Existing point has a single equation
- **WHEN** migration runs for a point with a non-empty single equation value
- **THEN** the system MUST create one reaction equation row preserving that raw value
- **AND** it MUST mark the row as migrated for audit or validation reporting.

#### Scenario: Existing point has no equation
- **WHEN** migration runs for a point without equation content
- **THEN** it MUST create no fake equation rows
- **AND** text principle, phenomenon explanation, safety note, and teaching note MUST remain unchanged.

### Requirement: Backend separates equation core from inline annotation
The backend SHALL split annotated reaction rows into an equation core and row-level annotation before chemical normalization.

#### Scenario: Normalizing an annotated equation row
- **WHEN** point content containing `Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-` is previewed or saved
- **THEN** the backend MUST set the equation core to the text before `//`
- **AND** it MUST set the annotation text to the text after `//`
- **AND** canonical display, mhchem, balancing diagnostics, reactants, products, and core formulae MUST be derived only from the equation core.

#### Scenario: Annotation contains formula-like text
- **WHEN** annotation text contains formulae or species such as `NaClO` or `OH-`
- **THEN** the backend MAY extract them into annotation-specific fields such as `annotation_formulae`
- **AND** it MUST NOT merge those annotation terms into core `reactants`, `products`, or core `formulae`.

#### Scenario: Row has no inline annotation
- **WHEN** a reaction row does not contain `//`
- **THEN** the backend MUST continue using the entire row as the equation core
- **AND** annotation-specific fields MUST be empty or omitted according to the existing response style.

### Requirement: Unicode ion charge notation is normalized safely
The backend SHALL normalize common Unicode ion charge notation before deriving chemistry tokens from either equation cores or annotation text.

#### Scenario: Core equation contains Unicode charged species
- **WHEN** a teacher enters species equivalent to `Mn^2+`, `Cl-`, and `OH-` using superscript plus, superscript minus, or superscript digits
- **THEN** the backend MUST recognize them as charged species
- **AND** it MUST NOT derive misleading formula tokens such as `MN2` from the charge notation.

#### Scenario: Annotation contains Unicode charged species
- **WHEN** an inline annotation contains charged species written with Unicode charge notation
- **THEN** annotation formula extraction MUST normalize those species consistently with equation-core parsing
- **AND** any extracted annotation terms MUST remain annotation-specific.

### Requirement: Inline annotation metadata feeds consumers without participant pollution
Normalized reaction records SHALL expose annotation text and derived annotation metadata to search, AI, and RAG consumers while keeping core reaction participant semantics clean.

#### Scenario: Published point is indexed
- **WHEN** a published point contains annotated reaction rows
- **THEN** the search document MUST include annotation text, annotation formulae, and condition tags in searchable text or metadata
- **AND** the indexed reaction participants MUST still come only from backend-normalized equation cores.

#### Scenario: AI or RAG context is assembled
- **WHEN** the system builds an AI, ES, or RAG context block for a point with annotated reaction rows
- **THEN** it MUST include the annotation text attached to the corresponding reaction row
- **AND** it MUST distinguish annotation formulae and condition tags from core reactants and products.

#### Scenario: Parser cannot parse the equation core
- **WHEN** the equation core is invalid but the annotation is present
- **THEN** the backend MUST preserve the raw row and annotation text for teacher correction
- **AND** it MUST NOT generate core formulae, participants, reaction features, or evidence-query participant hints from the invalid core.

