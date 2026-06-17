## ADDED Requirements

### Requirement: Mobile learning-entry state cues
The student H5 mobile design system SHALL use distinct visual cues for selected area state, recommended guidance, and chapter navigation entries on the periodic-table learning entry.

#### Scenario: Selected periodic-table area is highlighted
- **WHEN** an area is selected on the periodic-table entry
- **THEN** the selected area's element cells MUST be visually emphasized without relying on heavy dark per-cell borders
- **AND** non-selected area cells MUST remain visible but visually secondary

#### Scenario: Recommended area is visible
- **WHEN** the selected or unselected area matches the recommended profile's area
- **THEN** that area control MUST show a compact recommendation cue
- **AND** the cue MUST NOT replace or obscure the selected-state affordance
- **AND** the cue MUST NOT resize the area control's label text
- **AND** the cue MUST visually sit above the selected-area border without the border reading through the cue

#### Scenario: Chapter entry cards remain tappable rows
- **WHEN** chapter cards are shown on a phone viewport
- **THEN** each card MUST read as a tappable navigation row
- **AND** recommendation styling MUST be limited to a label or similarly compact cue
- **AND** the label MUST NOT consume a standalone row that pushes the chapter title down
- **AND** recommendation styling MUST NOT use the same visual treatment as selected cards, active tabs, or pressed controls
- **AND** area-level chapter card titles MUST prefer the learning object label such as `碱金属和碱土金属` rather than repeating the selected area prefix such as `s区`

#### Scenario: Learnable element symbols fit selected cells
- **WHEN** selected periodic-table cells show profile-backed element symbols
- **THEN** the symbols MUST fit inside the small cell without changing the periodic-table grid dimensions
- **AND** the symbols MUST add a learnable cue without reintroducing heavy dark selected-cell borders

#### Scenario: Recommended profile is visible across area, elements, and chapter card
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the recommended area control MUST show a compact recommendation cue whose secondary text describes the recommended profile, using `17族` for valid IUPAC family recommendations and a short category label such as `过渡金属` for area-level recommendations
- **AND** long recommendation cue labels such as `氢和稀有气体` and `碱金属和碱土金属` MUST be width-constrained so they do not overflow phone-sized area controls
- **AND** IUPAC group numbers MUST remain plain numbering labels and MUST NOT be used as the recommendation indicator
- **AND** element cells whose symbols belong to the recommended profile MUST show a subtle gold-border recommendation cue
- **AND** the recommended chapter card MUST NOT show a separate family-number badge when the recommendation label is already present
- **AND** when the recommended chapter title includes a family number and nickname, the chapter card title MUST preserve the complete form such as `17族（卤素）`

#### Scenario: Student periodic table aligns with resource overview
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the area controls MUST show six learning areas in a two-row, three-column grid
- **AND** the six areas MUST be `p区元素`, `s区元素`, `ds区元素`, `d区元素`, `f区元素`, and `氢和稀有气体`
- **AND** the periodic table MUST include a left-side period label column for `一` through `七`, `镧系`, and `锕系`
- **AND** the group 18 display column MUST only show the hydrogen/noble-gas learning-area cells for noble gases such as He, Ne, Ar, Kr, Xe, Rn, and Og
- **AND** f-block lanthanide and actinide rows MUST render as detached rows that do not occupy the group 18 display column
- **AND** profile-backed element symbols MUST be smaller than the previous symbol cue size so two-letter symbols fit comfortably
