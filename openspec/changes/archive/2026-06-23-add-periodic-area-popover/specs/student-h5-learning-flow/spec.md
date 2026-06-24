## MODIFIED Requirements

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning root that opens an anchored selected-area chapter popover in place, then hands off directly to one current family or chapter learning detail page.

#### Scenario: Student chooses an area from the periodic table
- **WHEN** a student selects an area control or periodic-table element cell from the learning root
- **THEN** the H5 app MUST open the matching selected-area chapter list as an anchored popover on the learning root
- **AND** the learning root MUST remain the active root route
- **AND** the bottom navigation MUST remain governed by root-route behavior while the popover is open
- **AND** the app MUST NOT navigate to the selected-area detail route for this normal tap interaction.

#### Scenario: Student chooses a family from the anchored area popover
- **WHEN** a student selects a family, group, or chapter entry from the anchored area popover
- **THEN** the H5 app MUST close the popover and open the corresponding current family or chapter as a second-level chapter learning route
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the bottom navigation MUST remain hidden while the chapter learning detail route is visible
- **AND** returning from the chapter detail route MUST restore the learning root where browser history allows.

#### Scenario: Existing selected-area route is used as fallback
- **WHEN** a student reaches a valid selected-area detail URL directly or through preserved browser history
- **THEN** the H5 app MUST render the selected-area page as a compatibility fallback
- **AND** the selected-area page MUST show the matching chapter entries
- **AND** choosing a chapter from that fallback page MUST still open the corresponding current family or chapter route.

#### Scenario: Existing recommendation is used as guidance
- **WHEN** a student reaches learning without choosing a family, chapter, or area explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as recommendation guidance on the periodic-table root
- **AND** the H5 app MUST render that resolved profile as a current chapter detail page only when a detail route is opened
- **AND** the learning root MUST remain a periodic-table entry surface rather than a selected-area chapter list or a hidden default detail page.
