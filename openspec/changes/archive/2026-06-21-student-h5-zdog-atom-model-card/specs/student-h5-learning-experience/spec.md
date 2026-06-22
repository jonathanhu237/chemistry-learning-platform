## MODIFIED Requirements

### Requirement: Within-family element selection
The student H5 element learning page SHALL let students select an element within the current family and view a model-led selected-element facts area for that element without changing the current family or chapter.

#### Scenario: Student selects an element chip
- **WHEN** the current profile contains multiple elements such as `F`, `Cl`, `Br`, `I`, and `At`
- **THEN** the page MUST render touch-friendly element chips for those elements
- **AND** selecting a chip MUST update the selected-element atom model card and compact facts area
- **AND** the selected property section and experiment-point groups MUST remain scoped to the same current family or chapter.

#### Scenario: Selected element model and facts are shown
- **WHEN** a student selects an element inside the current family
- **THEN** the page MUST show available element-specific facts including atomic number, electron configuration, family or group, common valence, elemental state, and oxidizing or reducing tendency where applicable
- **AND** the page MUST present those facts through a selected-element atom model card rather than a primary 2x3 static fact-card grid
- **AND** the card MUST preserve the selected element tile identity with atomic number, symbol, and English element name
- **AND** the card MUST show the atom visualization when electron configuration or fallback model data is available
- **AND** missing optional facts or unavailable model data MUST degrade to a clear empty or unavailable state rather than causing the page to fail.

#### Scenario: Selected element facts remain compact before tasks
- **WHEN** selected-element physical facts, teaching notes, family common properties, and property summaries would make the facts view long on a phone viewport
- **THEN** the selected-element card MUST use compact summaries, strips, chips, or progressive disclosure
- **AND** it MUST keep family common properties and experiment-point learning entry discoverable without excessive scrolling

## ADDED Requirements

### Requirement: RSC-backed selected-element physical facts
The student H5 learning experience SHALL support curated physical fact fields for selected elements using RSC Periodic Table fact boxes as the primary reference.

#### Scenario: Student sees RSC-style physical facts
- **WHEN** the selected element has curated physical facts
- **THEN** the facts view MUST be able to show relative atomic mass, group, period, block, 20°C state, density, and electron configuration in a compact mobile layout
- **AND** those fields MUST be maintained in profile or profile-adjacent seed data rather than fetched from RSC at runtime

#### Scenario: Student sees teaching facts separately
- **WHEN** the selected element also has common valence, redox tendency, or profile-specific teaching note
- **THEN** the facts view MUST keep those teaching facts visible as learning cues
- **AND** it MUST distinguish them from source-attributed physical facts where attribution is shown
