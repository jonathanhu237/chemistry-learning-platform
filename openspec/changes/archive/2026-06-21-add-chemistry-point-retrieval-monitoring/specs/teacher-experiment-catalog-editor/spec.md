## ADDED Requirements

### Requirement: Catalog editor diagnostic navigation uses retrieval wording
The teacher catalog editor SHALL distinguish point authoring from point retrieval diagnostics so teachers do not confuse editing content with AI/RAG/ES operational state.

#### Scenario: Teacher selects a point node
- **WHEN** a teacher selects a point node in the catalog editor
- **THEN** the primary editor MUST continue to prioritize point title, three-element content, equation authoring, publication state, and video binding
- **AND** retrieval diagnostics MUST appear as a secondary tab, panel, or action with wording such as `点位检索诊断`.

#### Scenario: Teacher selects a directory node
- **WHEN** a teacher selects a directory node
- **THEN** the editor MUST focus on directory metadata, recursive point counts, movement, visibility, and child organization
- **AND** it MUST NOT present directory nodes as if they had the same point-level ES/RAG content diagnostics as experiment points.

#### Scenario: Teacher opens advanced diagnostics
- **WHEN** a teacher opens point diagnostics from the editor
- **THEN** the diagnostics surface MUST show ES/RAG/AI/search-preview state for the selected placement
- **AND** it MUST be clearly separated from default authoring controls so operational debug data does not crowd routine editing.

### Requirement: Catalog tree semantics are visible to retrieval diagnostics
The catalog editor SHALL expose enough selected-node context for diagnostics to explain placement identity, canonical identity, and directory-derived recall.

#### Scenario: Same canonical point appears twice
- **WHEN** the editor displays two placements of the same canonical point under different directories
- **THEN** each selected placement MUST expose its placement node id and catalog path to diagnostics
- **AND** diagnostics MUST also expose the shared canonical point id for grouping and smart-pointer explanation.

#### Scenario: Directory context affects point search
- **WHEN** a teacher changes or inspects a directory that contributes to descendant point paths
- **THEN** diagnostics MUST be able to explain that descendant point placement documents may need reindexing
- **AND** the editor MUST avoid implying that a directory title change is purely cosmetic for search.

#### Scenario: Point publication changes from editor
- **WHEN** a teacher publishes, unpublishes, hides, or archives a point from the catalog editor
- **THEN** the editor MUST surface index/evidence state transitions through diagnostics or status badges
- **AND** it MUST preserve the existing save-vs-publish boundary for student search visibility.
