## MODIFIED Requirements

### Requirement: Mobile learning-entry state cues
The student H5 mobile design system SHALL keep selected area state, recommendation guidance, and chapter navigation entries visually distinct by separating periodic-table selection from smart recommendation content.

#### Scenario: Selected periodic-table area is highlighted
- **WHEN** an area is selected on the periodic-table entry
- **THEN** the selected area's element cells MUST be visually emphasized without relying on heavy dark per-cell borders
- **AND** non-selected area cells MUST remain visible but visually secondary
- **AND** the selected-state treatment MUST NOT be confused with recommendation styling.

#### Scenario: Recommendation is shown below the table
- **WHEN** the learning root has a recommended profile
- **THEN** recommendation guidance MUST render in a separate smart card below the periodic table
- **AND** the periodic-table area controls MUST NOT show yellow recommendation badges
- **AND** periodic-table element cells MUST NOT show gold recommendation outlines
- **AND** the recommendation card MUST fit the phone layout without leaving the lower half of the learning root visually empty.

#### Scenario: Chapter entry cards remain tappable rows
- **WHEN** chapter cards are shown on a phone viewport
- **THEN** each card MUST read as a tappable navigation row
- **AND** recommendation styling MUST be limited to a label or similarly compact cue outside the periodic-table selector
- **AND** the label MUST NOT consume a standalone row that pushes the chapter title down
- **AND** recommendation styling MUST NOT use the same visual treatment as selected cards, active tabs, or pressed controls
- **AND** area-level chapter card titles MUST prefer the learning object label such as `碱金属和碱土金属` rather than repeating the selected area prefix such as `s区`.

#### Scenario: Learnable element symbols fit selected cells
- **WHEN** selected periodic-table cells show profile-backed element symbols
- **THEN** the symbols MUST fit inside the small cell without changing the periodic-table grid dimensions
- **AND** the symbols MUST add a learnable cue without reintroducing heavy dark selected-cell borders
- **AND** removing recommendation outlines MUST NOT make learnable symbols unreadable.

#### Scenario: Student periodic table aligns with accepted areas
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the area controls MUST show six learning areas in a two-row, three-column grid
- **AND** the six areas MUST be `氢元素`, `p区元素`, `s区元素`, `ds区元素`, `d区元素`, and `f区元素`
- **AND** the combined `氢和稀有气体` area control MUST NOT be shown
- **AND** the student entry MUST NOT expose a `通识资源` area.

#### Scenario: Student periodic table maps special elements correctly
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the H cell MUST use the hydrogen area color and route target
- **AND** noble-gas cells in group 18 MUST use the p-area color and route target
- **AND** f-block lanthanide and actinide cells MUST use the f-area color and route target
- **AND** f-block lanthanide and actinide rows MUST render as detached rows that do not occupy the group 18 display column.

#### Scenario: Student f-block layout remains phone-safe
- **WHEN** the student H5 periodic-table entry is rendered at common phone widths
- **THEN** the f-block rows MUST include La-Lu and Ac-Lr in order where cells are rendered
- **AND** the detached rows MUST preserve the left-side period label column for `镧系` and `锕系`
- **AND** profile-backed element symbols MUST be small enough that two-letter symbols fit comfortably.
