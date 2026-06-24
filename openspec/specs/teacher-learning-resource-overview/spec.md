# teacher-learning-resource-overview Specification

## Purpose
TBD - created by archiving change redesign-periodic-learning-areas. Update Purpose after archive.
## Requirements
### Requirement: Teacher resource overview uses shared area semantics with desktop-specific rendering
The teacher resource overview SHALL use the accepted periodic learning area semantics and color tokens while preserving an independent desktop dashboard layout.

#### Scenario: Teacher overview renders shared areas
- **WHEN** a teacher opens the resource overview theory-material section
- **THEN** the area selector MUST expose shared element-learning areas using the same labels and colors as the accepted taxonomy
- **AND** it MUST keep the teacher desktop layout independent from the student phone periodic-table component
- **AND** `通识资源` MAY appear as an additional teacher-only resource bucket outside the six shared student learning areas.

#### Scenario: Teacher overview does not import student UI
- **WHEN** teacher frontend boundary checks run
- **THEN** teacher resource overview code MUST NOT import student H5 route pages, student periodic-table React components, or student CSS
- **AND** any consistency between teacher and student periodic selectors MUST be enforced by semantic tests or shared non-UI token data rather than component reuse.

### Requirement: Teacher resource periodic layout fixes f block
The teacher resource overview SHALL render f-block rows according to the student-aligned lanthanide and actinide structure while keeping desktop sizing.

#### Scenario: Lanthanide row starts at La
- **WHEN** the teacher resource overview renders the f-block lanthanide row
- **THEN** the row MUST include La through Lu in order
- **AND** the row MUST start with La rather than Ce
- **AND** it MUST preserve the detached f-block row with a visual spacer from the main table.

#### Scenario: Actinide row starts at Ac
- **WHEN** the teacher resource overview renders the f-block actinide row
- **THEN** the row MUST include Ac through Lr in order
- **AND** the row MUST start with Ac rather than Th
- **AND** f-block cells MUST not occupy or visually collide with group 18 noble-gas cells in the main table.

### Requirement: Teacher resource overview keeps chapter and area cards consistent
The teacher resource overview SHALL keep resource cards, selected area summaries, and chapter cards aligned with the accepted chapter-area taxonomy.

#### Scenario: Teacher selects p area
- **WHEN** the teacher selects the p-area selector or a p-area element cell including a noble-gas cell
- **THEN** the selected chapter list MUST include p-area chapters and any CH22 resource group needed for noble-gas content
- **AND** the displayed color and selected-state styling MUST match the p-area token.

#### Scenario: Teacher selects hydrogen area
- **WHEN** the teacher selects the hydrogen area or hydrogen cell
- **THEN** the selected chapter list MUST include CH22 as the hydrogen chapter context
- **AND** the displayed color and selected-state styling MUST match the hydrogen-area token.

#### Scenario: Teacher selects general resources
- **WHEN** the teacher selects `通识资源`
- **THEN** the overview MUST show cross-chapter/general resource groups
- **AND** this selection MUST NOT recolor or select any periodic element cells as if they belonged to `general`.

