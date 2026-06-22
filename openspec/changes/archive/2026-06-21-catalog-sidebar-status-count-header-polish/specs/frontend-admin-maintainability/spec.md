## ADDED Requirements

### Requirement: Catalog sidebar metadata polish remains feature-local
The admin frontend SHALL keep catalog sidebar row metadata, status labels, counts, and toolbar controls inside catalog-owned feature modules and API types.

#### Scenario: Developer adds recursive point counts to the admin API contract
- **WHEN** `descendant_point_count` is added to catalog node cards
- **THEN** the TypeScript contract MUST be owned by the catalog API client module
- **AND** catalog feature test fixtures MUST include the field so missing count handling is caught by tests.

#### Scenario: Developer maps catalog node status for visible UI
- **WHEN** catalog node status is displayed in the left tree
- **THEN** status-to-label and status-to-dot mapping MUST be centralized in catalog tree mapping or row helper modules
- **AND** feature UI code MUST NOT render backend enum values directly as visible tree text.

#### Scenario: Developer changes the tree header controls
- **WHEN** root creation, refresh, expand, collapse, or more-menu controls are changed for the catalog tree
- **THEN** those controls MUST remain in catalog tree workspace/list modules
- **AND** the change MUST NOT require modifying unrelated admin shell, route registry, or global layout modules.

#### Scenario: Developer updates row styling
- **WHEN** icon size, status dot, count, warning, hover action, or selected-row styling changes
- **THEN** CSS MUST remain scoped to the catalog tree feature
- **AND** it MUST NOT introduce global Ant Design overrides for tree rows or buttons.

### Requirement: Catalog sidebar polish is covered by focused regression checks
The admin frontend SHALL include focused checks for localized tree metadata, authoritative directory counts, and non-duplicated creation controls.

#### Scenario: Unit or contract tests render tree rows
- **WHEN** tree row tests render draft, published, or archived nodes
- **THEN** tests MUST assert Chinese-facing status labels, status-dot semantics, or accessible status labels
- **AND** tests MUST fail if visible row text contains raw `published`, `draft`, or `archived`.

#### Scenario: Directory count behavior is tested
- **WHEN** tree row or mapper tests render a directory with `descendant_point_count`
- **THEN** tests MUST assert that the directory count is shown as directory trailing metadata
- **AND** tests MUST assert that point rows do not show the directory descendant count.

#### Scenario: Root creation controls are tested
- **WHEN** catalog tree workspace or list tests inspect root creation controls
- **THEN** tests MUST assert that there is a single visible root creation surface for the selected chapter
- **AND** tests MUST assert that the creation menu provides Chinese entries for directory and point creation.

#### Scenario: Browser QA captures the teacher tree
- **WHEN** the change is implementation-complete
- **THEN** browser QA MUST capture the left tree at normal admin width and narrow laptop width
- **AND** the screenshots MUST show aligned chevrons, icons, directory counts, status dots, and non-duplicated root creation controls without text overlap.

### Requirement: Backend catalog count shape is validated with admin read-model tests
The backend SHALL include focused tests for the recursive count field used by the admin catalog sidebar.

#### Scenario: Backend returns root and child cards
- **WHEN** backend tests create nested directory and point nodes
- **THEN** root and child list responses MUST include `descendant_point_count`
- **AND** directory counts MUST include point descendants across multiple levels.

#### Scenario: Backend excludes archived descendants
- **WHEN** a point descendant is archived
- **THEN** subsequent admin catalog card responses MUST exclude that archived point from normal `descendant_point_count`
- **AND** point node cards MUST still return `descendant_point_count` as `0`.

#### Scenario: Backend count updates after movement
- **WHEN** a point or directory subtree is moved between directory parents
- **THEN** subsequent admin catalog card responses MUST reflect the updated recursive point counts for old and new ancestors.
