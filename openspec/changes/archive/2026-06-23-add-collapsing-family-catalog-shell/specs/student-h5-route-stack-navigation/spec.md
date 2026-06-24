## ADDED Requirements

### Requirement: Catalog directory route can render with family shell
The student H5 route stack SHALL allow catalog directory routes to render inside the family catalog shell when selected profile context is available.

#### Scenario: Directory route has profile context
- **WHEN** a catalog directory route is opened with a valid `profileId` search parameter
- **THEN** the route MUST resolve the selected learning profile using durable route/search data
- **AND** the page MUST render the family catalog shell with the directory body
- **AND** the bottom navigation MUST remain hidden because the route is still a non-tab detail route.

#### Scenario: Directory route lacks profile context
- **WHEN** a catalog directory route is opened without selected profile context
- **THEN** the route MUST continue to render a durable standalone directory page or controlled unavailable state
- **AND** it MUST NOT depend on prior in-memory chapter state.

#### Scenario: Directory navigation includes selected element context
- **WHEN** a directory is opened from a family catalog shell after the student selected an element
- **THEN** the navigation SHOULD include the selected element symbol in route search state
- **AND** the receiving shell SHOULD restore that selected element when it belongs to the selected profile.
