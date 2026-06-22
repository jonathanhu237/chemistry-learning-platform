## ADDED Requirements

### Requirement: Catalog tree interaction has an explicit module boundary
The admin frontend SHALL isolate catalog tree behavior from selected-node editing and route orchestration.

#### Scenario: Developer changes tree drag behavior
- **WHEN** a developer changes expansion, selection, search result focusing, drag/drop state, drop validation, reorder, move, or row action behavior
- **THEN** the change MUST be localized to catalog tree interaction modules
- **AND** it MUST NOT require editing point-content forms, media-binding panels, related-link panels, or unrelated admin shell code.

#### Scenario: Tree library adapter is introduced
- **WHEN** implementation uses React Arborist, Ant Design Tree, or another mature tree package
- **THEN** package-specific adapter code MUST be owned by catalog tree modules
- **AND** domain payload construction for move/reorder operations MUST remain in catalog API/mapping owners rather than inside visual row components.

#### Scenario: Tree visual skin changes
- **WHEN** a developer changes row icons, chevrons, guide lines, selected states, hover states, drag handles, status display, or row action placement
- **THEN** those styles and render helpers MUST remain local to the catalog tree feature
- **AND** they MUST NOT introduce global Ant Design overrides that affect unrelated tree, menu, table, or list components.

### Requirement: Selected-node editor panels are split by task
The admin frontend SHALL split the catalog selected-node editor into task-owned panels instead of one large all-concern component.

#### Scenario: Developer changes primary point content
- **WHEN** a developer changes point title mapping, teacher-only note, principle mode, equation/text principle, phenomenon explanation, or safety note UI
- **THEN** the change MUST be localized to point content editor modules and shared catalog form mappers
- **AND** it MUST NOT require editing tree rendering or media upload feature code.

#### Scenario: Developer changes directory card presentation
- **WHEN** a developer changes directory title, teacher note, student description, image, icon, accent, layout variant, or card preview UI
- **THEN** the change MUST be localized to directory editor or student-card panel modules
- **AND** point content, video binding, and related-link modules MUST remain separate.

#### Scenario: Developer changes low-frequency diagnostics
- **WHEN** a developer changes raw node id display, parent/order diagnostics, search-index preview, validation internals, or copy-debug actions
- **THEN** those changes MUST be localized to advanced or publish-check panels
- **AND** the default content panel MUST NOT become the owner of debug/search/order concerns.

### Requirement: Catalog editor dependency and bundle impact are documented
The admin frontend SHALL document any new tree/drag dependency decision and keep it scoped to the catalog workspace.

#### Scenario: New tree dependency is added
- **WHEN** implementation adds a dependency such as `react-arborist`, `react-dnd`, or another tree/drag package
- **THEN** the implementation notes or task review MUST document why it was chosen over Ant Design Tree and MUI X Tree View
- **AND** admin build output MUST be checked so unrelated routes are not eagerly loading the new tree behavior.

#### Scenario: Existing Ant Design Tree is retained
- **WHEN** implementation keeps Ant Design Tree instead of adding a new dependency
- **THEN** the implementation notes MUST document how it satisfies the required source-list visual language, drop indicator, accessibility fallback, and layout stability
- **AND** custom code added to compensate for missing behavior MUST remain feature-local.

### Requirement: Catalog editor visual regression has a stable owner
The admin frontend SHALL treat catalog tree/editor visual acceptance as part of the feature boundary.

#### Scenario: Visual checks are added
- **WHEN** Playwright, browser screenshots, DOM measurements, or manual screenshot notes are added for this change
- **THEN** the checks MUST live with admin catalog feature tests or documented admin QA artifacts
- **AND** they MUST cover both tree interaction states and selected-node editor panel states.

#### Scenario: Build or test validation runs
- **WHEN** admin frontend validation is run for this change
- **THEN** it MUST include typecheck, unit tests or focused component tests, build, boundary validation, and the catalog visual/interaction QA described by the teacher editor spec
- **AND** any accepted visual limitation MUST be documented before the change is considered complete.
