## ADDED Requirements

### Requirement: Chapter switching is integrated into the catalog heading
The teacher catalog workspace SHALL allow chapter changes from the current-chapter heading without rendering a second full-width chapter dropdown that repeats the same selected chapter title.

#### Scenario: Teacher views the selected chapter context
- **WHEN** a teacher opens the catalog workspace with a chapter selected
- **THEN** the left panel MUST show the selected chapter as the primary current-chapter title
- **AND** the title area MUST expose an accessible chapter-switching affordance.

#### Scenario: Teacher changes chapter from the heading
- **WHEN** a teacher activates the current-chapter title switcher and selects a different chapter
- **THEN** the workspace MUST load the selected chapter's catalog tree
- **AND** it MUST clear any previously selected node using the existing chapter-change behavior.

#### Scenario: Teacher searches catalog nodes
- **WHEN** a teacher uses the left search input
- **THEN** the search MUST remain scoped to catalog directories, points, notes, aliases, or identities
- **AND** it MUST NOT duplicate the chapter switching control.

### Requirement: Selected-node editor renders as a cohesive workbench
The right editor SHALL present the selected-node header, tabs, and active panel as one cohesive workbench surface rather than multiple disconnected cards.

#### Scenario: Teacher selects a directory or point
- **WHEN** a teacher selects a directory or point in the catalog tree
- **THEN** the right side MUST show the node status, kind, title, breadcrumb, actions, tabs, and active editing panel within a single visually unified workbench.
- **AND** publication, archive/restore, preview, validation, save, media binding, related-link, and advanced actions MUST keep their existing behavior.

#### Scenario: Teacher switches editor tabs
- **WHEN** a teacher changes tabs inside the selected-node editor
- **THEN** the tab navigation MUST remain visually attached to the selected-node workbench
- **AND** the active tab content MUST not appear as an unrelated floating card.

### Requirement: No-selection state matches the editor workbench
The teacher catalog workspace SHALL show an intentional no-selection state that uses the same right-side workbench shell as the selected-node editor.

#### Scenario: Teacher has not selected a catalog node
- **WHEN** no directory or point is selected and the editor is not loading or errored
- **THEN** the right side MUST show a coordinated empty state inviting the teacher to select a directory or point
- **AND** the empty state MUST align with the selected editor workbench's spacing, border, radius, and background treatment.
