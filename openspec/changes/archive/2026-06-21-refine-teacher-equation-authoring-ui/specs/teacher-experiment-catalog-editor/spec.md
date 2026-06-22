## ADDED Requirements

### Requirement: Teacher-friendly equation authoring surface
The teacher catalog editor SHALL present reaction equation authoring as a Chinese, card-based input and preview workflow for point-capable nodes whose principle mode is equation.

#### Scenario: Teacher opens equation principle mode
- **WHEN** a teacher selects equation principle mode for a point-capable catalog node
- **THEN** the editor MUST show an experiment reaction equation area in Chinese
- **AND** the main authoring surface MUST be organized around individual equation cards rather than a permanent row of global snippet buttons.

#### Scenario: Teacher edits a reaction equation row
- **WHEN** a teacher types into an equation card
- **THEN** the editor MUST preserve the raw teacher-entered text for backend preview and save
- **AND** the frontend MUST NOT derive authoritative AI, ES, or RAG fields from its local preview.

#### Scenario: Teacher inserts common chemistry notation
- **WHEN** a teacher opens common chemistry controls
- **THEN** the editor MUST present grouped helpers for reaction symbols, physical states, ions, and common reagents
- **AND** choosing a helper MUST insert text into the currently targeted equation input without changing backend normalization rules.

#### Scenario: Teacher checks equations
- **WHEN** a teacher runs equation checking
- **THEN** the primary visible action MUST use teacher-facing Chinese wording such as “检查”
- **AND** it MUST NOT expose backend implementation wording such as “后端预览” as the main workflow label.

#### Scenario: Backend preview returns normalized equations
- **WHEN** the backend preview or save response returns normalized equation records
- **THEN** each matching equation card MUST show inline normalized display text, validation status, and teacher-readable warnings near the raw input
- **AND** the UI MUST treat the backend response as authoritative over any frontend formatting preview.

#### Scenario: Teacher manages multiple equations
- **WHEN** a point contains multiple reaction equations
- **THEN** the editor MUST support adding, deleting, and reordering equation cards
- **AND** these controls MUST remain compact enough that the equation content remains the visual focus.

#### Scenario: Advanced structure drawing is not the default
- **WHEN** the teacher authors ordinary high-school experiment reaction equations
- **THEN** the default editor MUST remain text-plus-preview
- **AND** it MUST NOT require loading a full chemical structure drawing tool such as Ketcher, MarvinJS, ChemDoodle, or PubChem Sketcher.
