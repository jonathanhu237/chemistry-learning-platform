## ADDED Requirements

### Requirement: Point detail body uses watch-page learning hierarchy
The student H5 point video detail page SHALL organize required learning text below the fixed point video player as a flat mobile watch-page body.

#### Scenario: Student opens a point with complete learning content
- **WHEN** a student opens a visible experiment point that has a title, catalog path, phenomenon explanation, principle content, safety note, and related experiments
- **THEN** the scrollable body below the fixed player MUST show the catalog path and full point title first
- **AND** it MUST show the phenomenon explanation before the experiment principle
- **AND** it MUST show the safety note after the principle
- **AND** it MUST show related experiment links after the required explanatory sections.

#### Scenario: Student scans the body after watching the video
- **WHEN** the point detail body is rendered on a phone viewport
- **THEN** the content MUST use compact section headings, body-copy scale text, and flat dividers between major sections
- **AND** it MUST NOT present title, phenomenon, principle, safety, or related links as nested cards inside another card
- **AND** it MUST NOT use large decorative colored panels for long explanatory text.

#### Scenario: Required content is missing
- **WHEN** a point detail payload omits phenomenon explanation, principle content, safety note, or related experiments
- **THEN** the corresponding section MUST render a controlled empty state or be omitted according to existing student rules
- **AND** the remaining required sections MUST retain their relative learning order without collapsing into an undifferentiated paragraph.

### Requirement: Point principle text is structured as readable learning notes
The student H5 point video detail page SHALL treat principle content as structured learning notes rather than as a single heavy plain-text block.

#### Scenario: Equation-mode principle contains reaction rows
- **WHEN** a point detail payload has `principle_mode` set to `equation` and includes normalized `reaction_equations`
- **THEN** the principle section MUST render each valid reaction as its own readable row
- **AND** each row MUST visually associate the rendered equation with its annotation text when annotation text exists
- **AND** the section MUST preserve the shared chemistry renderer and fallback behavior defined by existing point-equation requirements.

#### Scenario: Reaction rows include annotations
- **WHEN** one or more rendered reaction rows include supplemental annotation text
- **THEN** each annotation MUST read as explanatory body text attached to its reaction
- **AND** repeated labels such as `补充说明：` MUST NOT be the dominant visual text for every row
- **AND** annotation text MUST wrap within the phone content width without overlapping the equation, neighboring rows, or fixed controls.

#### Scenario: Text-mode principle is available
- **WHEN** a point detail payload has text-mode principle content
- **THEN** the principle section MUST render the text as readable body copy with preserved intentional line breaks
- **AND** it MUST use the same watch-page section rhythm as phenomenon and safety sections.

### Requirement: Phenomenon and safety sections remain concise and scannable
The student H5 point video detail page SHALL make phenomenon and safety content easy to scan while preserving the authored text.

#### Scenario: Phenomenon explanation is shown
- **WHEN** a point detail payload includes a phenomenon explanation
- **THEN** the phenomenon section MUST appear immediately after the title area
- **AND** it MUST present the explanation as primary body copy that answers what the student observed in the video
- **AND** it MUST NOT be visually subordinated to equation annotations or action buttons.

#### Scenario: Safety note is shown
- **WHEN** a point detail payload includes a safety note
- **THEN** the safety section MUST include a clear caution heading or icon treatment
- **AND** it MUST keep the note compact and readable
- **AND** it MUST avoid a treatment that visually overpowers the phenomenon and principle sections unless future hazard severity metadata explicitly requires stronger warning levels.

### Requirement: Related experiments render as video-style recommendations
The student H5 point video detail page SHALL present related experiment links as a YouTube-like vertical list of related experiment video rows.

#### Scenario: Related experiments are available
- **WHEN** a point detail payload includes one or more related experiments
- **THEN** each related item MUST render as a single tappable row with a 16:10 visual area, the resolved related experiment title, and a secondary relation label or generic related-experiment label
- **AND** the visual area MUST use a stable placeholder when no student-visible thumbnail is available
- **AND** selecting the row MUST preserve the existing related-point navigation behavior.

#### Scenario: Related experiment title is long
- **WHEN** a related experiment title is longer than the available row copy width
- **THEN** the title MUST wrap or clamp cleanly without overlapping the visual area, relation label, neighboring rows, bottom controls, or viewport edge.

#### Scenario: Teacher preview renders related experiments
- **WHEN** the teacher preview shell renders the student point detail page
- **THEN** related experiment rows MUST use the same student-facing title and row presentation
- **AND** disabled preview actions MUST remain disabled without exposing teacher-only related-link labels or raw configuration.

### Requirement: Point detail actions stay separate from required learning content
The student H5 point video detail page SHALL keep AI, practice, completion, and assessment handoff controls visually separate from the required learning content hierarchy.

#### Scenario: Action controls are available
- **WHEN** AI, practice, completion, or assessment handoff controls are enabled for a point detail page
- **THEN** those controls MUST appear as action affordances outside the title, phenomenon, principle, safety, and related experiment content hierarchy
- **AND** they MUST NOT interrupt the required learning section order.

#### Scenario: Fixed or floating action controls are present
- **WHEN** a completion or practice action is fixed or floating near the bottom of the viewport
- **THEN** the scrollable content MUST include enough bottom spacing for related experiment rows and final content to remain reachable
- **AND** fixed or floating actions MUST NOT permanently cover required content.

### Requirement: Point detail text layout remains mobile-safe
The student H5 point video detail text layout SHALL remain usable on common phone preview widths.

#### Scenario: Phone viewport renders long text
- **WHEN** the point detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** long titles, catalog paths, equations, annotations, phenomenon text, safety text, and related titles MUST remain within the phone content area
- **AND** the page MUST avoid horizontal body scrolling caused by the learning text layout.

#### Scenario: Fixed player and scroll body coexist
- **WHEN** the student scrolls the point detail body
- **THEN** the fixed player MUST remain at the top of the viewport
- **AND** the scroll body MUST start below the player footprint rather than sliding underneath it
- **AND** section headings and body text MUST not be hidden behind the player.
