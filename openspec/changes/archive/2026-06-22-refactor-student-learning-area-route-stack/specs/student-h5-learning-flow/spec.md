## MODIFIED Requirements

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning root that hands off to a selected-area detail page, which then hands off to one current family or chapter learning detail page.

#### Scenario: Student chooses an area from the periodic table
- **WHEN** a student selects an area control or periodic-table element cell from the learning root
- **THEN** the H5 app MUST open the matching selected-area route as a second-level detail page
- **AND** the bottom navigation MUST be hidden while the selected-area detail route is visible
- **AND** the selected-area page MUST show the chapter entries for that area.

#### Scenario: Student chooses a family from the selected-area page
- **WHEN** a student selects a family, group, or chapter entry from the selected-area detail page
- **THEN** the H5 app MUST open the corresponding current family or chapter as a second-level chapter learning route
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the bottom navigation MUST remain hidden while the chapter learning detail route is visible
- **AND** returning from the chapter detail route MUST restore the selected-area route where browser history allows.

#### Scenario: Existing recommendation is used as fallback
- **WHEN** a student reaches learning without choosing a family, chapter, or area explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as recommendation guidance on the periodic-table root or selected-area page
- **AND** the H5 app MUST render that resolved profile as a current chapter detail page only when a detail route is opened
- **AND** the learning root MUST remain a periodic-table entry surface rather than a selected-area chapter list or a hidden default detail page.
