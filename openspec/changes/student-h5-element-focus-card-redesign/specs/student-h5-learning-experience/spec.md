## ADDED Requirements

### Requirement: Experiment-focused selected element card
The student H5 chapter learning page SHALL present the selected element as a compact experiment-learning card rather than as a generated sentence or full detail summary.

#### Scenario: Selected element card renders curated focus copy
- **WHEN** a student selects an element within the current family or chapter
- **THEN** the compact selected-element card MUST keep the periodic-table element tile visible with atomic number, symbol, and English element label
- **AND** it MUST show a curated focus-property line for the selected element
- **AND** it MUST show a curated experiment-relevance line explaining why that element matters to the current chapter's experiments or observation tasks
- **AND** it MUST show compact supporting tags such as group, period/block, state, or common valence where available

#### Scenario: Selected element card avoids generated prose
- **WHEN** the H5 app renders the compact selected-element card
- **THEN** it MUST NOT generate the primary title or body by concatenating the selected element name with the family name
- **AND** it MUST NOT use family-wide trend text as the selected element card body
- **AND** it MUST NOT prefix a family trend sentence with the selected element name to make it appear element-specific

#### Scenario: Detailed facts remain outside compact card
- **WHEN** the selected element has detailed facts such as electron configuration, atomic mass, density, full redox tendency, reference URL, or longer notes
- **THEN** those details MUST remain available in the facts view, element detail route, or equivalent detail area
- **AND** the compact selected-element card MUST only surface the short focus property, experiment relevance, and compact tags

#### Scenario: Element switching updates compact card
- **WHEN** the student taps another element chip in the same family or chapter
- **THEN** the compact card MUST update its tile, focus property, experiment relevance, and tags for the newly selected element
- **AND** the current family or chapter context, facts/experiments switcher state, and experiment-point groups MUST remain scoped to the same learning profile

### Requirement: Explicit element focus card seed copy
The platform SHALL store selected-element card copy as explicit maintained student learning seed data instead of deriving the compact card's teaching copy from RAG chunks, family trend summaries, or front-end string composition.

#### Scenario: Learning profile seed includes card copy
- **WHEN** production resource validation or test validation runs for enabled student learning profiles
- **THEN** each enabled element MUST include card-level focus copy, experiment relevance copy, and compact card tags before the profile is treated as complete for the redesigned card experience
- **AND** missing card-level copy MUST be reported as validation feedback before the profile is considered complete for the redesigned card experience

#### Scenario: Backend exposes card copy
- **WHEN** the student learning API builds the H5 learning payload for a selected family or chapter
- **THEN** each element badge MUST expose the card-level focus property, experiment relevance, and card tags when seed data provides them
- **AND** existing detailed element facts MUST remain available for the facts view and element detail experience

#### Scenario: Card copy is temporarily missing
- **WHEN** an element is missing redesigned card copy during migration
- **THEN** the H5 app MUST render a graceful compact fallback using stable factual tags where available
- **AND** the fallback MUST NOT recreate the old generated `<element>在<family>中的位置` pattern or use a family trend sentence as the element card body
