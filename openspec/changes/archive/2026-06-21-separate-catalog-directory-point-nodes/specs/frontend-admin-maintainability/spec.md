## MODIFIED Requirements

### Requirement: Catalog editor feature boundary
The admin frontend SHALL implement the teacher catalog editor as a feature-owned module with clear submodule boundaries.

#### Scenario: Developer edits tree behavior
- **WHEN** a developer changes tree search, selection, expansion, drag-move, reorder, drop validation, or row actions
- **THEN** the code MUST be localized to catalog tree interaction modules
- **AND** it MUST NOT require editing an unrelated admin shell or monolithic route page.

#### Scenario: Developer edits node editor behavior
- **WHEN** a developer changes directory basics, directory card presentation, point content, point card presentation, videos, related links, publication, validation, or search preview
- **THEN** the code MUST be localized to selected-node editor modules
- **AND** shared formatting or mapping helpers MUST have explicit module ownership.

### Requirement: Large editor surfaces remain split
The admin catalog workspace SHALL avoid becoming another large all-in-one experiments page.

#### Scenario: Catalog workspace grows
- **WHEN** tree editing, drag/drop state, directory card forms, point content forms, video binding panels, related-link editors, search preview, and validation panels are implemented
- **THEN** each major surface MUST be split into route-local components, hooks, and pure mappers
- **AND** the route page MUST remain an orchestration layer rather than the owner of all behavior.

#### Scenario: Catalog editor line-count risk appears
- **WHEN** a single catalog-tree React module begins to own tree rendering, drag/drop behavior, directory forms, point forms, media bindings, and related links together
- **THEN** the implementation MUST split the module before completion
- **AND** admin maintainability validation or task review MUST call out the ownership boundary.

## ADDED Requirements

### Requirement: Catalog tree uses a mature drag interaction boundary
The admin frontend SHALL implement catalog ordering and movement through a mature draggable tree interaction rather than bespoke per-row move buttons.

#### Scenario: Drag tree dependency is selected
- **WHEN** implementation selects Ant Design Tree, React Arborist, or another mature tree/drag approach
- **THEN** the decision MUST be documented with rationale, bundle/UX trade-offs, and how it integrates with the existing Ant Design admin shell
- **AND** the dependency MUST be route-owned or otherwise avoid eager-loading unrelated admin routes.

#### Scenario: Tree movement is implemented
- **WHEN** a teacher drags a node to reorder or move it
- **THEN** the UI MUST call catalog move/reorder APIs through the catalog API client
- **AND** drag/drop code MUST remain inside catalog tree interaction modules rather than point editor modules.

### Requirement: Catalog upload UI stays outside the catalog editor
The admin frontend SHALL keep video upload UI owned by the media/video feature rather than the catalog editor.

#### Scenario: Catalog point video panel renders
- **WHEN** a point node is selected
- **THEN** the video panel MUST allow choosing, previewing, binding, unbinding, publishing, or unpublishing existing media assets
- **AND** it MUST NOT render local file input or upload-and-bind controls.

#### Scenario: Teacher needs new media
- **WHEN** no suitable existing media asset exists
- **THEN** the catalog editor MAY provide a navigation hint or link to the media upload page
- **AND** the upload workflow MUST remain owned by the media feature.

### Requirement: Catalog node type assumptions are centralized
The admin frontend SHALL centralize directory-vs-point type helpers and remove hybrid/shortcut assumptions from live components.

#### Scenario: Node kind helpers are updated
- **WHEN** catalog node kind handling changes
- **THEN** type definitions, labels, icons, action rules, form hydration, and payload builders MUST support only directory and point
- **AND** repository search MUST show no live admin catalog editor imports or UI controls for hybrid or shortcut node kinds.

#### Scenario: Stale server data appears
- **WHEN** a stale API response includes an unknown node kind
- **THEN** the frontend MUST render a controlled unsupported-node state
- **AND** it MUST NOT silently treat it as point-capable content.
