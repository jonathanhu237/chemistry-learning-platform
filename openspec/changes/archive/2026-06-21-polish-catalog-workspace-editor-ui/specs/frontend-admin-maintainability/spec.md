## ADDED Requirements

### Requirement: Catalog workspace visual polish stays feature-local
The admin frontend SHALL keep catalog workspace visual polish inside catalog-tree owned modules and styles.

#### Scenario: Developer polishes catalog chapter switching
- **WHEN** a developer changes the chapter selector presentation for the catalog workspace
- **THEN** the code MUST remain localized to catalog workspace components and catalog-tree styles
- **AND** it MUST reuse existing chapter data, state, and query behavior rather than introducing a parallel chapter-selection model.

#### Scenario: Developer polishes the selected-node editor shell
- **WHEN** a developer changes the selected-node editor header, tabs, empty state, or content surface
- **THEN** the code MUST remain localized to selected-node editor modules and catalog-tree styles
- **AND** it MUST NOT require broad admin shell changes or a new global design-system abstraction.

#### Scenario: Developer verifies catalog polish
- **WHEN** catalog workspace polish is implemented
- **THEN** focused verification MUST cover selected-node and no-selection states
- **AND** it MUST include at least one check that existing catalog editor behavior still works or typechecks.
