## MODIFIED Requirements

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, transient area chapter popovers, recommended guidance, fallback selected-area route navigation, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the matching area or element cue MUST show recommendation guidance
- **AND** it MUST NOT render as a selected, active, current chapter, or inline chapter list before the student opens a detail route or area popover.

#### Scenario: Student opens a selected area from the root
- **WHEN** the student taps an area control or an element cell from the periodic-table learning root
- **THEN** the H5 app MUST render that area's chapter entries inside an anchored in-place popover
- **AND** the learning root MUST NOT navigate to a selected-area second-level route for this normal tap interaction
- **AND** the learning root MUST NOT render the selected area's chapter list as inline page content
- **AND** the selected area MUST be visually distinguishable through the popover title, focused trigger, or equivalent transient feedback without turning the root into a list page.

#### Scenario: Student dismisses a selected-area popover
- **WHEN** a selected-area chapter popover is open and the student taps outside it, presses Escape, selects another area, or navigates away
- **THEN** the popover MUST close without changing the selected chapter route
- **AND** the periodic-table root layout MUST remain at its original height and composition.

#### Scenario: Student views selected-area fallback route
- **WHEN** the selected-area route is opened directly or through existing history
- **THEN** the page MUST show the selected area identity and chapter list filtered to that area
- **AND** the recommended area or chapter cue MUST remain recommendation guidance rather than forcing a different route after the student's tap
- **AND** the bottom navigation MUST remain hidden because the selected-area route is a detail fallback route.

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry row from the selected-area popover or selected-area fallback route
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry row itself MUST be treated as a navigation row rather than a persistent selected item on the entry page.

#### Scenario: Current area shows learnable elements
- **WHEN** the periodic-table entry or selected-area fallback page has learning profiles for the relevant area
- **THEN** element cells in that area whose symbols appear in those profiles MUST show the element symbol where the table is rendered
- **AND** element cells outside the relevant area MUST NOT show profile-driven element symbols
- **AND** selected-area element cells without a matching profile symbol MAY remain unlabeled color cells.

#### Scenario: Hydrogen and noble gases are reachable learning contexts
- **WHEN** the student uses the periodic-table entry
- **THEN** hydrogen and group 18 noble gas cells MUST map to their configured learning area contexts
- **AND** the selected-area popover or fallback page MUST filter the chapter list to matching learning profiles for that context
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to the hydrogen or p learning contexts.

### Requirement: Prototype-aligned multi-level catalog flow
The student H5 app SHALL implement the prototype flow from periodic-table entry to selected area popover to chapter to catalog directories to point video/detail.

#### Scenario: Student enters from periodic table
- **WHEN** a student taps an area control or element cell from the periodic-table learning entry
- **THEN** the app MUST open that area's chapter choices in an anchored popover on the learning root
- **AND** the popover MUST make the area identity clear before showing chapter entries.

#### Scenario: Student enters chapter from selected area
- **WHEN** a student taps a chapter/family entry from the selected-area popover or fallback page
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
