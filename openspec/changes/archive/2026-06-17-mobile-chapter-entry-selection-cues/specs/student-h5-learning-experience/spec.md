## ADDED Requirements

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, recommended guidance, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the matching chapter entry MUST show a recommendation label
- **AND** it MUST NOT render as a selected, active, or current chapter before the student opens it

#### Scenario: Student changes selected area
- **WHEN** the student taps an area control or an element cell from a different area
- **THEN** the chapter list MUST filter to that selected area
- **AND** the selected area MUST be visually distinguishable from other areas
- **AND** the recommended area cue MUST remain recommendation guidance rather than forcing the selected area back after the student's tap

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page

#### Scenario: Current area shows learnable elements
- **WHEN** the periodic-table entry has learning profiles for the selected area
- **THEN** element cells in the selected area whose symbols appear in those profiles MUST show the element symbol
- **AND** element cells outside the selected area MUST NOT show profile-driven element symbols
- **AND** selected-area element cells without a matching profile symbol MAY remain unlabeled color cells

#### Scenario: Hydrogen and noble gases are a student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** hydrogen and group 18 noble gas cells MUST map to a dedicated `氢和稀有气体` learning area
- **AND** the area MUST filter the chapter list to matching learning profiles such as the hydrogen and noble gases chapter
- **AND** the student entry MUST NOT expose a `通识资源` area
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to the `氢和稀有气体` learning area
