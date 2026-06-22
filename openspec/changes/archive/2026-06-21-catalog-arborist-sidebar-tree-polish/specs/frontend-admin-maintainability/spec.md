## ADDED Requirements

### Requirement: Arborist catalog tree dependency is route-owned
The admin frontend SHALL keep the Arborist tree dependency and related icon dependency scoped to the lazy-loaded catalog workspace.

#### Scenario: Arborist dependency is introduced
- **WHEN** `react-arborist` is added to the admin frontend
- **THEN** imports from `react-arborist` MUST live in catalog-tree feature modules
- **AND** the production build report MUST show the resulting tree behavior code is not eagerly imported by unrelated admin shell routes.

#### Scenario: Catalog icon dependency is introduced
- **WHEN** `lucide-react` or another icon package is added for sidebar tree icons
- **THEN** imports from that package MUST be limited to catalog-tree UI modules unless another feature explicitly adopts the same dependency in its own change
- **AND** the icon usage MUST remain tree-shakeable and route-scoped.

#### Scenario: Developer changes the tree engine
- **WHEN** a developer changes Arborist configuration, node rendering, row rendering, drag preview, drop cursor, open state, lazy loading, or move mapping
- **THEN** the change MUST be localized to catalog tree modules
- **AND** selected-node content, video binding, related-link, and media upload modules MUST NOT depend on Arborist types.

### Requirement: Catalog tree visual skin has a stable feature boundary
The admin frontend SHALL implement the Dribbble/Gmail sidebar tree visual skin as feature-owned styling and render helpers.

#### Scenario: Developer changes sidebar tree visuals
- **WHEN** a developer changes chevrons, guide lines, directory icons, point experiment icons, selected state, hover state, drag affordance, trailing metadata, or row actions
- **THEN** those changes MUST live in catalog tree feature CSS or catalog tree row/render modules
- **AND** they MUST NOT introduce global Ant Design or app-shell overrides.

#### Scenario: Developer changes point iconography
- **WHEN** a developer changes the experiment point icon from flask to test tube or another chemistry icon
- **THEN** the icon mapping MUST be centralized in a catalog tree renderer or icon helper
- **AND** point rows MUST NOT fall back to generic document/file icons unless an explicit visual QA decision accepts it.

#### Scenario: Developer removes Ant Design Tree
- **WHEN** the catalog tree migrates from Ant Design Tree to Arborist
- **THEN** tests MUST no longer assert Ant Design Tree-specific wrapper classes as the source of truth
- **AND** tests MUST assert catalog behavior, feature-owned classes, and user-visible tree semantics instead.

### Requirement: Directory and point panel boundaries are test-owned
The admin frontend SHALL keep directory-only and point-only editor panel visibility covered by focused tests.

#### Scenario: Directory node editor is rendered
- **WHEN** a test renders or inspects the selected-node editor for a directory node
- **THEN** it MUST verify that video and related experiment tabs are absent
- **AND** it MUST verify point-only media and related search queries are gated off for directory nodes.

#### Scenario: Point node editor is rendered
- **WHEN** a test renders or inspects the selected-node editor for a point node
- **THEN** it MUST verify that video and related experiment tabs are present
- **AND** it MUST verify those panels remain separate from primary content and advanced diagnostics.

### Requirement: Sidebar tree visual QA is explicit
The admin frontend SHALL validate the Arborist sidebar tree against the requested visual direction with browser or screenshot QA.

#### Scenario: Sidebar tree visual QA runs
- **WHEN** visual QA is run for this change
- **THEN** screenshots MUST cover normal-width and narrow laptop-width catalog tree layouts
- **AND** screenshots MUST include expanded directory, collapsed directory, selected directory, selected point, hover or focus actions, and at least one nested point node with experiment iconography.

#### Scenario: Drag visual QA runs
- **WHEN** browser automation can simulate tree drag movement reliably
- **THEN** the QA MUST capture or assert a visible drop cursor or valid drop-target state
- **AND** if drag screenshot capture is not reliable, the limitation MUST be documented and move/drop behavior MUST still be covered by focused tests.

#### Scenario: Editor capability QA runs
- **WHEN** visual QA validates the right editor after this change
- **THEN** it MUST capture a directory selection without video or related experiment tabs
- **AND** it MUST capture a point selection with video and related experiment tabs.
