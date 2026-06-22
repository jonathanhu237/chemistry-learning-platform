## ADDED Requirements

### Requirement: Student equation principles display inline annotations
The student H5 experiment point detail SHALL display inline annotation text attached to its reaction equation when a published point uses annotated equation-mode principles.

#### Scenario: Student opens a point with annotated reaction principles
- **WHEN** a student opens a published experiment point whose normalized reaction rows include annotation text
- **THEN** the point detail MUST show the rendered equation and its annotation together
- **AND** the annotation MUST be readable as explanatory text for that reaction rather than as another equation.

#### Scenario: Point has multiple annotated reactions
- **WHEN** a point contains multiple reaction rows and some rows have inline annotations
- **THEN** each annotation MUST appear only with its corresponding reaction row
- **AND** unannotated reaction rows MUST continue to render without annotation chrome.

#### Scenario: Student-facing payload is assembled
- **WHEN** the backend builds the student point detail payload for equation-mode principles
- **THEN** it MUST include annotation text for each annotated reaction row
- **AND** it MUST keep annotation formulae and condition tags separate from core reactants and products in any structured fields exposed to the frontend.
