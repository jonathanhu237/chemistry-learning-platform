## ADDED Requirements

### Requirement: Catalog content editor layout refinements remain feature-local
The admin frontend SHALL keep point content editor layout refinements inside catalog-tree owned modules and styles without changing backend contracts or creating a parallel editor model.

#### Scenario: Developer changes point content form layout
- **WHEN** a developer updates teacher-only note, experiment principle, reaction-equation presentation, phenomenon explanation, or safety note layout
- **THEN** the implementation MUST remain localized to catalog-tree selected-node editor components, catalog content mappers where needed, and catalog-tree feature CSS
- **AND** it MUST NOT require broad admin shell changes, global Ant Design overrides, backend API changes, or new dependencies.

#### Scenario: Developer compacts reaction equation presentation
- **WHEN** a developer changes the visible layout of the reaction-equation input, preview, AI action, or suggestion list
- **THEN** the implementation MUST preserve existing preview, AI assistance, suggestion application, hydration, autosave, and save payload behavior
- **AND** verification MUST include focused catalog editor checks such as contract tests, typecheck, or equivalent browser QA.
