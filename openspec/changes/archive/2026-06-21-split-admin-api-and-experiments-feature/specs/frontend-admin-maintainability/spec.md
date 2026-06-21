## ADDED Requirements

### Requirement: Admin feature imports reveal ownership
Admin feature modules SHALL import API clients and types from explicit ownership paths rather than catch-all barrels.

#### Scenario: Feature API import is reviewed
- **WHEN** a feature module needs backend data
- **THEN** it MUST import from a domain API module or shared HTTP/auth module with a specific file path
- **AND** it MUST NOT import from a global API index that obscures domain ownership.

### Requirement: Large admin feature pages split by responsibility
Admin feature pages SHALL be decomposed by stable responsibilities before new feature behavior is added to them.

#### Scenario: Large feature page is refactored
- **WHEN** a large feature page is split
- **THEN** route-level page code MUST remain a composition boundary
- **AND** data hooks, pure mappers, forms/modals, list/table display, and feature-specific helpers MUST move to explicit owner modules.

#### Scenario: New behavior is added to a large feature
- **WHEN** a new behavior is added to a feature that already has extracted owners
- **THEN** the change MUST land in the narrowest relevant owner module
- **AND** it MUST NOT re-expand the route-level page into a monolith.

### Requirement: Admin structural refactors keep lazy route boundaries
Admin frontend structural refactors SHALL preserve route-level lazy loading unless a deliberate performance change is specified.

#### Scenario: Production build is inspected
- **WHEN** admin production build and build report run after a structural refactor
- **THEN** large feature dependencies MUST remain behind lazy route chunks
- **AND** the app shell MUST NOT newly import experiments, media, question-bank, analytics, or learning-assistant feature code eagerly.
