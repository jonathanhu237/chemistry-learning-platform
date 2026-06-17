## ADDED Requirements

### Requirement: Current family chapter composition
The student H5 element learning page SHALL render as the learning page for one current family or chapter selected from the periodic-table learning entry, not as a primary sibling-family browsing surface.

#### Scenario: Student opens a selected family chapter
- **WHEN** a student opens the H5 learning page for a selected profile such as `halogens-17`
- **THEN** the page MUST show the selected family or chapter as the current learning context
- **AND** it MUST NOT present sibling families as the page-level primary navigation
- **AND** it MUST provide a secondary way to return to or switch through the periodic-table learning entry.

#### Scenario: Student opens the default or recommended chapter
- **WHEN** no explicit profile is selected and the system resolves a default or recommended profile
- **THEN** the page MUST still render that profile as the current family or chapter
- **AND** it MUST NOT imply that the student is on a cross-family index page.

### Requirement: Within-family element selection
The student H5 element learning page SHALL let students select an element within the current family and view facts for that selected element without changing the current family or chapter.

#### Scenario: Student selects an element chip
- **WHEN** the current profile contains multiple elements such as `F`, `Cl`, `Br`, `I`, and `At`
- **THEN** the page MUST render touch-friendly element chips for those elements
- **AND** selecting a chip MUST update the selected-element facts area
- **AND** the selected property section and experiment-point groups MUST remain scoped to the same current family or chapter.

#### Scenario: Selected element facts are shown
- **WHEN** a student selects an element inside the current family
- **THEN** the page MUST show available element-specific facts including atomic number, electron configuration, family or group, common valence, elemental state, and oxidizing or reducing tendency where applicable
- **AND** missing optional facts MUST degrade to a clear empty or unavailable state rather than causing the page to fail.

### Requirement: Family-wide common properties
The student H5 element learning page SHALL distinguish family-wide common properties and trends from selected-element facts.

#### Scenario: Student reviews family common properties
- **WHEN** the current profile defines common properties or trend summaries
- **THEN** the page MUST show those properties as family-level learning context
- **AND** the content MUST remain visually separate from selected-element facts
- **AND** it MUST support trend formulas or summaries such as oxidizing strength, reducing strength, salt formation, precipitation, coordination, or disproportionation where defined by seed data.

#### Scenario: Common properties connect to experiment sections
- **WHEN** a family-wide property corresponds to one or more experiment-point sections
- **THEN** the page MUST provide a clear path from the property summary to the related experiment-point group
- **AND** the experiment-point group MUST remain the primary actionable learning content.

### Requirement: Experiment-point primary task area
The student H5 element learning page SHALL keep related experiment points as the primary learning task after the compact chemistry context.

#### Scenario: Student reaches related experiment points
- **WHEN** a selected family or property has related experiment points
- **THEN** the page MUST show point cards grouped by the relevant property or parent experiment
- **AND** each point card MUST include the point title, parent experiment context, concise reaction or point summary when available, media availability, and question count
- **AND** selecting a point card MUST open the point detail learning page.

#### Scenario: Context area would push points too low
- **WHEN** selected-element facts and family common properties contain more content than fits comfortably before the point list on a phone viewport
- **THEN** the page MUST prioritize compact summaries, expandable detail, or equivalent progressive disclosure
- **AND** it MUST keep the experiment-point task area discoverable without requiring excessive scrolling.

### Requirement: Optional licensed reference media
The student H5 element learning page SHALL treat public images, videos, or external reference resources as optional licensed reference media, not as protected experiment-point resources.

#### Scenario: Reference media exists
- **WHEN** the profile seed or media manifest provides reference media for a family, element, or property
- **THEN** the page MAY show the media as contextual illustration
- **AND** the resource metadata MUST include source URL, license, attribution, usage scope, and alt text
- **AND** the page MUST distinguish reference media from protected experiment videos and manually reviewed point evidence.

#### Scenario: Reference media is absent
- **WHEN** no reference media exists or a reference media source is unavailable
- **THEN** the page MUST still render the selected-element facts, family common properties, experiment-point groups, AI entry, feedback entry, and assessment handoff.
