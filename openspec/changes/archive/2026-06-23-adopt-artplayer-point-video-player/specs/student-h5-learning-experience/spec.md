## ADDED Requirements

### Requirement: Point detail uses edge-to-edge player header chrome
The student H5 experiment point detail page SHALL render the playable video as the page header, SHALL make that player span the full available mobile width, and SHALL avoid using the standard detail page title bar for point video pages.

#### Scenario: Student opens a point with a long title
- **WHEN** a student opens a visible experiment point whose title is longer than one normal mobile header line
- **THEN** the point detail page MUST keep the video player as the top page header
- **AND** the player MUST touch the top of the detail viewport without route padding above it
- **AND** the player MUST span the full width of the phone content area without side gutters, outer border, radius, shadow, or card background
- **AND** the page MUST render the catalog path and full point title below the player
- **AND** the title MUST be allowed to wrap without increasing or pushing down the player stage

#### Scenario: Player controls reveal return action
- **WHEN** a student taps or otherwise activates the point video player controls
- **THEN** the return action MUST appear as part of the player control chrome
- **AND** activating that return action MUST call the same source-aware route back behavior as the existing point detail back action
- **AND** the point detail page MUST NOT render a separate always-visible standard `PageBar` title above the player

#### Scenario: Page separates video header from learning content
- **WHEN** the point detail page is rendered
- **THEN** the page MUST NOT use the experiment grid-paper background behind the detail content
- **AND** the player and title area MUST NOT be presented as stacked floating cards
- **AND** the page MUST use flat sections and dividers below the video header for title, principle, explanation, safety, related links, AI handoff, and assessment handoff

#### Scenario: Point has no playable video
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the point detail page MUST keep the same edge-to-edge top video-header footprint
- **AND** it MUST show the existing graceful no-video state in that footprint
- **AND** the catalog path, title, learning content, related links, AI handoff, and assessment handoff MUST remain available

#### Scenario: Teacher previews point detail
- **WHEN** the teacher preview shell renders a student point detail page
- **THEN** the preview MUST use the same player-first layout and title-below-player composition
- **AND** preview media URLs MUST continue to resolve through preview-scoped media access
- **AND** preview-only disabled actions MUST remain disabled according to existing preview behavior

### Requirement: Point principle equations render as chemistry notation
The student H5 experiment point detail page SHALL render equation-mode experiment principles as chemical equations from the same normalized reaction-equation semantics used by the teacher catalog preview.

#### Scenario: Student opens a point with normalized reaction equations
- **WHEN** a point detail payload contains `reaction_equations` with `canonical_mhchem`
- **THEN** the experiment principle section MUST render each equation through the shared reaction-equation rendering core
- **AND** it MUST keep each row's supplemental `annotation_text` as a readable explanation below its rendered equation
- **AND** it MUST NOT rely on a single plain-text paragraph that shows the backend raw equation string as the primary student-facing equation display

#### Scenario: Student opens a point with long normalized reaction equations
- **WHEN** a normalized reaction equation is wider than the phone content width at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the student H5 equation presentation MUST use body-copy scale rather than large display-math scale
- **AND** it MUST allow the equation to wrap naturally across lines where the renderer permits
- **AND** it MUST keep horizontal scrolling as an overflow fallback only, not as the expected reading path
- **AND** it MUST NOT render KaTeX display blocks as the default student mobile equation treatment

#### Scenario: Teacher preview and student display share equation semantics
- **WHEN** the teacher catalog preview and the student H5 point detail render the same normalized reaction row
- **THEN** both surfaces MUST use the same priority order for renderable source and fallback text
- **AND** both surfaces MUST treat `canonical_mhchem` as the trusted renderable chemistry source
- **AND** both surfaces MUST preserve the same supplemental `annotation_text`
- **AND** any difference between the teacher and student output MUST be limited to the named presentation profile, not duplicated business parsing logic

#### Scenario: Student opens a legacy equation-only point
- **WHEN** a point detail payload has `principle_mode` set to `equation` but has no valid normalized `reaction_equations`
- **THEN** the experiment principle section MUST show each non-empty line of `principle_equation` through the shared fallback path
- **AND** it MUST NOT invent a chemistry parse for unconfirmed raw legacy text
- **AND** invalid or unrenderable chemistry syntax MUST fall back gracefully to the original text without breaking the page
