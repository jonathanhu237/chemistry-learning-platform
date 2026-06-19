# student-h5-mobile-design-system Specification

## Purpose
TBD - created by archiving change student-h5-mobile-design-system. Update Purpose after archive.
## Requirements
### Requirement: Student web remains mobile-browser H5
The student frontend SHALL remain a phone-first mobile browser / WebView H5 application unless a separate future change explicitly introduces a native mini-program package.

#### Scenario: Student H5 is built for current deployment
- **WHEN** the student frontend is built or served for this change
- **THEN** it MUST continue to use the existing React + Vite H5 deployment path
- **AND** it MUST NOT require Taro, uni-app, React Native, or a native WeChat mini-program build chain

#### Scenario: Desktop preview is not a second student product
- **WHEN** a developer opens the student frontend on a wide desktop browser
- **THEN** the UI MUST behave as a phone-layout preview
- **AND** it MUST NOT introduce desktop-only navigation, hover-only controls, dense admin tables, or separate desktop student workflows

### Requirement: Mobile design-system primitives
The student frontend SHALL provide or adopt reusable mobile primitives for repeated mobile interaction patterns instead of recreating raw fixed controls and form controls per screen.

#### Scenario: Shared mobile primitives exist
- **WHEN** implementation of this change is complete
- **THEN** the student frontend MUST have a documented mobile primitive layer or equivalent shared modules for buttons, icon buttons, fields, overlay/sheet/dialog behavior, floating actions, empty states, and status feedback
- **AND** repeated student H5 screens MUST use those primitives where practical

#### Scenario: Tokens define mobile layout rules
- **WHEN** styling student H5 screens
- **THEN** common colors, spacing, radii, touch-target sizes, z-index layers, safe-area offsets, and viewport constants MUST be defined through shared tokens or a documented equivalent
- **AND** screens MUST avoid duplicating incompatible values for the same mobile behavior

### Requirement: Phone viewport compatibility
The student frontend SHALL be verified against common phone viewport sizes before student-web changes are considered complete.

#### Scenario: Required viewport sizes pass
- **WHEN** viewport QA runs for student-web
- **THEN** primary student flows MUST be checked at 360x780, 390x844, and 430x932 CSS pixels
- **AND** each checked viewport MUST avoid page-level horizontal scrolling
- **AND** primary content MUST remain readable without clipped headings, clipped actions, or broken card layout

#### Scenario: Touch target contract
- **WHEN** a required student action is rendered on a phone viewport
- **THEN** the action MUST be reachable by touch without hover or desktop keyboard shortcuts
- **AND** primary buttons, icon buttons, form controls, tabs, floating actions, and list/card actions MUST use phone-appropriate hit areas

### Requirement: Safe-area and keyboard-aware layout
The student frontend SHALL account for mobile safe areas and keyboard-sensitive controls.

#### Scenario: Safe-area protected fixed controls
- **WHEN** fixed or sticky controls are shown near viewport edges
- **THEN** they MUST account for `safe-area-inset-*` or an equivalent safe-area abstraction
- **AND** they MUST NOT be cut off by phone notches, rounded corners, or bottom browser chrome in supported mobile browsers

#### Scenario: Input overlays remain usable with keyboard
- **WHEN** a student opens a chat, feedback, login, password, or answer input on a phone viewport
- **THEN** the input and its submit action MUST remain usable when the mobile keyboard is expected to appear
- **AND** the UI MUST avoid relying on desktop-only fixed heights that hide the focused input

### Requirement: Floating overlay governance
The student frontend SHALL coordinate floating controls, bottom actions, dialogs, sheets, chat, and feedback through a shared overlay rule.

#### Scenario: Floating overlays do not overlap
- **WHEN** AI chat, feedback, dialogs, sheets, or other floating overlays are opened
- **THEN** conflicting floating entries MUST be hidden, disabled, or repositioned so they do not overlap the active overlay
- **AND** the active overlay MUST stay within the visible phone viewport width

#### Scenario: Bottom actions remain reachable
- **WHEN** a page contains a bottom fixed or floating entry and also contains an in-content primary action
- **THEN** the page MUST provide enough bottom spacing for the in-content action to scroll clear of the floating entry
- **AND** the floating entry MUST NOT block completion, submit, back, logout, chat, or feedback actions

### Requirement: Optional mobile component library governance
The student frontend SHALL treat third-party mobile UI libraries as optional providers of generic primitives, not as a replacement for the chemistry learning UI.

#### Scenario: Library adoption is evaluated first
- **WHEN** a mobile UI library such as `antd-mobile`, WeUI, or NutUI React is considered
- **THEN** the implementation MUST document the intended components, bundle impact, styling integration, and rollback path before broad adoption
- **AND** the library MUST be used only when it reduces implementation risk or improves mobile correctness

#### Scenario: Domain learning UI remains custom
- **WHEN** rendering chemistry learning content such as family profiles, element property cards, related experiment-point cards, video/point detail, AI source summaries, and chemistry-specific empty states
- **THEN** the UI MUST preserve the product-specific learning design
- **AND** it MUST NOT be replaced wholesale by generic library card or list layouts

### Requirement: Mobile QA evidence
The student frontend SHALL produce repeatable evidence that mobile-browser behavior satisfies the design-system contract.

#### Scenario: Local verification records mobile checks
- **WHEN** implementation tasks for this change are completed
- **THEN** final verification MUST record the viewport sizes tested, flows tested, commands run, and any remaining manual phone/WebView risks
- **AND** failures such as horizontal overflow, fixed-control overlap, unreachable actions, or keyboard-blocked inputs MUST be fixed or explicitly tracked before completion

### Requirement: Mobile current-chapter composition
The student H5 mobile layout SHALL present the element learning page as a current family or chapter page optimized for phone WebView reading and tapping.

#### Scenario: Student views the current chapter page on a phone
- **WHEN** the current family or chapter page is rendered at common phone widths from 360px to 430px CSS pixels
- **THEN** the layout MUST show current chapter identity, within-family element chips, selected-element facts, family common properties, property-driven experiment-point groups, floating AI or feedback entries when enabled, and completion actions without horizontal scrolling
- **AND** sibling-family browsing controls MUST NOT consume the page's primary top navigation area.

#### Scenario: Student needs to switch chapter
- **WHEN** a student wants to choose a different family or chapter
- **THEN** the page MUST expose a touch-friendly secondary navigation affordance to return to the periodic-table learning entry or switch chapter
- **AND** that affordance MUST NOT obscure the main experiment-point task area.

### Requirement: Touch-first chemistry learning controls
The student H5 mobile layout SHALL make within-family element selection and experiment-point learning controls reachable by touch without desktop-only interaction patterns.

#### Scenario: Student switches selected element
- **WHEN** element chips are displayed for the current family
- **THEN** each chip MUST use a phone-appropriate hit area
- **AND** the active element state MUST be visually clear without relying on hover.

#### Scenario: Student opens an experiment point
- **WHEN** experiment-point cards are displayed below the chemistry context
- **THEN** each card MUST be tappable without hover or precise pointer input
- **AND** floating AI or feedback controls MUST NOT block the point card, back action, completion action, or assessment entry.

### Requirement: Compact context before primary tasks
The student H5 mobile layout SHALL keep chemistry context compact enough that the experiment-point task area remains discoverable on phone viewports.

#### Scenario: Chemistry facts are lengthy
- **WHEN** selected-element facts, family common properties, trend formulas, or reference media would make the top context area long
- **THEN** the layout MUST use compact summaries, carousels, accordions, tabs, or equivalent progressive disclosure
- **AND** it MUST avoid making experiment-point learning feel secondary to an encyclopedia-style fact page.

### Requirement: Sticky segmented chapter switcher
The student frontend SHALL provide a phone-first sticky segmented switcher for local facts/experiments switching inside a selected chapter.

#### Scenario: Switcher appears on chapter page
- **WHEN** the student opens a selected family/chapter learning page
- **THEN** the page MUST render a two-option segmented switcher for facts/common properties and experiment videos
- **AND** the switcher MUST be visually associated with the current chapter rather than the global app navigation

#### Scenario: Switcher remains quickly reachable
- **WHEN** the student scrolls the chapter page on a phone viewport
- **THEN** the segmented switcher MUST remain sticky or quickly reachable according to the page layout
- **AND** it MUST NOT be placed in the bottom navigation area where it would conflict with global navigation, AI, feedback, or finish actions

#### Scenario: Switcher supports touch use
- **WHEN** a student uses touch input on a 360px to 430px CSS-pixel-wide viewport
- **THEN** each segmented option MUST have a phone-appropriate hit area, clear active state, and readable label
- **AND** switching views MUST NOT require hover, keyboard shortcuts, or undiscoverable gestures

#### Scenario: Optional swipe gesture exists
- **WHEN** an implementation supports horizontal swipe between facts and experiments
- **THEN** the visible segmented buttons MUST remain the primary discoverable switching mechanism
- **AND** swipe support MUST NOT interfere with vertical scrolling, point-card taps, video controls, AI, or feedback

### Requirement: Segmented switcher overlay governance
The segmented switcher SHALL coexist with floating entries, safe areas, and bottom actions without visual or interaction overlap.

#### Scenario: Floating entries are visible
- **WHEN** AI chat, feedback, or finish actions are available on the chapter page
- **THEN** the segmented switcher MUST remain usable without being covered by those floating entries
- **AND** floating entries MUST follow the existing overlay governance when panels are opened

#### Scenario: Safe-area and browser chrome are present
- **WHEN** the H5 app runs in a mobile browser or WebView with safe-area insets or browser chrome
- **THEN** the segmented switcher and its sticky offset MUST account for the app's safe-area and header layout
- **AND** it MUST avoid clipped labels, clipped active indicators, and horizontal overflow

#### Scenario: Mobile QA covers A/B switching
- **WHEN** mobile viewport QA runs for this change
- **THEN** it MUST cover facts-to-experiments switching, experiments-to-facts switching, element switching, experiment point list, point detail, AI entry, feedback entry, and assessment handoff
- **AND** it MUST check 360x780, 390x844, and 430x932 CSS-pixel viewports

### Requirement: Mobile learning-entry state cues
The student H5 mobile design system SHALL use distinct visual cues for selected area state, recommended guidance, and chapter navigation entries on the periodic-table learning entry.

#### Scenario: Selected periodic-table area is highlighted
- **WHEN** an area is selected on the periodic-table entry
- **THEN** the selected area's element cells MUST be visually emphasized without relying on heavy dark per-cell borders
- **AND** non-selected area cells MUST remain visible but visually secondary

#### Scenario: Recommended area is visible
- **WHEN** the selected or unselected area matches the recommended profile's area
- **THEN** that area control MUST show a compact recommendation cue
- **AND** the cue MUST NOT replace or obscure the selected-state affordance
- **AND** the cue MUST NOT resize the area control's label text
- **AND** the cue MUST visually sit above the selected-area border without the border reading through the cue

#### Scenario: Chapter entry cards remain tappable rows
- **WHEN** chapter cards are shown on a phone viewport
- **THEN** each card MUST read as a tappable navigation row
- **AND** recommendation styling MUST be limited to a label or similarly compact cue
- **AND** the label MUST NOT consume a standalone row that pushes the chapter title down
- **AND** recommendation styling MUST NOT use the same visual treatment as selected cards, active tabs, or pressed controls
- **AND** area-level chapter card titles MUST prefer the learning object label such as `碱金属和碱土金属` rather than repeating the selected area prefix such as `s区`

#### Scenario: Learnable element symbols fit selected cells
- **WHEN** selected periodic-table cells show profile-backed element symbols
- **THEN** the symbols MUST fit inside the small cell without changing the periodic-table grid dimensions
- **AND** the symbols MUST add a learnable cue without reintroducing heavy dark selected-cell borders

#### Scenario: Recommended profile is visible across area, elements, and chapter card
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the recommended area control MUST show a compact recommendation cue whose secondary text describes the recommended profile, using `17族` for valid IUPAC family recommendations and a short category label such as `过渡金属` for area-level recommendations
- **AND** long recommendation cue labels such as `氢和稀有气体` and `碱金属和碱土金属` MUST be width-constrained so they do not overflow phone-sized area controls
- **AND** IUPAC group numbers MUST remain plain numbering labels and MUST NOT be used as the recommendation indicator
- **AND** element cells whose symbols belong to the recommended profile MUST show a subtle gold-border recommendation cue
- **AND** the recommended chapter card MUST NOT show a separate family-number badge when the recommendation label is already present
- **AND** when the recommended chapter title includes a family number and nickname, the chapter card title MUST preserve the complete form such as `17族（卤素）`

#### Scenario: Student periodic table aligns with resource overview
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the area controls MUST show six learning areas in a two-row, three-column grid
- **AND** the six areas MUST be `p区元素`, `s区元素`, `ds区元素`, `d区元素`, `f区元素`, and `氢和稀有气体`
- **AND** the periodic table MUST include a left-side period label column for `一` through `七`, `镧系`, and `锕系`
- **AND** the group 18 display column MUST only show the hydrogen/noble-gas learning-area cells for noble gases such as He, Ne, Ar, Kr, Xe, Rn, and Og
- **AND** f-block lanthanide and actinide rows MUST render as detached rows that do not occupy the group 18 display column
- **AND** profile-backed element symbols MUST be smaller than the previous symbol cue size so two-letter symbols fit comfortably

### Requirement: Feedback attachment controls follow mobile overlay governance
The student H5 feedback attachment UI SHALL be implemented inside the existing mobile feedback overlay rather than as a second floating widget.

#### Scenario: Feedback panel includes screenshot controls
- **WHEN** the feedback overlay is open on a phone viewport
- **THEN** the panel MUST provide a touch-friendly screenshot add/change/remove control
- **AND** the selected filename or attachment state MUST fit within the panel without horizontal overflow
- **AND** the submit action MUST remain reachable with the mobile keyboard expected.

#### Scenario: AI and feedback overlays coexist
- **WHEN** the feedback panel is open with or without an attachment
- **THEN** AI chat entry, segmented chapter switcher, finish actions, and point cards MUST follow existing overlay governance
- **AND** no floating feedback widget from an alternate component may overlap the current panel.

#### Scenario: Attachment validation is visible to student
- **WHEN** a student chooses an unsupported screenshot file
- **THEN** the H5 app MUST show a clear mobile-readable validation message
- **AND** it MUST allow the student to choose another file without losing typed feedback content.

### Requirement: Mobile QA covers feedback attachments
Mobile viewport QA SHALL cover the feedback attachment interaction after PR2 integration.

#### Scenario: Feedback attachment QA runs
- **WHEN** mobile QA is run for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST cover opening feedback, selecting or simulating a screenshot attachment, removing an attachment, submitting feedback, and closing the panel
- **AND** it MUST verify that the feedback panel does not block the facts/experiments switcher, point detail back action, or assessment handoff.

### Requirement: Atom model preview geometry is covered by mobile QA
The student H5 mobile QA evidence SHALL cover the element detail atom model geometry on phone viewports and wide desktop previews.

#### Scenario: Phone atom model QA runs
- **WHEN** mobile viewport QA runs for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST open or navigate to an element detail route containing the atom model
- **AND** it MUST verify that the atom canvas is visible, nonblank, has reachable mode controls, and does not create horizontal overflow

#### Scenario: Wide preview atom model QA runs
- **WHEN** preview QA runs at a wide desktop viewport for the element detail route
- **THEN** it MUST verify that the atom viewer stage is not stretched by sibling fact content
- **AND** it MUST fail if the atom viewer height-to-width ratio or bounded height indicates the tall-canvas layout regression
- **AND** it MUST keep bottom navigation hidden because the element detail route is a second-level page
