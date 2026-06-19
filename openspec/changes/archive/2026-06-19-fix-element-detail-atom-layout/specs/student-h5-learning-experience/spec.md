## ADDED Requirements

### Requirement: Element detail atom model stage remains stable
The student H5 element detail page SHALL render the selected element's atom model in a stable, readable stage whose size is independent of adjacent fact content.

#### Scenario: Student opens element detail on a phone viewport
- **WHEN** a student opens an element detail route such as `/chapter/halogens-17/element/Cl` at a common phone viewport width from 360px to 430px CSS pixels
- **THEN** the atom model stage MUST be visible, nonblank, centered within its card, and controlled by readable touch controls
- **AND** selected-element fact content MUST appear without overlapping or stretching the atom model stage

#### Scenario: Developer previews element detail on a wide browser
- **WHEN** a developer opens the same element detail route in a wide desktop browser preview
- **THEN** the page MUST preserve the phone-first H5 composition for the atom model card
- **AND** fact chips, teaching cues, or other detail content MUST NOT stretch the atom viewer canvas into an abnormally tall rectangle
- **AND** the atom model MUST remain visible near the intended visual center of the stage without requiring excessive scrolling inside the model card

#### Scenario: External console errors are present
- **WHEN** unrelated browser extension CORS errors or backend auth errors appear in the developer console while the already-rendered element detail page is visible
- **THEN** those errors MUST NOT be treated as the rendering cause unless they prevent the atom data or component from loading
- **AND** layout geometry MUST remain the primary regression signal for this atom-stage failure mode
