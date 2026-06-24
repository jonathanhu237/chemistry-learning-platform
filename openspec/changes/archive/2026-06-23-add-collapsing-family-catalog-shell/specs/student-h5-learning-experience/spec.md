## ADDED Requirements

### Requirement: Family learning page prioritizes catalog browser
The student H5 learning experience SHALL treat the selected family/chapter page as a catalog browser with compact chemistry context rather than as a large element detail page.

#### Scenario: Student enters a family chapter page
- **WHEN** a student enters a family/chapter page from a selected-area entry or recommendation
- **THEN** the page MUST present selected element context in a compact header area
- **AND** the page MUST make catalog directory and point entries the dominant scroll body
- **AND** large element cards, full-width element CTAs, or long fact summaries MUST NOT push catalog entries below the practical first-screen discovery area.

#### Scenario: Element facts exceed compact space
- **WHEN** the selected element has more detail than the compact header can show
- **THEN** the page MUST keep only short focus copy, relevance copy, and compact tags in the family catalog shell
- **AND** detailed atom/fact content MUST remain available through the existing element detail route or equivalent progressive detail affordance.

#### Scenario: Catalog entries are visible after context header
- **WHEN** the page is rendered on common phone viewport widths from 360px to 430px
- **THEN** at least the catalog section heading and the start of the catalog list MUST be visible without excessive scrolling from the top expanded state
- **AND** scrolling down MUST prioritize catalog list reading over decorative element chrome.
