## ADDED Requirements

### Requirement: Chapter catalog header uses two-line breadcrumb navigation
The student H5 learning flow SHALL render chapter catalog orientation as a two-line mobile breadcrumb rail where the root learning scope remains fixed above horizontally scrollable child directory breadcrumbs.

#### Scenario: Root catalog displays fixed learning scope and tools
- **WHEN** a student views the root of a family/chapter catalog
- **THEN** the catalog header MUST display the current learning scope as the first-row root chip
- **AND** it MUST display `搜索` and `更多` actions in the first-row action cluster
- **AND** it MUST NOT display `章节学习目录` or `章节学习目录下` as a visible header label
- **AND** it MUST NOT display an `上一级` action
- **AND** it MUST NOT render a child breadcrumb row when the student is already at the catalog root.

#### Scenario: Nested catalog displays child breadcrumb rail
- **WHEN** a student navigates from the catalog root into one or more directory nodes
- **THEN** the first row MUST keep the root learning scope chip separate from the child path
- **AND** the second row MUST render child directory chips from left to right in ancestor-to-current order
- **AND** the current directory MUST be the rightmost chip and MUST use selected styling
- **AND** each non-current ancestor chip MUST be tappable and navigate directly to that directory
- **AND** the root chip MUST be tappable and navigate directly to the catalog root.

#### Scenario: Breadcrumb chips preserve full text
- **WHEN** a directory name or learning scope name is longer than the available row width
- **THEN** the breadcrumb chip MUST retain its full natural text width
- **AND** the breadcrumb rail MUST handle overflow with horizontal scrolling
- **AND** the chip text MUST NOT be protected by `max-width`, ellipsis, or clipping.

#### Scenario: Search results emphasize direct parent directory
- **WHEN** a student searches chapter catalog content and receives matching directory or point results
- **THEN** each result MUST show the matching item title as primary text
- **AND** it MUST show the direct parent directory as primary path metadata
- **AND** any ancestor chain MUST be secondary, weak metadata
- **AND** the secondary ancestor chain MUST NOT include the result title as part of a long full-path string.
