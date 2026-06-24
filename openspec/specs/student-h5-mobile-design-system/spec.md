# student-h5-mobile-design-system Specification

## Purpose
Define mobile-browser H5 design primitives, viewport safety, touch ergonomics, overlay governance, and mobile QA expectations shared by student-facing screens.
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
The student frontend SHALL be verified against common phone viewport sizes before `web-student` changes are considered complete.

#### Scenario: Required viewport sizes pass
- **WHEN** viewport QA runs for `web-student`
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
The student frontend SHALL coordinate bottom navigation, fixed controls, dialogs, sheets, anchored popovers, and any remaining overlays through a shared mobile layering rule.

#### Scenario: Fixed and overlay controls do not overlap
- **WHEN** dialogs, sheets, anchored popovers, chat pages, feedback forms, assessment actions, or other fixed controls are shown
- **THEN** conflicting controls MUST be hidden, disabled, or repositioned so they do not overlap the active interaction
- **AND** the active interaction MUST stay within the visible phone viewport width.

#### Scenario: Bottom actions remain reachable
- **WHEN** a page contains the bottom tab bar and also contains an in-content primary action or anchored learning-selection popover
- **THEN** the page MUST provide enough bottom spacing or overlay collision handling for the action to remain reachable
- **AND** the tab bar MUST NOT block completion, submit, back, logout, chat composer, feedback, video actions, or learning-selection popover rows.

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

#### Scenario: Student opens a catalog point
- **WHEN** catalog point cards are displayed below the chemistry context
- **THEN** each card MUST be tappable without hover or precise pointer input
- **AND** the bottom navigation, assistant tab, profile feedback form, or completion action MUST NOT block the point card, back action, completion action, or assessment entry.

### Requirement: Compact context before primary tasks
The student H5 mobile layout SHALL keep chemistry context compact enough that the experiment-point task area remains discoverable on phone viewports.

#### Scenario: Chemistry facts are lengthy
- **WHEN** selected-element facts, family common properties, trend formulas, or reference media would make the top context area long
- **THEN** the layout MUST use compact summaries, carousels, accordions, tabs, or equivalent progressive disclosure
- **AND** it MUST avoid making experiment-point learning feel secondary to an encyclopedia-style fact page.

### Requirement: Chapter catalog browser controls
The student frontend SHALL provide phone-first catalog browser controls inside a selected family or chapter instead of a fixed two-mode chapter switcher.

#### Scenario: Catalog browser appears on chapter page
- **WHEN** the student opens a selected family/chapter learning page
- **THEN** the page MUST render compact family or element context above the chapter catalog browser
- **AND** the catalog browser MUST be the primary path to directories and point video/detail learning
- **AND** the page MUST NOT render a fixed two-option facts/common-properties versus experiment-videos segmented switcher.

#### Scenario: Catalog browser controls remain reachable
- **WHEN** the student browses catalog entries on a phone viewport
- **THEN** search, more actions, root breadcrumb, and directory breadcrumb controls MUST remain reachable according to the catalog layout
- **AND** those controls MUST NOT be placed in the bottom navigation area where they would conflict with global navigation, AI, feedback, video, or finish actions.

#### Scenario: Catalog browser supports touch use
- **WHEN** a student uses touch input on a 360px to 430px CSS-pixel-wide viewport
- **THEN** catalog rows, breadcrumb chips, search, more actions, element rail buttons, and element-detail affordances MUST have phone-appropriate hit areas, clear active state where applicable, and readable labels
- **AND** navigating catalog depth MUST NOT require hover, keyboard shortcuts, or undiscoverable gestures.

### Requirement: Catalog browser overlay governance
The chapter catalog browser controls SHALL coexist with the authenticated app shell, safe areas, and detail-page actions without visual or interaction overlap.

#### Scenario: Detail page is open
- **WHEN** the student is on a chapter, catalog directory, element detail, search, or point video detail route
- **THEN** bottom navigation MUST remain hidden according to route-role semantics
- **AND** chapter-local catalog controls MUST remain inside the page content rather than merging with app-level navigation.

#### Scenario: Safe-area and browser chrome are present
- **WHEN** the H5 app runs in a mobile browser or WebView with safe-area insets or browser chrome
- **THEN** catalog browser controls, sticky element rails, and second-level back affordances MUST account for the app's safe-area and compact header layout
- **AND** they MUST avoid clipped labels, clipped active indicators, and horizontal overflow.

#### Scenario: Mobile QA covers catalog navigation
- **WHEN** mobile viewport QA runs for this change
- **THEN** it MUST cover area-to-chapter navigation, element switching, catalog directory navigation, catalog search, point video detail, assistant tab entry, profile feedback entry, and assessment handoff
- **AND** it MUST check 360x780, 390x844, and 430x932 CSS-pixel viewports.

### Requirement: Mobile learning-entry state cues
The student H5 mobile design system SHALL keep selected area state, recommendation guidance, and chapter navigation entries visually distinct by separating periodic-table selection from smart recommendation content.

#### Scenario: Selected periodic-table area is highlighted
- **WHEN** an area is selected on the periodic-table entry
- **THEN** the selected area's element cells MUST be visually emphasized without relying on heavy dark per-cell borders
- **AND** non-selected area cells MUST remain visible but visually secondary
- **AND** the selected-state treatment MUST NOT be confused with recommendation styling.

#### Scenario: Recommendation is shown below the table
- **WHEN** the learning root has a recommended profile
- **THEN** recommendation guidance MUST render in a separate smart card below the periodic table
- **AND** the periodic-table area controls MUST NOT show yellow recommendation badges
- **AND** periodic-table element cells MUST NOT show gold recommendation outlines
- **AND** the recommendation card MUST fit the phone layout without leaving the lower half of the learning root visually empty.

#### Scenario: Chapter entry cards remain tappable rows
- **WHEN** chapter cards are shown on a phone viewport
- **THEN** each card MUST read as a tappable navigation row
- **AND** recommendation styling MUST be limited to a label or similarly compact cue outside the periodic-table selector
- **AND** the label MUST NOT consume a standalone row that pushes the chapter title down
- **AND** recommendation styling MUST NOT use the same visual treatment as selected cards, active tabs, or pressed controls
- **AND** area-level chapter card titles MUST prefer the learning object label such as `碱金属和碱土金属` rather than repeating the selected area prefix such as `s区`.

#### Scenario: Learnable element symbols fit selected cells
- **WHEN** selected periodic-table cells show profile-backed element symbols
- **THEN** the symbols MUST fit inside the small cell without changing the periodic-table grid dimensions
- **AND** the symbols MUST add a learnable cue without reintroducing heavy dark selected-cell borders
- **AND** removing recommendation outlines MUST NOT make learnable symbols unreadable.

#### Scenario: Student periodic table aligns with accepted areas
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the area controls MUST show six learning areas in a two-row, three-column grid
- **AND** the six areas MUST be `氢元素`, `p区元素`, `s区元素`, `ds区元素`, `d区元素`, and `f区元素`
- **AND** the combined `氢和稀有气体` area control MUST NOT be shown
- **AND** the student entry MUST NOT expose a `通识资源` area.

#### Scenario: Student periodic table maps special elements correctly
- **WHEN** the student H5 periodic-table entry is shown
- **THEN** the H cell MUST use the hydrogen area color and route target
- **AND** noble-gas cells in group 18 MUST use the p-area color and route target
- **AND** f-block lanthanide and actinide cells MUST use the f-area color and route target
- **AND** f-block lanthanide and actinide rows MUST render as detached rows that do not occupy the group 18 display column.

#### Scenario: Student f-block layout remains phone-safe
- **WHEN** the student H5 periodic-table entry is rendered at common phone widths
- **THEN** the f-block rows MUST include La-Lu and Ac-Lr in order where cells are rendered
- **AND** the detached rows MUST preserve the left-side period label column for `镧系` and `锕系`
- **AND** profile-backed element symbols MUST be small enough that two-letter symbols fit comfortably.

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

### Requirement: Element detail atom model mobile layout
The student H5 mobile design system SHALL support a full atom model card inside the element detail second-level route without breaking phone viewport layout.

#### Scenario: Atom model card fits phone widths
- **WHEN** the element detail route renders the atom model card at 360px, 390px, or 430px CSS-pixel viewport widths
- **THEN** the card MUST fit without page-level horizontal scrolling
- **AND** its element tile, title, mode controls, compact facts, and canvas MUST not overlap each other
- **AND** long facts such as electron configuration and density MUST wrap or truncate in a readable mobile-safe way

#### Scenario: Chapter page keeps catalog primary
- **WHEN** the chapter page shows compact selected-element context and catalog navigation
- **THEN** the full atom model MUST remain available through the element detail route rather than expanding the chapter page into an encyclopedia-style facts screen
- **AND** the chapter catalog browser MUST remain the primary path to point video/detail learning.

#### Scenario: Atom model coexists with app shell controls
- **WHEN** the element detail route is open
- **THEN** bottom navigation MUST remain hidden because the element detail route is a second-level page
- **AND** the PageBar back affordance, model controls, assistant handoff, and any scrollable facts content MUST not obscure one another.

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
The student H5 mobile design system SHALL govern atom animation so it remains responsive and battery-conscious on phones.

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
- **THEN** it MUST cover navigating from a selected chapter or family page into an element detail route
- **AND** it MUST verify the atom model card is visible
- **AND** it MUST verify model mode controls still work
- **AND** it MUST verify returning to the chapter page restores the chapter catalog browser context where browser history allows
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
- **AND** it MUST NOT visually compete with the chapter catalog browser, point actions, AI entry, feedback entry, or completion action

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
- **WHEN** mobile viewport QA runs for `web-student`
- **THEN** it MUST cover the global assistant starter at 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check that there is no horizontal page overflow.

#### Scenario: Mobile viewport QA covers context handoff
- **WHEN** mobile viewport QA runs for `web-student`
- **THEN** it MUST cover at least one assistant launch from a learning chapter or catalog point context
- **AND** it MUST verify that the merged context cue, starter intents, composer, and bottom navigation remain reachable.

#### Scenario: Feature-disabled assistant remains covered
- **WHEN** assistant feature flags are disabled
- **THEN** `web-student` tests or QA MUST verify that the assistant tab remains hidden, disabled, or redirected according to the current app-config behavior.

### Requirement: Collapsing family headers preserve mobile content space
The student H5 mobile design system SHALL allow a family context header to collapse into a compact sticky header without harming catalog readability.

#### Scenario: Detail page chrome is compact
- **WHEN** a student opens a second-level detail page
- **THEN** the page bar MUST use a plain left arrow and a left-aligned title
- **AND** the page bar MUST NOT reserve a decorative square button background or mirrored right spacer only for centering
- **AND** the vertical padding MUST stay compact enough to preserve room for the content below.

#### Scenario: Expanded family header renders on phone
- **WHEN** a family catalog shell is rendered at common phone widths from 360px to 430px
- **THEN** the expanded header MUST use stable dimensions, line clamping, and horizontal overflow where needed
- **AND** text, element tiles, buttons, and catalog cards MUST not overlap
- **AND** the header MUST avoid decorative height that prevents catalog discovery.

#### Scenario: Compact family header sticks during scroll
- **WHEN** the family context collapses while the student scrolls catalog content
- **THEN** the compact header MUST remain readable and tappable
- **AND** it MUST keep touch targets usable without growing taller than the intended compact row
- **AND** it MUST contrast with catalog content without hiding list rows behind translucent artifacts.

#### Scenario: Motion is used for collapse
- **WHEN** the expanded header transitions into the compact header
- **THEN** the animation MUST be short, natural, and responsive to scroll
- **AND** it MUST NOT use delayed follower behavior, idle timers, or continuous expensive re-rendering.

### Requirement: Fullscreen assistant surface layout
The student H5 mobile design system SHALL support root-level fullscreen assistant surfaces that are not visually framed as cards and carry a bright static course-themed background.

#### Scenario: Assistant root uses full-bleed surface
- **WHEN** the authenticated student opens the `AI` root on a 360px, 390px, or 430px CSS-pixel-wide viewport
- **THEN** the assistant root MUST avoid a bordered floating panel/card appearance
- **AND** it MUST avoid nested cards inside the first-screen assistant surface
- **AND** it MUST avoid horizontal page overflow
- **AND** the root assistant surface MUST be allowed to suppress the generic root app header so route content begins at the top of the phone page frame.

#### Scenario: Assistant root uses static learning-page background
- **WHEN** a fullscreen assistant root uses a decorative background
- **THEN** the background SHOULD be near-white or paper-like rather than dark
- **AND** the background glow SHOULD stay aligned with the student learning page palette, using paper white, pale yellow-green, and light sage-green rather than cold blue-mint washes
- **AND** the root assistant MUST NOT render animated star, particle, meteor, or canvas background effects
- **AND** the static background MUST stay light enough that text, icons, composer borders, and bottom navigation remain readable.

#### Scenario: Assistant root preserves bottom-weighted composition
- **WHEN** the assistant root has no messages
- **THEN** the top bar MUST remain visually light
- **AND** the middle area MUST preserve large breathing room
- **AND** primary interaction weight MUST sit near the bottom composer, following the reference layout's low-center gravity.

#### Scenario: Root assistant title bar replaces generic page header
- **WHEN** the `AI` root renders as a fullscreen assistant surface
- **THEN** the generic root page header MUST NOT reserve vertical space above the chat surface
- **AND** the assistant title, history action, new-chat action, and any top-level assistant identity MUST live inside the assistant surface top bar
- **AND** root assistant top-bar actions MUST be icon-only controls that visually merge with the background rather than framed card buttons
- **AND** the root assistant top bar SHOULD remain compact enough to behave like lightweight chat chrome rather than a page header
- **AND** explanatory context copy such as global-course descriptions MUST NOT appear in that top bar.

#### Scenario: Composer and bottom navigation coexist
- **WHEN** the root assistant composer and bottom navigation are both visible
- **THEN** the composer bottom edge MUST sit above the bottom navigation top edge
- **AND** the send action MUST remain reachable by touch
- **AND** the send action MUST be visually embedded within the composer container rather than placed as an external square button
- **AND** the root composer SHOULD use a large rounded capsule form, approximately 82px tall with a radius near 24px on common phone widths
- **AND** the root composer SHOULD keep reference-like 12px surface side margins and a compact approximately 34px circular send control seated near the capsule's bottom-right edge
- **AND** the root composer placeholder SHOULD guide experiment learning, such as `问实验现象、步骤或原理`, rather than generic casual chat phrasing
- **AND** the bottom navigation MUST NOT cover the active input, send button, starter prompt, or visible chat messages.

#### Scenario: Root and detail assistant variants remain distinct
- **WHEN** the root assistant route and contextual assistant detail route are rendered
- **THEN** root styling MUST be scoped to the root variant
- **AND** detail styling MUST preserve route-stack pagebar/back behavior and hidden bottom navigation
- **AND** root-only actions such as history MUST NOT leak into contextual detail routes.

### Requirement: Mobile chat empty-state rhythm
The student H5 mobile design system SHALL support sparse AI chat empty states with large breathing room before the first turn.

#### Scenario: Empty chat uses low prompt placement
- **WHEN** a root AI chat has no messages
- **THEN** the first screen MUST NOT show a starter prompt card or explanatory copy block above the composer
- **AND** the first screen MAY show the Atom AI identity pictogram centered above one welcome phrase, such as `从一个实验开始吧！`, in the calm middle area
- **AND** that welcome group MUST remain unframed without a card container, subtitle, or secondary explanatory line
- **AND** the middle of the screen MUST remain visually calm and uncluttered
- **AND** the UI MUST NOT fill the empty state with multiple stacked cards or dense prompt grids
- **AND** the first screen MUST NOT include a separate explanatory assistant intro block above the calm middle area.

#### Scenario: Empty chat keeps course atmosphere
- **WHEN** the sparse AI root empty state renders
- **THEN** the visual treatment MAY use the existing chemistry green, subtle grid, and paper-like surface
- **AND** those treatments MUST behave as static background treatments rather than card borders around the whole assistant.

### Requirement: Branded edge-to-edge point video player controls
The student H5 mobile design system SHALL support a branded, touch-safe, edge-to-edge point video player control layer for point video detail pages, and playable point videos SHALL use a single custom mobile shell rather than ArtPlayer's default visible chrome.

#### Scenario: Player controls are inactive
- **WHEN** the point detail video player is visible, playable, and its custom shell is inactive
- **THEN** the player MUST prioritize the video frame or poster
- **AND** the player MUST appear as the page header rather than as a card inside a card-like content stack
- **AND** browser native video controls MUST NOT be visible
- **AND** ArtPlayer's default bottom toolbar, default progress control, default time display, default play control, default settings control, default fullscreen control, and default mask/state chrome MUST NOT be visible as the student-facing product UI
- **AND** the playable player-owned return arrow MUST NOT be visible or touchable
- **AND** the inactive shell MUST expose no persistent toolbar except a faint bottom progress indicator when progress data is available.

#### Scenario: Student activates player controls
- **WHEN** the student taps or otherwise activates the playable video player on a touch viewport
- **THEN** the player MUST reveal the custom active shell inside the player footprint
- **AND** the active shell MUST include a touch-reachable route return action, a central play/pause control, time feedback where duration is available, an interactive progress/seek control, and a fullscreen or equivalent player affordance where supported
- **AND** those controls MUST hide or de-emphasize again according to normal player inactivity behavior
- **AND** those controls MUST remain inside the player footprint rather than using the generic detail-page header
- **AND** the player-owned return action MUST become visible and touchable only while the custom shell is active
- **AND** the player-owned return action MUST render the same shared filled-outline back-arrow path as ordinary second-level page headers.

#### Scenario: Custom shell owns visible playback actions
- **WHEN** a playable point video renders visible playback controls
- **THEN** every visible custom playback control MUST call a real playback, seek, fullscreen, mute, settings, or route action
- **AND** display-only playback controls MUST NOT be rendered as if they control playback
- **AND** the custom shell MUST use ArtPlayer or the underlying `HTMLVideoElement` as the playback source of truth for current time, duration, playing state, buffering/loading state, error state, and fullscreen state
- **AND** the shell MUST clean up timers and event listeners when the ArtPlayer instance is destroyed or the source changes.

#### Scenario: Progress is custom and touch safe
- **WHEN** playable point-video progress is shown in the custom shell
- **THEN** the inactive progress indicator MUST be a quiet bottom-pinned line without a draggable thumb or full toolbar
- **AND** the active progress control MUST provide a phone-safe hit target larger than the visible line
- **AND** the active progress control MUST use a colored branded played track and a small circular SYSU progress thumb
- **AND** the inactive progress indicator MUST NOT show the SYSU thumb or colored active seek treatment
- **AND** dragging or tapping the active progress control MUST seek the ArtPlayer media to the corresponding playback time
- **AND** seeking MUST NOT accidentally trigger route back or simple tap-to-toggle behavior.

#### Scenario: SYSU progress branding is restrained
- **WHEN** a playable point video renders custom progress branding
- **THEN** any SYSU logo or SYSU-logo-derived progress treatment MUST be scoped to the point video player
- **AND** the SYSU progress thumb MUST appear only with the active progress/seek control
- **AND** the branding MUST NOT make the inactive state visually noisy
- **AND** the branding MUST NOT obscure the progress hit target, central play/pause control, time capsule, or player-owned return action
- **AND** unrelated student controls MUST NOT be restyled by the player branding.

#### Scenario: Empty video state keeps visible route return
- **WHEN** the point video header renders the no-playable-video placeholder
- **THEN** the placeholder MUST keep a visible shared return affordance immediately available
- **AND** the placeholder return affordance MUST use the same shared filled-outline back-arrow geometry as playable player chrome
- **AND** the placeholder MUST NOT show fake play, progress, time, fullscreen, or settings controls
- **AND** the placeholder MUST remain visually distinct from an inactive playable video, because inactive playable videos can still reveal controls by tapping the player.

#### Scenario: Phone viewport layout is verified
- **WHEN** the point video detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the player, custom shell, flat title section, learning content sections, and finish-learning action MUST avoid horizontal scrolling and incoherent overlap
- **AND** the player controls MUST remain reachable by touch without relying on hover or desktop keyboard shortcuts
- **AND** playable-video inactive state MUST show no persistent toolbar except the faint bottom progress indicator
- **AND** playable-video active state MUST keep the back arrow, centered playback control, time feedback, progress, and supported fullscreen/settings controls inside the player footprint
- **AND** chemistry equations inside learning content MUST render at body-copy scale and wrap within the phone content area whenever the rendering engine permits
- **AND** large display-math equation styling MUST NOT be the default student mobile treatment.

#### Scenario: Detail page opts out of card-grid styling
- **WHEN** a point video detail route is displayed in the student H5 shell or teacher student-preview phone frame
- **THEN** the detail content MUST remove the paper grid background used by other experiment learning views
- **AND** the player MUST have square outer corners at the page edge
- **AND** the title and learning sections MUST be separated by full-width bands or dividers rather than nested cards
- **AND** the custom player shell MUST clip to the video header footprint and MUST NOT create page-level overlays outside the player frame.

#### Scenario: Student preview matches real H5 player interaction
- **WHEN** the point video detail route is rendered inside the teacher student-preview phone frame
- **THEN** tapping the playable video MUST reveal the same custom active player shell as normal student H5
- **AND** inactive-player shell hiding MUST match the normal student H5 behavior
- **AND** progress tapping or dragging in student preview MUST seek through the same shell logic as real H5
- **AND** no preview-only player controls or preview-only event paths MAY replace the student shell behavior.

### Requirement: Mobile home feed preserves horizontal video clarity
The student H5 mobile design system SHALL support horizontal 16:9 video feed cards and compact action rows that remain clear, aligned, and usable on phone viewports.

#### Scenario: Home feed renders on common phone widths
- **WHEN** the home video feed is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** video cards MUST fit the viewport without horizontal scrolling
- **AND** title, catalog path, tags, action row, media controls, and bottom navigation MUST NOT overlap

#### Scenario: Home video action row fits common phone widths
- **WHEN** a home video card action row is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** the left `查看实验` CTA and the right icon group MUST remain on one visual row without wrapping into an incoherent second line
- **AND** the like, favorite or bookmark, share, Atom, and more controls MUST keep stable touch targets and accessible names
- **AND** the Atom control MUST remain visually identifiable as the green highlighted product action without pushing adjacent icons out of view

#### Scenario: Video card loads before playback
- **WHEN** a feed card is not active or video metadata is still loading
- **THEN** the card MUST preserve a stable 16:9 media box
- **AND** poster, loading, fallback states, or action-row icon states MUST NOT shift the surrounding feed layout

#### Scenario: Feed reaches bottom navigation
- **WHEN** the student scrolls near the bottom of the home feed
- **THEN** the final card content MUST remain readable above the app bottom navigation and safe-area inset
- **AND** the bottom navigation MUST not obscure primary feed actions

### Requirement: Viewport-contained anchored learning popover
The student H5 mobile design system SHALL support anchored learning-selection popovers that remain inside the visible phone viewport and do not affect root page layout.

#### Scenario: Popover opens from a periodic-table trigger
- **WHEN** a student taps a periodic-table area control or element cell on a supported phone viewport
- **THEN** the popover MUST appear visually related to the tapped trigger
- **AND** it MUST render above the page as a fixed or portaled overlay rather than inline content
- **AND** opening it MUST NOT change the document flow, stretch the periodic-table card, or increase the root page's layout height.

#### Scenario: Popover avoids viewport clipping
- **WHEN** the tapped trigger is near the top, bottom, left, or right edge of the visible viewport
- **THEN** the popover MUST flip, shift, or otherwise reposition so its actionable rows remain visible
- **AND** it MUST respect viewport padding and mobile safe-area constraints
- **AND** it MUST NOT be clipped behind the bottom navigation, browser chrome, or rounded phone preview frame in the supported QA viewports.

#### Scenario: Area chapter list fits normal phone viewports
- **WHEN** an area chapter list such as the p-area list is opened at 360x780, 390x844, or 430x932 CSS pixels
- **THEN** the popover SHOULD show the complete list without internal scrolling
- **AND** if the visual viewport is unusually short, the popover MUST clamp its max height and keep rows reachable through internal scrolling rather than expanding the page.

#### Scenario: Popover rows are touch safe
- **WHEN** chapter rows are shown inside the popover
- **THEN** each row MUST have a phone-appropriate touch target
- **AND** row titles, element symbol summaries, and trailing navigation icons MUST fit without horizontal overflow
- **AND** the selected row action MUST be reachable without hover, long press, or desktop keyboard shortcuts.

#### Scenario: Popover dismissal is predictable
- **WHEN** the popover is open
- **THEN** outside tap, Escape, route transition, and row selection MUST dismiss it
- **AND** dismissal MUST restore interaction to the periodic-table root without visual overlap or stuck focus state.

### Requirement: Unified second-level back arrow geometry
The student H5 mobile design system SHALL provide one shared vector geometry for second-level back arrows instead of allowing each screen to independently choose an icon, copied SVG, or bitmap-derived asset.

#### Scenario: Shared back arrow source is used
- **WHEN** a student H5 second-level back arrow is rendered in React UI or injected into player HTML chrome
- **THEN** the visible glyph MUST come from the shared student mobile back-arrow source
- **AND** ordinary detail headers, unified search back controls, point-video player chrome, and point-video empty states MUST NOT maintain separate hand-copied arrow paths for the same back affordance.

#### Scenario: Arrow is filled-outline SVG
- **WHEN** the shared back arrow glyph is implemented
- **THEN** it MUST be drawn as one closed SVG path filled with `currentColor`
- **AND** it MUST use the shared `24x24` viewBox filled-outline geometry equivalent to `M7.414 13l5.043 5.04-1.414 1.42L3.586 12l7.457-7.46 1.414 1.42L7.414 11H21v2H7.414z`
- **AND** it MUST NOT use independent `line`, `polyline`, stroke-width-driven arrow segments, tip patch polygons, copied per-screen SVG strings, or bitmap screenshot assets for the same back affordance.

#### Scenario: Geometry follows measured reference proportions
- **WHEN** the shared arrow is rendered at the standard second-level glyph size
- **THEN** the visible arrow MUST read wider than Lucide's default `ArrowLeft` shape
- **AND** the horizontal tail MUST extend to the right edge of the filled-outline silhouette without relying on stroke caps
- **AND** the arrow head MUST be defined by the closed path outline rather than by joined stroke segments
- **AND** the arrow joint MUST avoid square burrs, split tips, protruding artifacts, or anti-aliased seams at the left point.

#### Scenario: Touch target remains phone-safe
- **WHEN** the back arrow visual is moved or resized
- **THEN** its tappable control MUST remain phone-appropriate and SHOULD preserve the existing `44px` hit area where practical
- **AND** the implementation MUST NOT shrink the accessible target merely to make the visible glyph closer to the screen edge.

### Requirement: Second-level back arrow placement matches mobile reference spacing
The student H5 mobile design system SHALL position the visible second-level back arrow with reference-like left whitespace rather than the current overly-loose left margin.

#### Scenario: Reference-derived left whitespace is used
- **WHEN** a second-level student page is rendered near the current preview width of `406px`
- **THEN** the first visible arrow pixel MUST use the tuned compact-left standard validated by phone preview
- **AND** ordinary page headers MUST keep a `44px` tappable icon button while using a compact `38px` back column and about `4px` title gap
- **AND** ordinary page-header titles MUST sit about one Chinese character away from the arrow rather than being pushed by the full touch-target width
- **AND** the visual left whitespace MUST be materially smaller than the previous wide-left-padding implementation without overcorrecting to the screen edge.

#### Scenario: Adopted placement constants are preserved
- **WHEN** the current student H5 second-level back standard is implemented
- **THEN** normal `PageBar` back controls MUST use the adopted compact placement equivalent to `margin-left: 12px`, a `38px` back column, a `4px` title gap, and `translateX(-8px)` on the icon button
- **AND** unified search back controls MUST use the same `translateX(-8px)` visual placement standard
- **AND** point-video playable chrome and empty-video back controls MUST use the adopted player placement equivalent to `4px` left and `6px` top so the apparent position aligns with ordinary second-level PageBar arrows
- **AND** all of those controls MUST preserve phone-safe hit targets.

#### Scenario: Standard applies to every second-level page
- **WHEN** any current or future student H5 second-level page needs a visible back affordance
- **THEN** the page MUST reuse the shared second-level back-arrow geometry and the matching placement family from this requirement
- **AND** ordinary pages MUST use the PageBar placement family, search-like pages MUST use the search-bar placement family, and video-player pages MUST place the same shared arrow inside player chrome
- **AND** a new back-arrow style, copied icon, bitmap-derived glyph, or unrelated left-spacing value MUST require a future OpenSpec change before implementation.

#### Scenario: Common phone widths remain aligned
- **WHEN** second-level back arrows are rendered on `360px`, `390px`, or `430px` wide phone viewports
- **THEN** the visible arrow left edge MUST remain in a compact reference-like band rather than drifting back to the previous wide-left-padding look
- **AND** the page MUST avoid horizontal scrolling or clipped titles caused by the placement adjustment.

#### Scenario: Video and non-video arrows feel related
- **WHEN** comparing a normal second-level detail page, a unified search detail-style page, a point-video page with player controls visible, and a point-video empty state
- **THEN** the back arrow glyph geometry MUST be the same
- **AND** the apparent left spacing MUST feel consistent even though the video page places the arrow inside the player frame rather than inside a page header.

### Requirement: Back arrow regression coverage
The student H5 mobile design system SHALL include regression coverage that protects the shared arrow geometry and placement contract.

#### Scenario: Source-level guard prevents drift
- **WHEN** `web-student` regression tests run
- **THEN** they MUST verify that the shared back-arrow module or equivalent shared source is used by PageBar-style detail headers, unified search, and point-video player back controls
- **AND** they MUST catch reintroduction of independent copied SVG strings or direct Lucide-only `ArrowLeft` geometry for the student second-level back affordance.

#### Scenario: Geometry constants are protected
- **WHEN** the shared back-arrow implementation changes
- **THEN** tests or equivalent checks MUST guard the intended `24x24` viewBox, shared filled-outline path, `fill="currentColor"` rendering, and absence of old stroke/line/polyline/polygon-patch arrow construction
- **AND** placement checks MUST guard against restoring the previous excessive video-player left/top offsets or equivalent wide-left-padding behavior.

### Requirement: Mobile composer workbench supports stable action anchoring
The student H5 mobile design system SHALL support a composer workbench layout whose action controls stay fixed while the input zone grows or scrolls.

#### Scenario: Workbench has stable touch targets
- **WHEN** the Atom composer renders on supported phone widths from 360px to 430px CSS pixels
- **THEN** the `+` action and send action MUST each remain reachable by touch inside the composer workbench
- **AND** their hit targets MUST NOT shrink because the textarea content grows
- **AND** the controls MUST maintain clear visual separation from typed text.

#### Scenario: Composer shape transitions without action drift
- **WHEN** the composer changes from compact one-line mode to expanded multi-line mode
- **THEN** the outer composer shape MUST transition from a race-track capsule to a rounded rectangle
- **AND** the `+` action and send action MUST remain visually aligned to the workbench row rather than following the text baseline.

#### Scenario: Compact width owns the expansion boundary
- **WHEN** typed text sits near the one-line boundary
- **THEN** the decision to stay compact or expand MUST use the compact race-track text lane width as the canonical line-capacity measurement
- **AND** changing into the wider expanded layout MUST NOT immediately reclassify that same text as compact.

#### Scenario: Compact measurement mirrors one-row input
- **WHEN** the design system measures compact composer line capacity with a hidden textarea
- **THEN** that measurement element MUST use the same one-row baseline as the visible compact composer input
- **AND** a one-character input MUST NOT make the composer leave compact mode.

#### Scenario: Compact composer text is centered and readable
- **WHEN** the compact Atom composer displays placeholder text or one-line typed text
- **THEN** the text MUST be vertically centered in the race-track lane
- **AND** the text size MUST visually match the left `+` action scale closely enough that both read as one row of the same control surface
- **AND** the same root composer text size MUST continue to be used after expansion or internal scrolling.

#### Scenario: Text area growth is bounded above the workbench
- **WHEN** the composer input zone grows for multi-line text
- **THEN** the growth MUST occur upward from the fixed workbench row
- **AND** the growth MUST preserve the existing effective-panel-height budget for the full root Atom composer
- **AND** once the growth budget is exceeded, only the input zone MUST scroll internally.

#### Scenario: Composer outer height respects the growth budget
- **WHEN** the root Atom composer is expanded or scrollable during normal or keyboard-active layout
- **THEN** the full composer surface, including padding and the fixed workbench row, MUST NOT exceed the configured `61.8%` effective-panel-height budget
- **AND** the input zone MUST receive the remaining height after the workbench row and composer padding are reserved.

### Requirement: Composer workbench coexists with keyboard-aware layout
The student H5 mobile design system SHALL keep the composer workbench usable during soft-keyboard and visible-viewport changes.

#### Scenario: Keyboard-active root composer preserves workbench gap
- **WHEN** the root Atom composer is keyboard-active
- **THEN** the composer bottom edge MUST retain the established breathing gap above the expected keyboard edge
- **AND** the workbench actions MUST remain visible above the keyboard
- **AND** the page MUST NOT expose unrelated raw background bands between the composer and the keyboard area.

#### Scenario: Bottom navigation does not conflict with workbench
- **WHEN** the root Atom composer and bottom navigation are both visible
- **THEN** the composer workbench MUST remain above the bottom navigation top edge
- **AND** the bottom navigation MUST NOT cover the `+` action, send action, or textarea input zone.

#### Scenario: Detail route chrome remains independent
- **WHEN** the contextual Atom chat detail route is open
- **THEN** detail-route chrome and hidden-bottom-navigation behavior MUST remain governed by route-stack rules
- **AND** composer workbench styling MUST NOT force root-route spacing or root-route actions into the detail route.

### Requirement: Composer workbench visual semantics are course-specific
The student H5 mobile design system SHALL present the composer workbench as a course-learning control surface rather than a generic consumer chat toolbar.

#### Scenario: Plus action uses course context semantics
- **WHEN** the workbench displays the `+` action
- **THEN** its accessible label and any visible supporting UI MUST describe injecting or using learning background context
- **AND** it MUST NOT use attachment, upload, media, microphone, or model-selection language.

#### Scenario: Unsupported controls remain absent
- **WHEN** the workbench renders in compact, expanded, scrollable, or loading states
- **THEN** it MUST NOT display unsupported upload, attachment, model-picker, microphone, voice-waveform, image-generation, or external-service controls
- **AND** visual space reserved for possible future controls MUST NOT imply those unsupported actions are currently available.

#### Scenario: Workbench remains visually quiet
- **WHEN** the composer is empty or contains short text
- **THEN** the workbench MUST preserve the calm bottom-weighted Atom root composition
- **AND** the composer MUST NOT become a dense toolbar that competes with the welcome group, history action, new-chat action, or generated follow-up chips.

### Requirement: Chat body text uses one mobile reading scale
The student H5 mobile design system SHALL treat chat body reading and writing text as one typography role.

#### Scenario: Body text scale is shared across chat surfaces
- **WHEN** root composer text, user message body text, assistant message body text, or Markdown paragraph/list body text is displayed
- **THEN** those surfaces MUST use the same mobile chat body font family, size, line-height, weight, and letter spacing
- **AND** the size SHOULD use the existing mobile large text token rather than introducing a one-off midpoint size.

#### Scenario: Non-body text remains separate
- **WHEN** chat headers, welcome text, metadata, badges, progress states, quick prompts, or code snippets render
- **THEN** those elements MUST remain allowed to use distinct typography appropriate to their function.

### Requirement: Mobile overlay headers use veil layers without duplicated backgrounds
The student H5 mobile design system SHALL implement translucent overlay headers by layering a local veil over the real page background instead of duplicating complex page backgrounds inside the header.

#### Scenario: Overlay header needs a soft fade
- **WHEN** a mobile page header needs content behind it to be softened or faded while the foreground title remains readable
- **THEN** the implementation MUST use a separate background veil layer, such as a pseudo-element, behind the header foreground
- **AND** the foreground title, icons, buttons, and hit targets MUST remain fully opaque
- **AND** the design MUST NOT rely on whole-header opacity for this effect.

#### Scenario: Page background contains glows or radial gradients
- **WHEN** the page background contains radial gradients, glow fields, canvas treatments, or other position-sensitive background art
- **THEN** overlay headers MUST NOT duplicate that full background stack inside the header
- **AND** the page-level background MUST remain the single source of truth for position-sensitive art
- **AND** the header veil MUST use a simple translucent tint or linear gradient that does not require pixel-perfect background alignment.

#### Scenario: Veil fallback works without backdrop blur
- **WHEN** a mobile browser or WebView does not support `backdrop-filter` consistently
- **THEN** the header overlay MUST still provide the required fade/readability behavior through the veil's own gradient and opacity stops
- **AND** blur MUST NOT be required for the intended translucency
- **AND** product-specific light chat headers MAY choose an alpha-only veil when sharp underlying content should remain visible through the fade.

#### Scenario: Overlay header respects touch and route scoping
- **WHEN** an overlay header includes interactive controls
- **THEN** those controls MUST keep phone-appropriate hit areas above the veil layer
- **AND** the overlay header selectors MUST be scoped to the intended page or variant so unrelated student pages do not inherit its chrome.

#### Scenario: Overlay header spacing is scoped to scrollable content states
- **WHEN** a mobile page uses an overlay header above content that can be either empty/static or scrollable
- **THEN** header-safe top padding, scroll-padding, or first-content offsets MUST be scoped to the scrollable/content-present state
- **AND** empty or static states MUST NOT inherit scroll-only spacing that creates false scrollbars, pushes centered content downward, or compresses bottom controls
- **AND** the overlay header selector MUST win the cascade over generic foreground-layer selectors that set positioning or stacking.

#### Scenario: Nested mobile scroll surfaces avoid desktop scrollbar chrome
- **WHEN** a mobile chat surface is embedded in a desktop teacher preview or iframe while using an internal scroll container
- **THEN** the internal scroll container SHOULD keep scrolling available without drawing persistent desktop scrollbar chrome over the phone canvas
- **AND** scrollbar hiding MUST be scoped to the intended mobile surface rather than disabling page-level scrolling globally.

### Requirement: Light-theme chat header veils preserve canvas continuity
The student H5 mobile design system SHALL support light-theme chat header veils that preserve a continuous page canvas instead of introducing visible card or strip artifacts.

#### Scenario: Light chat canvas renders behind a header veil
- **WHEN** a light-theme chat canvas uses warm paper, pale yellow-green, or sage-green background tones
- **THEN** the header veil MUST use compatible light translucent stops so the top area reads as the same canvas atmosphere
- **AND** the lower edge of the veil MUST fade out smoothly without creating a visible horizontal strip.

#### Scenario: Protected action groups sit above variable content
- **WHEN** header actions sit above scrollable messages, welcome content, or other variable chat content
- **THEN** those action groups MUST use a compact real-background capsule or equivalent protected surface
- **AND** the protected surface MUST be smaller and more purposeful than a full card-style header
- **AND** it MUST preserve visual alignment with the title row.

#### Scenario: Overlay header is verified on common phone sizes
- **WHEN** mobile viewport QA runs for a page using a translucent chat header veil
- **THEN** QA MUST include 360x780, 390x844, and 430x932 CSS-pixel viewports where practical
- **AND** QA MUST verify that foreground text is readable, action controls are reachable, the veil edge is not a hard strip, and no duplicated-background seam is visible.

### Requirement: Light-theme assistant replies may use flat canvas turns
The student H5 mobile design system SHALL support cardless assistant reply surfaces when the page background itself is the intended reading canvas.

#### Scenario: Assistant reply uses the page canvas as its surface
- **WHEN** a light-theme mobile assistant page intentionally uses a continuous canvas background
- **THEN** successful assistant reply text MAY render directly on that canvas without a card background
- **AND** the page MUST retain enough inline padding, line height, and contrast for long-form reading
- **AND** the cardless treatment MUST NOT depend on duplicating the page background inside the reply block.

#### Scenario: User and assistant authorship remains clear
- **WHEN** a cardless assistant reply appears near a user-authored message
- **THEN** the user-authored message SHOULD remain visually distinct through alignment, color, or bubble treatment
- **AND** the assistant reply SHOULD use typography and action-row placement rather than a card shell to communicate turn boundaries.

#### Scenario: Action rows delimit flat assistant turns
- **WHEN** a cardless assistant reply needs interactive affordances
- **THEN** the reply SHOULD place feedback, copy, more, citation, or similar actions in a lightweight row below the answer body
- **AND** the action row MUST avoid reading as a nested card inside another card
- **AND** the action row MUST preserve phone-appropriate hit areas and accessible names.

#### Scenario: Flat reply surfaces are verified with long content
- **WHEN** mobile viewport QA covers a cardless assistant reply surface
- **THEN** QA MUST include at least one long answer with paragraphs and list items
- **AND** QA MUST check that answer text, action controls, citation affordances, follow-up chips, and bottom composer controls do not overlap or overflow on common phone widths.

### Requirement: Root scroll chrome remains native and performance-safe
The student H5 mobile design system SHALL implement root-page header and navigation quick-return behavior through native page scrolling, passive scroll observation, and thresholded state changes rather than active gesture interception.

#### Scenario: Home feed scroll remains native
- **WHEN** the student scrolls the home video feed on a supported phone browser or WebView
- **THEN** the browser MUST remain the owner of vertical page scrolling
- **AND** header quick-return behavior MUST NOT require active `touchmove` or wheel listeners that call `preventDefault`.

#### Scenario: Header collapse avoids synthetic scroll replay
- **WHEN** home header quick-return behavior is implemented
- **THEN** the implementation MUST NOT use per-gesture synthetic scroll replay, repeated `window.scrollBy` calls, or a title-height progress loop to simulate native scrolling
- **AND** React state updates for the quick-return chrome MUST be thresholded rather than driven by every raw touch delta.

#### Scenario: Unsupported animation APIs do not change behavior
- **WHEN** a mobile browser or WebView does not support CSS Scroll-Driven Animations or similar experimental animation APIs
- **THEN** the home header quick-return behavior MUST still work through the option-2 state-based navigation pattern
- **AND** support for those experimental APIs MUST NOT be required for the home feed to feel scrollable.

#### Scenario: Mobile QA checks root chrome smoothness
- **WHEN** mobile viewport QA runs for this change
- **THEN** QA MUST cover the home root at 360x780, 390x844, and 430x932 CSS-pixel viewports where practical
- **AND** QA MUST verify that downward scroll can compress the home header, upward scroll can restore it, and video feed scrolling remains smooth without visible control overlap.

### Requirement: Compact Atom-centered bottom navigation
The student H5 mobile design system SHALL provide a compact root bottom navigation bar that reserves less vertical space than the previous icon-plus-label bar while keeping fixed-control safe-area protection.

#### Scenario: Compact bottom bar uses shared layout token
- **WHEN** a root route renders the authenticated student bottom navigation
- **THEN** the visible bar height MUST be controlled by the shared mobile bottom-navigation height token
- **AND** the compact token value MUST be shorter than the previous `68px` bar height before safe-area inset is added
- **AND** route-content bottom spacing and root page height formulas MUST continue to derive from that token rather than hardcoded per-page nav heights.

#### Scenario: Ordinary destinations are text-forward
- **WHEN** the bottom navigation renders the non-Atom root destinations
- **THEN** `home`, `learn`, `assessment`, and `profile` MUST render as compact text-forward controls
- **AND** their selected state MUST use a quiet active text treatment without a large filled active background block
- **AND** their labels MUST remain readable and non-overlapping on supported phone widths from `360px` to `430px`.

#### Scenario: Atom destination is the centered branded control
- **WHEN** the bottom navigation renders the `ai` root destination
- **THEN** the Atom destination MUST remain visually centered among the five root entries
- **AND** it MUST render as a rounded rectangular or squircle control containing an Atom icon
- **AND** its inactive state MUST be visually distinct from its active state
- **AND** only the active `ai` root state MUST use the solid product-green control with a white Atom icon
- **AND** the Atom control MUST stay within the bottom navigation bar instead of protruding as a floating action button.

#### Scenario: Compact navigation remains touch and safe-area usable
- **WHEN** the compact bottom navigation is shown in a mobile browser or WebView
- **THEN** every root navigation entry MUST remain reachable by touch
- **AND** the bar MUST account for `env(safe-area-inset-bottom)`
- **AND** focus-visible styling MUST remain available without showing default browser focus boxes during normal pointer use.

#### Scenario: Keyboard and detail-route rules continue to win
- **WHEN** the root Atom composer enters keyboard-active layout
- **THEN** the bottom navigation MUST continue to hide so it does not compete with the composer workbench
- **AND** when any non-tab/detail route is open the bottom navigation MUST remain hidden according to route-stack semantics.

