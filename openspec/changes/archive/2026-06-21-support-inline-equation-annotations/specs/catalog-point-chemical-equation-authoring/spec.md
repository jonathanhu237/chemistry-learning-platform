## ADDED Requirements

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
