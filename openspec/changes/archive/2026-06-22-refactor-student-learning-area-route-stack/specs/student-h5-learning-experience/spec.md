## MODIFIED Requirements

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, recommended guidance, selected-area route navigation, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the matching area or element cue MUST show recommendation guidance
- **AND** it MUST NOT render as a selected, active, current chapter, or inline chapter list before the student opens a detail route.

#### Scenario: Student opens a selected area
- **WHEN** the student taps an area control or an element cell from the periodic-table learning root
- **THEN** the H5 app MUST navigate to a selected-area second-level route for that area
- **AND** the learning root MUST NOT render the selected area's chapter list inline
- **AND** the selected area MUST be visually distinguishable on the root as navigation feedback or recommendation guidance without turning the root into a list page.

#### Scenario: Student views selected-area chapter list
- **WHEN** the selected-area route is open
- **THEN** the page MUST show the selected area identity and chapter list filtered to that area
- **AND** the recommended area or chapter cue MUST remain recommendation guidance rather than forcing a different route after the student's tap
- **AND** the bottom navigation MUST remain hidden because the selected-area route is a detail route.

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card from the selected-area route
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page.

#### Scenario: Current area shows learnable elements
- **WHEN** the periodic-table entry or selected-area page has learning profiles for the relevant area
- **THEN** element cells in that area whose symbols appear in those profiles MUST show the element symbol where the table is rendered
- **AND** element cells outside the relevant area MUST NOT show profile-driven element symbols
- **AND** selected-area element cells without a matching profile symbol MAY remain unlabeled color cells.

#### Scenario: Hydrogen and noble gases are a student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** hydrogen and group 18 noble gas cells MUST map to a dedicated `氢和稀有气体` learning area route
- **AND** the selected-area page MUST filter the chapter list to matching learning profiles such as the hydrogen and noble gases chapter
- **AND** the student entry MUST NOT expose a `通识资源` area
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to the `氢和稀有气体` learning area.

### Requirement: Prototype-aligned multi-level catalog flow
The student H5 app SHALL implement the prototype flow from periodic-table entry to selected area to chapter to catalog directories to point video/detail.

#### Scenario: Student enters from periodic table
- **WHEN** a student taps an area control or element cell from the periodic-table learning entry
- **THEN** the app MUST navigate to that area's standalone selected-area page
- **AND** the selected-area page MUST make the area identity clear before showing chapter entries.

#### Scenario: Student enters chapter from selected area
- **WHEN** a student taps a chapter/family entry from the selected-area page
- **THEN** the app MUST navigate to that chapter's standalone page
- **AND** the page MUST make the chapter identity clear before showing catalog entries.

#### Scenario: Student opens nested directory
- **WHEN** a student taps a directory catalog node
- **THEN** the app MUST open a second-level route for that directory
- **AND** the page MUST show child directory and point entries according to the authored order.

#### Scenario: Student opens concrete point video
- **WHEN** a student taps a point catalog node
- **THEN** the app MUST open the point video/detail page
- **AND** the page MUST show manually authored principle, phenomenon explanation, safety note, related links, and the fixed test handoff
- **AND** teacher-only remarks MUST remain hidden from this page.

#### Scenario: Directory search context leads to points
- **WHEN** a student search result is matched through directory/category text
- **THEN** the result list MUST show concrete descendant point entries
- **AND** selecting a result MUST open point detail rather than a directory-only search result page.
