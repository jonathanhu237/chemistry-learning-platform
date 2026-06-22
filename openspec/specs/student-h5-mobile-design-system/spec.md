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
The student frontend SHALL coordinate bottom navigation, fixed controls, dialogs, sheets, and any remaining overlays through a shared mobile layering rule.

#### Scenario: Fixed and overlay controls do not overlap
- **WHEN** dialogs, sheets, chat pages, feedback forms, assessment actions, or other fixed controls are shown
- **THEN** conflicting controls MUST be hidden, disabled, or repositioned so they do not overlap the active interaction
- **AND** the active interaction MUST stay within the visible phone viewport width.

#### Scenario: Bottom actions remain reachable
- **WHEN** a page contains the bottom tab bar and also contains an in-content primary action
- **THEN** the page MUST provide enough bottom spacing for the in-content action to scroll clear of the tab bar
- **AND** the tab bar MUST NOT block completion, submit, back, logout, chat composer, feedback, or video actions.

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
- **THEN** the layout MUST show current chapter identity, within-family element chips, selected-element facts, family common properties, property-driven experiment-point groups, bottom navigation when in the authenticated shell, and completion actions without horizontal scrolling
- **AND** sibling-family browsing controls MUST NOT consume the page's primary top navigation area.

#### Scenario: Student needs to switch chapter
- **WHEN** a student wants to choose a different family or chapter
- **THEN** the page MUST expose a touch-friendly secondary navigation affordance to return to the periodic-table learning entry or switch chapter
- **AND** that affordance MUST NOT obscure the main experiment-point task area or the bottom tab bar.

### Requirement: Touch-first chemistry learning controls
The student H5 mobile layout SHALL make within-family element selection and experiment-point learning controls reachable by touch without desktop-only interaction patterns.

#### Scenario: Student switches selected element
- **WHEN** element chips are displayed for the current family
- **THEN** each chip MUST use a phone-appropriate hit area
- **AND** the active element state MUST be visually clear without relying on hover.

#### Scenario: Student opens an experiment point
- **WHEN** experiment-point cards are displayed below the chemistry context
- **THEN** each card MUST be tappable without hover or precise pointer input
- **AND** the bottom navigation, assistant tab, profile feedback form, or completion action MUST NOT block the point card, back action, completion action, or assessment entry.

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
The segmented switcher SHALL coexist with the authenticated app shell, safe areas, and bottom actions without visual or interaction overlap.

#### Scenario: Bottom navigation is visible
- **WHEN** the student is on a chapter page with the bottom tab bar available
- **THEN** the segmented switcher MUST remain a local chapter control above the content
- **AND** it MUST NOT be placed in or visually merge with the bottom app navigation.

#### Scenario: Safe-area and browser chrome are present
- **WHEN** the H5 app runs in a mobile browser or WebView with safe-area insets or browser chrome
- **THEN** the segmented switcher and its sticky offset MUST account for the app's safe-area and compact header layout
- **AND** it MUST avoid clipped labels, clipped active indicators, and horizontal overflow.

#### Scenario: Mobile QA covers A/B switching
- **WHEN** mobile viewport QA runs for this change
- **THEN** it MUST cover facts-to-experiments switching, experiments-to-facts switching, element switching, experiment point list, point detail, assistant tab entry, profile feedback entry, and assessment handoff
- **AND** it MUST check 360x780, 390x844, and 430x932 CSS-pixel viewports.

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

### Requirement: Mobile QA covers feedback attachments
The student frontend SHALL cover feedback screenshot attachment behavior from the `我的` profile destination in repeatable mobile QA.

#### Scenario: Feedback attachment QA runs
- **WHEN** mobile QA is run for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST cover opening `我的`, opening feedback, selecting or simulating a screenshot attachment, removing an attachment, submitting feedback, and returning to another tab
- **AND** it MUST verify that the feedback form and bottom navigation do not block each other.

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

### Requirement: Embedded atom model mobile layout
The student H5 mobile design system SHALL support an embedded atom model card inside the chapter facts view without breaking phone viewport layout.

#### Scenario: Atom model card fits phone widths
- **WHEN** the atom model card is rendered at 360px, 390px, or 430px CSS-pixel viewport widths
- **THEN** the card MUST fit without page-level horizontal scrolling
- **AND** its element tile, title, mode controls, compact facts, and canvas MUST not overlap each other
- **AND** long facts such as electron configuration and density MUST wrap or truncate in a readable mobile-safe way

#### Scenario: Atom model card does not hide primary tasks
- **WHEN** the facts view contains the atom model card, family common properties, property summaries, and experiment handoff content
- **THEN** the card MUST remain compact enough that the rest of the learning content is discoverable on a phone
- **AND** it MUST not reintroduce an encyclopedia-style stack of large fact cards before the experiment-point learning task area

#### Scenario: Atom model coexists with app shell controls
- **WHEN** the app bottom navigation, local facts/experiments switcher, assistant handoff, feedback/profile flow, or finish-learning action is present
- **THEN** the atom model card MUST not be obscured by those controls
- **AND** it MUST not obscure those controls

### Requirement: Touch-safe atom canvas interaction
The student H5 mobile design system SHALL make atom canvas interaction touch-friendly without interfering with page scrolling.

#### Scenario: Student rotates the atom by touch
- **WHEN** the student drags inside the atom canvas
- **THEN** the atom model MAY capture the pointer to rotate the model
- **AND** the drag behavior MUST remain limited to the canvas interaction region
- **AND** vertical page scrolling outside the canvas MUST remain usable

#### Scenario: Student uses mode and playback controls
- **WHEN** the atom model card exposes mode, reset, play, pause, or orbital option controls
- **THEN** every exposed control MUST have a phone-appropriate hit area
- **AND** active states MUST be visually clear without hover
- **AND** labels MUST remain readable on the smallest supported viewport

### Requirement: Mobile animation governance for atom viewer
The student H5 mobile design system SHALL govern embedded atom animation so it remains responsive and battery-conscious on phones.

#### Scenario: Atom animation is hidden or paused
- **WHEN** the page becomes hidden, the card unmounts, or the student pauses the model
- **THEN** the viewer MUST stop unnecessary animation frames
- **AND** it MUST clean up observers and pointer handlers when unmounted

#### Scenario: Atom model resizes
- **WHEN** the phone viewport changes size, browser chrome changes available space, or the student switches tabs/routes and returns
- **THEN** the atom canvas MUST recalculate its size
- **AND** it MUST render a nonzero visible model region rather than a collapsed or blank panel

### Requirement: Atom model mobile QA evidence
The student H5 mobile QA suite SHALL cover the atom model card as part of the authenticated learning flow.

#### Scenario: Mobile QA covers atom model
- **WHEN** mobile viewport QA runs after this change
- **THEN** it MUST cover navigating to a selected chapter facts view
- **AND** it MUST verify the atom model card is visible
- **AND** it MUST verify element chip switching still works
- **AND** it MUST verify the local facts/experiments switcher remains reachable
- **AND** it MUST verify no horizontal overflow occurs at 360x780, 390x844, and 430x932 CSS-pixel viewports

#### Scenario: Canvas QA has practical fallback
- **WHEN** automated QA cannot reliably inspect rendered canvas pixels in the local environment
- **THEN** QA MUST at least verify the canvas exists, has nonzero dimensions, and survives element/mode switching
- **AND** final verification MUST record any remaining manual phone/WebView visual check performed for canvas rendering

### Requirement: Compact element focus card layout
The student H5 mobile layout SHALL render the selected-element focus card as a compact phone-first learning component that preserves the periodic-table tile while keeping experiment tasks discoverable.

#### Scenario: Element tile remains the visual anchor
- **WHEN** the selected-element focus card is shown on a 360px to 430px CSS-pixel-wide phone viewport
- **THEN** the card MUST keep the element square visible near the leading edge of the card
- **AND** the square MUST show atomic number, element symbol, and English label without clipping
- **AND** the surrounding card content MUST align with the square rather than replacing it with plain text-only identity

#### Scenario: Focus and relevance text fit the card
- **WHEN** the selected element has focus-property and experiment-relevance copy
- **THEN** the focus-property line MUST be visually more prominent than supporting tags
- **AND** the experiment-relevance line MUST wrap within the card without horizontal overflow
- **AND** long labels MUST be clamped, wrapped, or otherwise constrained so they do not overlap the tile, tags, action, or following content

#### Scenario: Card stays compact before experiment tasks
- **WHEN** the chapter page contains the selected-element focus card above family facts or experiment-point content
- **THEN** the card MUST use a compact layout that avoids pushing the experiment-point task area below excessive introductory content
- **AND** long detailed facts MUST be placed in the facts/detail area instead of expanding the compact card by default

#### Scenario: Detail action is touch reachable
- **WHEN** the focus card includes an action to view element details
- **THEN** the action MUST be reachable by touch without hover or desktop-only interaction
- **AND** it MUST NOT visually compete with the facts/experiments segmented switcher, experiment-point card actions, AI entry, feedback entry, or completion action

#### Scenario: Mobile viewport QA covers redesigned card
- **WHEN** implementation verification runs for the redesigned selected-element card
- **THEN** QA MUST cover 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check element switching, long Chinese focus/relevance copy, tag wrapping, detail action reachability, and the first visible experiment-point task area

### Requirement: Bottom tab navigation primitive
The student H5 mobile design system SHALL provide a bottom tab navigation primitive for authenticated app-level destinations.

#### Scenario: Bottom tab bar renders on phone viewport
- **WHEN** an authenticated student page is rendered at 360px, 390px, or 430px CSS-pixel width
- **THEN** the bottom tab bar MUST fit without horizontal scrolling
- **AND** each visible item MUST have a phone-appropriate touch target, readable label, and clear active state.

#### Scenario: Safe area protects bottom navigation
- **WHEN** the H5 app runs in a mobile browser or WebView with bottom browser chrome or safe-area insets
- **THEN** the bottom navigation MUST account for the bottom safe area
- **AND** page content MUST reserve enough bottom padding so primary actions, inputs, cards, and video controls can scroll clear of the bar.

#### Scenario: Tab labels are localized and stable
- **WHEN** all student features are enabled
- **THEN** the bottom navigation MUST use concise app-level labels such as `学习`, `实验`, `问答`, `测评`, and `我的`
- **AND** it MUST NOT use chapter-local labels such as `性质通识` or `实验视频` as app-level tabs.

### Requirement: Profile feedback attachment controls
The student H5 mobile design system SHALL support feedback screenshot attachment controls inside the `我的` profile destination rather than inside a global floating feedback overlay.

#### Scenario: Student opens profile feedback
- **WHEN** the student opens the feedback area from `我的`
- **THEN** the form MUST provide touch-friendly screenshot add, change, and remove controls
- **AND** selected filename or attachment state MUST fit within phone viewport width without horizontal overflow.

#### Scenario: Feedback form uses mobile keyboard
- **WHEN** the student focuses the feedback text input on a phone viewport
- **THEN** the input and submit action MUST remain usable with the mobile keyboard expected
- **AND** the bottom navigation MUST NOT cover the submit action.

### Requirement: Assistant point starter mobile layout
The student H5 mobile design system SHALL support a point-aware assistant starter layout that remains readable and reachable on supported phone viewports.

#### Scenario: Point starter renders on narrow phones
- **WHEN** the student opens experiment/video-point starter mode on a 360px to 430px CSS-pixel-wide viewport
- **THEN** experiment group, experiment, point, template, preview, composer, and launch controls MUST remain within the viewport width
- **AND** the page MUST avoid horizontal scrolling caused by long Chinese experiment or point labels.

#### Scenario: Point starter uses progressive disclosure
- **WHEN** the point starter contains multiple experiment groups, experiments, or video points
- **THEN** the UI MUST present them through stacked sections, segmented controls, accordions, sheets, or equivalent phone-first disclosure
- **AND** it MUST NOT require a desktop three-column grid to use the starter.

#### Scenario: Long point labels are rendered
- **WHEN** experiment titles, point titles, candidate labels, template descriptions, or preview questions are longer than one short phrase
- **THEN** the UI MUST wrap, clamp, or otherwise constrain text so controls remain usable
- **AND** selected states MUST remain visually clear without relying on hover.

### Requirement: Assistant point starter touch and safe-area behavior
The student H5 mobile design system SHALL keep assistant point starter actions reachable around the fixed bottom navigation, safe areas, and the chat composer.

#### Scenario: Starter and bottom navigation coexist
- **WHEN** point starter controls, composer, starter launch action, and bottom tab navigation are all visible
- **THEN** the composer and launch action MUST remain reachable by touch
- **AND** bottom navigation MUST NOT cover the active input, selected controls, send button, or launch action.

#### Scenario: Student scrolls point starter
- **WHEN** the point starter content is taller than the available chat panel space
- **THEN** the starter content MUST scroll inside the assistant panel or otherwise remain reachable
- **AND** the page MUST NOT create nested scrolling that traps the composer or bottom navigation offscreen.

#### Scenario: Student focuses the composer in point mode
- **WHEN** the student focuses the assistant composer while point starter mode is active
- **THEN** the input and submit action MUST remain usable when the mobile keyboard is expected to appear
- **AND** point starter controls MUST not overlap the focused input.

### Requirement: Assistant point starter loading and empty states
The student H5 mobile design system SHALL present point starter loading, empty, and error states without blocking global course asking.

#### Scenario: Point starter is loading data
- **WHEN** the app is loading experiment groups, experiments, or point detail for the point starter
- **THEN** it MUST show compact mobile-readable loading feedback in the relevant point-starter section
- **AND** it MUST keep the global course starter or free-form composer usable whenever possible.

#### Scenario: No point choices are available
- **WHEN** the selected group or experiment has no visible point choices
- **THEN** the UI MUST show a compact empty state that explains the point choices are unavailable
- **AND** it MUST provide a way to choose another group/experiment or ask a global/free-form question.

#### Scenario: Point starter request fails
- **WHEN** an optional point starter data request fails
- **THEN** the UI MUST show a student-readable error or retry affordance
- **AND** it MUST NOT break the rest of the assistant tab.

### Requirement: Assistant point starter mobile QA coverage
The student H5 mobile QA workflow SHALL verify the point-aware assistant starter across supported phone viewports.

#### Scenario: Mobile viewport QA covers point starter
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover point starter mode at 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check that there is no horizontal overflow, no blocked composer, no blocked launch action, and no bottom-navigation overlap.

#### Scenario: Mobile QA covers point starter launch
- **WHEN** mobile viewport QA exercises the assistant point starter
- **THEN** it MUST select a student-visible group, experiment or point option, and question template
- **AND** it MUST verify that the generated point starter request transitions into normal chat.

#### Scenario: Mobile QA confirms bottom status removal
- **WHEN** mobile viewport QA sends an assistant message
- **THEN** it MUST verify that per-turn assistant status remains visible
- **AND** it MUST verify that the redundant bottom status row below the composer is not rendered.

### Requirement: Assistant starter mobile layout
The student H5 mobile design system SHALL support an assistant starter layout that fits phone viewports without horizontal overflow, clipped text, or blocked actions.

#### Scenario: Starter renders on narrow phones
- **WHEN** the student opens the `问答` tab on a 360px to 430px CSS-pixel-wide viewport
- **THEN** the assistant starter surface MUST keep all primary starter controls within the viewport width
- **AND** starter intent labels, context title, preview text, and launch action MUST not overlap each other.

#### Scenario: Long Chinese starter labels render
- **WHEN** starter labels, prompt text, or context titles are longer than a single short phrase
- **THEN** the UI MUST wrap, clamp, or otherwise constrain text so it remains readable
- **AND** it MUST NOT rely on horizontal scrolling for the primary first-screen starter intent choices.

#### Scenario: Starter and bottom navigation coexist
- **WHEN** the starter surface, composer, and bottom tab navigation are all visible
- **THEN** the composer and starter launch action MUST remain reachable by touch
- **AND** bottom navigation MUST NOT cover the active input, send button, or launch action.

#### Scenario: Assistant panel uses available mobile height
- **WHEN** the student opens the `问答` tab between the sticky app header and fixed bottom navigation
- **THEN** the primary assistant panel SHOULD occupy the available vertical space with only necessary top and bottom breathing room
- **AND** it MUST NOT use a short fixed maximum height that leaves a large empty background area before the bottom navigation.

### Requirement: Assistant composer mobile ergonomics
The student H5 assistant composer SHALL remain usable with mobile keyboards and student-length chemistry questions.

#### Scenario: Student focuses the composer
- **WHEN** a student focuses the assistant input on a phone viewport
- **THEN** the input and submit action MUST remain usable when the mobile keyboard is expected to appear
- **AND** the layout MUST avoid desktop-only fixed heights that hide the focused input behind browser chrome or bottom navigation.

#### Scenario: Student enters a longer question
- **WHEN** the student types a multi-clause chemistry question or edits a starter preview into a custom question
- **THEN** the composer MUST allow enough visible text for comfortable editing
- **AND** the send action MUST remain visually associated with the input.

### Requirement: Assistant viewport QA coverage
The student H5 mobile QA workflow SHALL verify the assistant starter and chat interaction across supported phone viewports.

#### Scenario: Mobile viewport QA runs for assistant starter
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover the global assistant starter at 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check that there is no horizontal page overflow.

#### Scenario: Mobile viewport QA covers context handoff
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover at least one assistant launch from a learning chapter or experiment point context
- **AND** it MUST verify that the merged context cue, starter intents, composer, and bottom navigation remain reachable.

#### Scenario: Feature-disabled assistant remains covered
- **WHEN** assistant feature flags are disabled
- **THEN** student-web tests or QA MUST verify that the assistant tab remains hidden, disabled, or redirected according to the current app-config behavior.

