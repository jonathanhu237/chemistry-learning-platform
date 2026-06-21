## ADDED Requirements

### Requirement: Sidebar tree row metadata is localized and scan-friendly
The teacher catalog tree SHALL render row metadata with Chinese-facing labels, compact status dots, and sidebar-style trailing numbers instead of raw backend enum text.

#### Scenario: Directory row renders in the sidebar tree
- **WHEN** a directory row is visible in the teacher catalog tree
- **THEN** the row MUST show a folder icon sized clearly for the sidebar row density
- **AND** it MUST show the directory title and directory kind without overlapping trailing metadata
- **AND** it MUST render the directory status as a compact colored status dot with a Chinese accessible label
- **AND** it MUST NOT render raw backend status values such as `published`, `draft`, or `archived` as visible row text.

#### Scenario: Point row renders in the sidebar tree
- **WHEN** a point row is visible in the teacher catalog tree
- **THEN** the row MUST show an experiment-specific icon such as a flask or test tube, sized clearly for the sidebar row density
- **AND** it MUST preserve the same title alignment as directory rows by reserving disclosure space
- **AND** it MUST render point status with the same compact Chinese status-dot system
- **AND** it MUST NOT use a generic document icon as the primary point identity.

#### Scenario: Selected row needs explicit status clarity
- **WHEN** a directory or point row is selected, hovered, focused, or inspected by assistive technology
- **THEN** the UI MUST expose the status using Chinese-facing labels such as `已发布`, `草稿`, or `已归档`
- **AND** it MUST NOT expose raw backend status enum text in the visible left tree.

#### Scenario: Validation and publication status both apply
- **WHEN** a node has validation warnings or errors
- **THEN** the row MUST keep validation warning affordances visually distinct from the publication status dot
- **AND** the warning state MUST NOT replace or redefine the node's publication status.

### Requirement: Directory rows expose authoritative recursive point counts
The teacher catalog tree SHALL show directory point counts from a backend-provided recursive node-card field rather than from the currently loaded client subtree.

#### Scenario: Teacher views a directory with descendant points
- **WHEN** a directory has point descendants at any depth under the same chapter
- **THEN** the directory row MUST be able to show the total count of non-archived descendant point nodes as trailing sidebar metadata
- **AND** the count MUST remain correct even when some descendant directories are not currently expanded or loaded in the client.

#### Scenario: Teacher views an empty directory
- **WHEN** a directory has zero non-archived descendant point nodes
- **THEN** the row MUST avoid presenting a misleading loaded-child count as a total point count
- **AND** the UI MUST either hide the zero count or show `0` as an authoritative backend-provided zero count.

#### Scenario: Teacher views a point row
- **WHEN** a point row is visible
- **THEN** the row MUST NOT show the directory descendant point count as if the point had children
- **AND** point-specific trailing metadata MUST be limited to point-owned information such as video binding completion where applicable.

#### Scenario: Tree structure changes
- **WHEN** a teacher creates, moves, archives, restores, or deletes a point under a directory subtree
- **THEN** subsequent catalog root, child, detail, or search fetches MUST return updated recursive point counts for affected directory cards.

### Requirement: Catalog node cards include recursive directory point count
The teacher catalog read model SHALL expose a stable recursive point-count field on catalog node cards used by the admin tree.

#### Scenario: Root directory cards are loaded
- **WHEN** the admin frontend loads root catalog nodes for a chapter
- **THEN** every returned `CatalogNodeCard` MUST include `descendant_point_count` as a number
- **AND** directory values MUST count non-archived descendant point nodes recursively.

#### Scenario: Child directory cards are loaded lazily
- **WHEN** the admin frontend loads children for a directory
- **THEN** every returned child `CatalogNodeCard` MUST include `descendant_point_count`
- **AND** the count MUST NOT depend on which sibling or descendant nodes the client has already loaded.

#### Scenario: Point cards are loaded
- **WHEN** a `CatalogNodeCard` represents a point node
- **THEN** `descendant_point_count` MUST be `0`
- **AND** consumers MUST use point-owned media fields for video completion metadata.

#### Scenario: Selected node detail is loaded
- **WHEN** the admin frontend loads selected node detail
- **THEN** the detail payload's node card and child cards MUST include the same `descendant_point_count` contract as tree list payloads.

### Requirement: Tree header has one root creation surface
The teacher catalog tree SHALL expose a single compact chapter-root creation surface in the left tree toolbar.

#### Scenario: Teacher views the selected chapter heading
- **WHEN** a teacher views the left catalog panel for a selected chapter
- **THEN** the chapter heading MUST show chapter context such as `当前章节` and the chapter title
- **AND** it MUST NOT also show duplicate visible `目录` and `点位` root creation buttons.

#### Scenario: Teacher creates a root node
- **WHEN** a teacher wants to create a top-level node under the selected chapter
- **THEN** the tree toolbar MUST provide one compact add action
- **AND** that add action MUST offer Chinese menu items for creating a directory and creating a point.

#### Scenario: Secondary tree actions exist
- **WHEN** refresh, expand-all, collapse-all, or similar secondary tree commands are available
- **THEN** they MUST live in a subtle toolbar icon or more menu
- **AND** they MUST NOT create another competing root-add surface.

#### Scenario: Root creation wording is visible
- **WHEN** root creation controls are visible
- **THEN** the UI MUST use teacher-facing Chinese wording such as `新建目录`, `新建点位`, or `添加到本章`
- **AND** it MUST NOT expose implementation wording such as `root node` as primary visible text.

### Requirement: Sidebar row layout remains stable under actions and counts
The teacher catalog tree SHALL keep row alignment stable when counts, status dots, warnings, and contextual actions appear.

#### Scenario: Teacher hovers a directory row
- **WHEN** a directory row is hovered, focused, or selected
- **THEN** child-add and more-actions controls MUST be available without being permanently visible on every unselected row
- **AND** their appearance MUST NOT shift the chevron, icon, title, status dot, or count positions.

#### Scenario: Teacher hovers a point row
- **WHEN** a point row is hovered, focused, or selected
- **THEN** point-appropriate more-actions controls MUST be available without being permanently visible on every unselected row
- **AND** child-add controls MUST NOT appear for point rows.

#### Scenario: Row title is long
- **WHEN** a directory or point title is longer than the available row title area
- **THEN** the title MUST truncate or otherwise fit without overlapping the trailing count, status dot, warning icon, or actions.
