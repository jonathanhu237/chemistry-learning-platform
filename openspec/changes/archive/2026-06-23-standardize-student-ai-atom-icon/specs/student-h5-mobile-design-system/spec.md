## ADDED Requirements

### Requirement: Student icon semantics reserve Atom for AI
The student H5 mobile design system SHALL reserve the visible Atom pictogram in `apps/web-student` for student AI identity and avoid using it for unrelated search, empty-state, or content-section affordances.

#### Scenario: Element search input renders
- **WHEN** the student H5 periodic-table element search input renders
- **THEN** the input MUST use a Search pictogram or equivalent search affordance
- **AND** it MUST NOT use the Atom pictogram

#### Scenario: Non-AI chemistry content renders
- **WHEN** student H5 non-AI chemistry content sections or empty states render, including experiment principle and element/chapter empty states
- **THEN** those non-AI affordances MUST use a non-Atom pictogram such as a flask, search, clipboard, book, or other content-specific icon
- **AND** the copy, layout, and navigation behavior MUST remain unchanged

#### Scenario: Atom model content renders
- **WHEN** the student H5 atom model card or atom visualization renders as learning content
- **THEN** the model content MAY continue to use atom terminology and atom-model visuals
- **AND** this requirement only restricts the small visible Atom pictogram used as a generic UI icon outside AI identity
