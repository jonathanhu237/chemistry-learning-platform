## ADDED Requirements

### Requirement: Selected-node editor presents a title summary card
The right-side teacher catalog editor SHALL present the selected directory or point with a prominent title summary card that combines object identity, status information, and node actions without relying on tiny status tags as the primary header.

#### Scenario: Teacher selects a catalog node
- **WHEN** a teacher selects a directory, point, hybrid, or shortcut node
- **THEN** the editor MUST show the selected node title as the dominant header text
- **AND** it MUST show supporting breadcrumb or alias context without repeating the same title as a second dominant heading immediately below.

#### Scenario: Teacher reviews node status
- **WHEN** a selected node is visible in the editor
- **THEN** publication state, node kind, child count, and relevant content indicators MUST be presented as readable information blocks or equivalent summary fields
- **AND** archive, restore, publish, cancel-publish, and preview actions MUST remain available according to the existing node state rules.

### Requirement: Editor panel switching uses a clear tab-view control
The selected-node editor SHALL present mutually exclusive editing panels through a visually clear tab-view or segmented workbench switcher that remains attached to the selected-node workbench.

#### Scenario: Teacher switches between editing panels
- **WHEN** a teacher changes between content, student card, video, publication check, or advanced panels
- **THEN** the switcher MUST make the active panel visually obvious
- **AND** the active panel content MUST remain part of the same right-side workbench rather than appearing as an unrelated floating card.

#### Scenario: Teacher selects a directory-only node
- **WHEN** a directory-only node is selected
- **THEN** the editor MUST keep directory-appropriate panel availability
- **AND** it MUST NOT show point-only video or learning-content panels solely because the switcher presentation changed.

#### Scenario: Teacher selects a point-capable node
- **WHEN** a point or hybrid node is selected
- **THEN** the editor MUST keep point-appropriate panel availability
- **AND** existing save, validation, media binding, related-link, and publication behavior MUST remain unchanged.
