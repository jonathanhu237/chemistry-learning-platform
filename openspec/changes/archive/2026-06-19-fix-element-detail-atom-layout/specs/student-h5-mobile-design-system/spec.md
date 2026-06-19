## ADDED Requirements

### Requirement: Atom model preview geometry is covered by mobile QA
The student H5 mobile QA evidence SHALL cover the element detail atom model geometry on phone viewports and wide desktop previews.

#### Scenario: Phone atom model QA runs
- **WHEN** mobile viewport QA runs for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST open or navigate to an element detail route containing the atom model
- **AND** it MUST verify that the atom canvas is visible, nonblank, has reachable mode controls, and does not create horizontal overflow

#### Scenario: Wide preview atom model QA runs
- **WHEN** preview QA runs at a wide desktop viewport for the element detail route
- **THEN** it MUST verify that the atom viewer stage is not stretched by sibling fact content
- **AND** it MUST fail if the atom viewer height-to-width ratio or bounded height indicates the tall-canvas layout regression
- **AND** it MUST keep bottom navigation hidden because the element detail route is a second-level page
