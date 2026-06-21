## ADDED Requirements

### Requirement: Catalog editor presentation refinements remain feature-local
The admin frontend SHALL implement selected-node title-card and tab-view refinements inside catalog-tree owned modules and styles without introducing broad shell changes or a parallel editor behavior model.

#### Scenario: Developer changes selected-node header presentation
- **WHEN** a developer updates the catalog selected-node title card, status information blocks, or header actions
- **THEN** the change MUST remain localized to catalog editor components and catalog-tree styles
- **AND** it MUST reuse existing selected-node data, derived counts, publication state, and action handlers.

#### Scenario: Developer changes editor panel switching presentation
- **WHEN** a developer updates the selected-node panel switcher styling
- **THEN** the change MUST preserve the existing tab item filtering and active-tab behavior
- **AND** it MUST NOT require route shell, backend API, or global design-system rewrites.

#### Scenario: Developer verifies the refined editor presentation
- **WHEN** the title-card and tab-view refinements are implemented
- **THEN** focused verification MUST cover at least one selected directory or point state
- **AND** it MUST include automated typecheck, focused tests, or an equivalent catalog editor behavior check.
