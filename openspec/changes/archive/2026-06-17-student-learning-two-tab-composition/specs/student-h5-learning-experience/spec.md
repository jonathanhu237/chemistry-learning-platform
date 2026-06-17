## ADDED Requirements

### Requirement: Two-tab chapter learning composition
The student H5 chapter learning page SHALL split the selected family/chapter learning experience into two quickly switchable sibling views: a facts/common-property view and an experiment-point video view.

#### Scenario: Student switches from facts to experiments
- **WHEN** a student opens a selected family/chapter page
- **THEN** the H5 app MUST show a visible two-option switcher for facts/common properties and experiment videos
- **AND** selecting the experiment option MUST show the chapter's experiment-point video learning view without changing the selected chapter or selected element

#### Scenario: Student switches from experiments to facts
- **WHEN** a student is viewing experiment-point video content for a chapter
- **THEN** selecting the facts option MUST return to the same chapter's element facts and family common properties
- **AND** the selected family/chapter MUST remain the current learning context

#### Scenario: Facts view contains theory content
- **WHEN** the facts/common-property view is active
- **THEN** the page MUST show selected-element facts, family-wide common properties or trend summaries, and optional licensed reference media when available
- **AND** it MUST NOT require the student to interpret experiment-point navigation through chemical property sections

#### Scenario: Experiments view contains task content
- **WHEN** the experiment-point video view is active
- **THEN** the page MUST show experiment-point learning content grouped by current chapter, parent experiment, and point
- **AND** it MUST keep video availability, point title, parent experiment context, and question count visible on point cards where available

### Requirement: Property sections are facts content
The student H5 learning page SHALL treat property sections as theory/common-property content rather than as the required primary grouping for experiment-point video learning.

#### Scenario: Property sections exist in seed data
- **WHEN** a learning profile includes property sections such as oxidizing property, reducing property, precipitation, coordination, or disproportionation
- **THEN** the H5 app MAY render those sections in the facts/common-property view
- **AND** it MUST NOT require the experiment-point view to group points by those property sections

#### Scenario: Experiment-point grouping is chapter based
- **WHEN** the backend builds the experiment-point payload for a selected profile
- **THEN** it MUST provide or derive groups based on the selected chapter's parent experiments and points
- **AND** it MUST avoid using property section selection as the primary experiment navigation contract

## MODIFIED Requirements

### Requirement: Real student learning page payload
The backend SHALL expose a student learning payload centered on a family or chapter profile, its display facts, and its chapter-level experiment-point video groups.

#### Scenario: Student opens learning page
- **WHEN** an authenticated student opens the H5 learning page
- **THEN** the backend MUST return a recommended, default, or explicitly selected learning profile
- **AND** the payload MUST include the profile's visible family/element facts and common-property content
- **AND** it MUST include experiment-point video groups derived from published formal experiments for the current chapter

#### Scenario: Student opens the experiment-point video view
- **WHEN** a student switches to the experiment-point video view
- **THEN** the H5 app MUST show experiment-point cards grouped by chapter parent experiment and point
- **AND** the cards MUST include experiment/point title, concise reaction or point summary when available, media availability, and question count
- **AND** the view MUST NOT depend on selecting a chemical property section such as oxidizing property or reducing property

#### Scenario: No video exists for a point
- **WHEN** a related experiment point has no published video media
- **THEN** the H5 app MUST still show the point and its learning context
- **AND** it MUST render a graceful empty video state instead of failing navigation

### Requirement: Student H5 mobile-first WebView contract
The student learning surface SHALL be treated as a phone-first H5 / mini-program WebView experience, not as a desktop admin page or a shrunken desktop layout.

#### Scenario: Student opens H5 on a phone viewport
- **WHEN** the student H5 app is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** primary learning screens MUST fit the viewport without horizontal scrolling
- **AND** headings, cards, segmented chapter switcher, bottom navigation, floating feedback entry, chat entry, and action buttons MUST remain tappable and non-overlapping
- **AND** the layout MUST prioritize the phone flow: current chapter context, A/B facts-or-experiments switching, experiment-point cards, point detail, chat, and feedback

#### Scenario: Student uses touch-only interaction
- **WHEN** a student uses the app without hover, precise mouse input, or desktop keyboard shortcuts
- **THEN** all required learning, A/B switching, chat, feedback, login, password-change, pretest-skip, and logout actions MUST be reachable through touch controls
- **AND** interactive controls SHOULD use phone-appropriate hit areas and spacing

#### Scenario: Desktop browser is used only for development preview
- **WHEN** a developer opens the student H5 app on a wide desktop browser
- **THEN** the app MAY center or constrain the phone layout for preview
- **BUT** it MUST NOT introduce desktop-only navigation, table-first layouts, hover-only affordances, or admin-console density into the student H5 experience
