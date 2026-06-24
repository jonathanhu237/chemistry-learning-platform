# student-h5-learning-catalog Specification

## Purpose
Define the student H5 learning catalog browser from periodic-table area selection through family/chapter catalog browsing, breadcrumb chips, directory navigation, catalog search entry, and catalog row/end-marker behavior.
## Requirements
### Requirement: Family page renders as catalog browser shell
The student H5 family/chapter page SHALL render as a family-scoped catalog browser shell that keeps compact element context above the catalog body.

#### Scenario: Student opens a family chapter
- **WHEN** a student opens a selected family or chapter route such as `halogens-17`
- **THEN** the page MUST show the selected family title and a compact element context header
- **AND** the page MUST show the chapter catalog tree as the primary body content below that header
- **AND** the catalog body MUST be discoverable within the first phone viewport without requiring the student to scroll past a large element detail card
- **AND** the compact element context header MUST NOT repeat the detail page title already shown by the page bar
- **AND** the root chapter catalog body MUST NOT repeat the chapter/family title as a second large heading below the element context
- **AND** the page MUST NOT split the experience into separate `性质` and `目录` tabs.

#### Scenario: Student switches selected element
- **WHEN** the student selects another element from the family element rail
- **THEN** the compact context header MUST update the selected element symbol, label, focus copy, relevance copy, and tags
- **AND** the current family/chapter catalog body MUST remain unchanged
- **AND** the app MUST NOT navigate away from the family catalog shell.

#### Scenario: Student opens element detail
- **WHEN** the student taps the compact element detail affordance
- **THEN** the app MUST open the existing element detail route for the selected profile and element
- **AND** returning MUST restore the family catalog shell with the same selected family context where browser history allows.

### Requirement: Family catalog uses a lower directory workspace
The student H5 family catalog shell SHALL visually separate the chapter learning catalog into a lower workspace without making the directory list feel like a nested card.

#### Scenario: Student views the family catalog body
- **WHEN** the family catalog shell renders the chapter or directory body
- **THEN** the catalog body MUST appear as a distinct lower section from the element context above
- **AND** the section MUST present itself as a compact catalog-browser workspace rather than a duplicate large chapter heading
- **AND** catalog entries MUST render as flat browser rows directly on the lower background rather than inside a rounded list card
- **AND** each catalog entry in the family shell MUST use a single-line row with a node-type icon, a protected one-line ellipsized title, and a trailing affordance on the same baseline
- **AND** family-shell catalog rows MUST NOT show repeated summaries, progress captions, or secondary meta text such as continue-learning labels
- **AND** catalog entries SHOULD avoid repeated floating cards.

#### Scenario: Grid background remains subordinate to reading
- **WHEN** the lower catalog workspace is visible over the global periodic-grid app background
- **THEN** the lower workspace SHOULD soften the grid enough that row titles and icons remain the primary reading layer
- **AND** the background treatment MUST stay scoped to the family catalog shell rather than removing the global student H5 background identity.

#### Scenario: Student scrolls the catalog directory
- **WHEN** the family catalog shell is open on a phone viewport
- **THEN** the overall page MUST remain fixed within the viewport
- **AND** the upper element context MUST remain visible without participating in document scrolling
- **AND** only the catalog row list inside the lower sheet MUST scroll vertically
- **AND** the lower sheet MUST NOT add a fixed bottom search field or any fixed footer overlay that covers catalog rows
- **AND** the lower sheet MUST allocate real remaining height to the row-list viewport through explicit `min-height: 0` / `1fr` ancestors.

#### Scenario: Student reaches the catalog end marker
- **WHEN** the current catalog layer has visible directory or point entries
- **THEN** the row list MUST render an end marker as list content rather than as `fixed`, `absolute`, or `sticky` chrome
- **AND** the marker MUST summarize only non-zero counts for the current visible layer, using `目录` for directory nodes and `实验` for point nodes
- **AND** point-node counts MUST be independent of whether a real media file has been uploaded
- **AND** the marker MUST not render when both visible counts are zero
- **AND** a short non-scrollable row list MUST place the marker at the bottom of the row-list viewport
- **AND** a long scrollable row list MUST show the marker only after the student scrolls to the end.

#### Scenario: Student opens catalog search
- **WHEN** the student taps the catalog browser search tool
- **THEN** the app MUST open the unified search page with the current profile, chapter, selected element, source node, and catalog path context where available
- **AND** the family catalog shell MUST NOT render an inline bottom search input for current-layer filtering.

### Requirement: Family context collapses during catalog browsing
The student H5 family catalog shell SHALL support an expanded context header that collapses into a slim sticky element rail during catalog scrolling.

#### Scenario: Family page opens at top
- **WHEN** the family catalog shell is first rendered near the top of the page
- **THEN** the expanded header MUST show the family identity, mini element rail, selected element focus copy, and compact tags
- **AND** the mini element rail MUST show at most five visible tiles before horizontal overflow scrolling
- **AND** the selected element summary MUST use an inline `元素详情` affordance rather than a full-width CTA
- **AND** the expanded header MUST remain short enough that catalog entries are visible early in the first phone viewport.

#### Scenario: Student scrolls into catalog body
- **WHEN** the student scrolls the catalog body past the collapse threshold
- **THEN** the family context MUST collapse into a slim sticky header that preserves the selected family and selected element identity
- **AND** the slim header MUST keep the element rail or equivalent element selector reachable
- **AND** the slim header MUST NOT obscure the catalog list more than one compact control row.

#### Scenario: Student scrolls back to top
- **WHEN** the student scrolls back above the collapse threshold
- **THEN** the expanded header MUST return without losing selected element state
- **AND** the transition MUST feel immediate and stable rather than delayed or automatic after an idle timer.

### Requirement: Directory browsing preserves family shell
The student H5 family catalog shell SHALL preserve the selected family context while the student browses child catalog directories for the same chapter.

#### Scenario: Student opens a child directory
- **WHEN** a student taps a directory card from the family catalog shell
- **THEN** the lower catalog browser MUST load the selected directory's child catalog entries in place
- **AND** the page MUST keep the same family context header and selected element rail above the directory body
- **AND** the app MUST NOT navigate to a `/catalog/...` page for in-family directory browsing
- **AND** the header MUST NOT be replaced by a directory-only page when the route has selected profile context
- **AND** the lower catalog browser MUST expose the learning scope as a first-row root chip with search and more tools
- **AND** nested directory ancestry MUST appear as horizontally scrollable breadcrumb chips on a second row
- **AND** ancestor chips MUST be tappable for direct directory jumps instead of exposing a separate `up one level` control
- **AND** `more` MUST open a bottom sheet without requiring a visible close button.

#### Scenario: Student opens a point
- **WHEN** a student taps a point node from the chapter root or any child directory inside the family shell
- **THEN** the app MUST open the existing point detail route
- **AND** the point route MUST retain available profile, chapter, source node, path, and selected element context in search parameters where available.

#### Scenario: Directory URL has no family context
- **WHEN** a catalog directory route is opened directly without a selected profile context
- **THEN** the app MAY render the existing plain directory page
- **AND** the page MUST remain usable and MUST NOT crash because the family shell cannot be resolved.

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

### Requirement: Experiment-point primary task area
The student H5 element learning page SHALL keep catalog point navigation as the primary learning task after compact chemistry context.

#### Scenario: Student reaches catalog points
- **WHEN** a selected family or chapter has published catalog nodes
- **THEN** the page MUST show top-level directory and point entries for that chapter
- **AND** selecting a directory MUST open the next catalog level
- **AND** selecting a point MUST open the point detail learning page.

#### Scenario: Directory card appears in task area
- **WHEN** a directory node is shown in the catalog task area
- **THEN** it MUST render as a navigation category card using derived directory card presentation
- **AND** it MUST NOT appear as a playable video point
- **AND** it MUST NOT require manual directory description, card image, icon, accent, or layout fields.

#### Scenario: Context area would push catalog too low
- **WHEN** selected-element facts and family common properties contain more content than fits comfortably before the catalog entry area on a phone viewport
- **THEN** the page MUST prioritize compact summaries, expandable detail, or equivalent progressive disclosure
- **AND** it MUST keep the catalog task area discoverable without requiring excessive scrolling.

### Requirement: Catalog-first chapter learning composition
The student H5 chapter learning page SHALL support the prototype's selected-chapter flow and MUST NOT require a fixed two-mode chapter contract when the authored catalog is the primary navigation.

#### Scenario: Student opens a selected chapter
- **WHEN** a student opens a selected family or chapter page from the periodic-table entry
- **THEN** the page MUST show the selected chapter context and a clear entry into its catalog tree
- **AND** the catalog tree MUST be available without assuming a fixed local mode switch.

#### Scenario: Student navigates catalog depth
- **WHEN** a student opens a catalog directory from the chapter page
- **THEN** the app MUST render a catalog page for that node with breadcrumbs or equivalent source context
- **AND** returning MUST restore the previous chapter or directory page.

#### Scenario: Facts content remains available
- **WHEN** the profile has facts, common properties, or element context
- **THEN** the page MAY show them as compact chapter context
- **AND** these facts MUST NOT replace the catalog as the path to point video/detail learning.

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, separate recommended guidance, selected-area route navigation, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as separate guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the recommendation MUST be shown through a separate smart recommendation card on the learning root
- **AND** the periodic-table area controls and element cells MUST remain pure selection affordances
- **AND** the recommendation MUST NOT render as a selected, active, current chapter, inline chapter list, area badge, or element-cell gold outline before the student opens a detail route.

#### Scenario: Student opens a selected area
- **WHEN** the student taps an area control or an element cell from the periodic-table learning root
- **THEN** the H5 app MUST navigate to a selected-area second-level route for that area
- **AND** the learning root MUST NOT render the selected area's chapter list inline
- **AND** the selected area MAY be visually distinguishable as navigation feedback without turning the root into a list page or recommendation surface.

#### Scenario: Student views selected-area chapter list
- **WHEN** the selected-area route is open
- **THEN** the page title MUST be the selected area label such as `p区元素`
- **AND** the page body MUST show only the chapter list filtered to that area
- **AND** the page body MUST NOT repeat a `当前选区` header, count badge, recommendation badge, or separate recommendation card
- **AND** the bottom navigation MUST remain hidden because the selected-area route is a detail route.

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card from the selected-area route
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page.

#### Scenario: Learning root periodic table is pure navigation
- **WHEN** the learning root periodic-table entry is rendered
- **THEN** all visible element cells MUST show their element symbol without requiring a selected area or matching profile symbol
- **AND** area legend buttons and element cells MUST NOT render a default selected, muted, learnable, or focused visual state
- **AND** tapping an area legend button or element cell MUST navigate to the corresponding area route.

#### Scenario: Hydrogen is its own student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** the hydrogen cell MUST map to a dedicated `氢元素` learning area route
- **AND** the selected-area page MUST show matching learning profiles such as CH22 where hydrogen is taught
- **AND** the student entry MUST NOT expose `氢与稀有气体` as a combined area.

#### Scenario: Noble gases are shown through p area
- **WHEN** the student uses the periodic-table entry
- **THEN** group 18 noble-gas cells MUST map to `p区元素`
- **AND** selecting a noble-gas cell MUST open the p-area selected-area route
- **AND** the CH22 learning profile MUST include He, Ne, Ar, Kr, Xe, Rn, and Og so the p-area noble-gas column does not render blank cells
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to p or hydrogen.

#### Scenario: f area is open to students
- **WHEN** the student uses the periodic-table entry
- **THEN** the `f区元素` area MUST be available when the CH21 student learning profile exists
- **AND** selecting an f-block cell MUST open the f selected-area route
- **AND** the selected-area page MUST show the CH21 f-block chapter entry.

### Requirement: Prototype-aligned multi-level catalog flow
The student H5 app SHALL implement the prototype flow from periodic-table entry to selected area popover to chapter to catalog directories to point video/detail.

#### Scenario: Student enters from periodic table
- **WHEN** a student taps an area control or element cell from the periodic-table learning entry
- **THEN** the app MUST open that area's chapter choices in an anchored popover on the learning root
- **AND** the popover MUST make the area identity clear before showing chapter entries.

#### Scenario: Student enters chapter from selected area
- **WHEN** a student taps a chapter/family entry from the selected-area popover or fallback page
- **THEN** the app MUST navigate to that chapter's standalone page
- **AND** the page MUST make the chapter identity clear before showing catalog entries.

#### Scenario: Student opens nested directory
- **WHEN** a student taps a directory catalog node
- **THEN** the app MUST open a second-level route for that directory
- **AND** the page MUST show child directory and point entries according to the authored order.

#### Scenario: Student opens concrete point video
- **WHEN** a student taps a point catalog node
- **THEN** the app MUST open the point video/detail page
- **AND** the page MUST show manually authored principle, phenomenon explanation, safety note, related links, and the fixed test handoff
- **AND** teacher-only remarks MUST remain hidden from this page.

#### Scenario: Directory search context leads to points
- **WHEN** a student search result is matched through directory/category text
- **THEN** the result list MUST show concrete descendant point entries
- **AND** selecting a result MUST open point detail rather than a directory-only search result page.

### Requirement: Student catalog cards ignore removed card overrides
The student H5 catalog SHALL render directory and point cards without relying on removed manual card-presentation fields.

#### Scenario: Removed fields are absent from API payload
- **WHEN** a student catalog response omits `student_description`, `card_image_asset_id`, `card_icon_key`, `card_accent`, `card_layout`, `card_presentation`, and `point_card_presentation`
- **THEN** the student H5 catalog MUST still render directory and point cards successfully
- **AND** no runtime error or blank card MUST occur because those fields are absent.

#### Scenario: Point learning summary is available
- **WHEN** a point has learning content such as principle, phenomenon explanation, or safety note
- **THEN** the point card MAY show a concise derived summary from that content
- **AND** the summary MUST be treated as a display projection rather than an editable card override.

#### Scenario: Point learning summary is missing
- **WHEN** a point has no available learning summary yet
- **THEN** the point card MUST still show the point title and stable point/video affordance
- **AND** it MUST not require teacher-authored short card description.

#### Scenario: Bound video thumbnail is available
- **WHEN** a point has a bound video thumbnail available to students
- **THEN** the point card MAY use that thumbnail as the visual cue
- **AND** it MUST fall back to a stable default if no thumbnail is available.

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

### Requirement: Learning root separates periodic selection from smart recommendation
The student H5 learning root SHALL present the periodic table as the primary chapter-selection tool and show recommendation guidance as a separate smart card below it.

#### Scenario: Student opens learning root
- **WHEN** a student opens the `学习` root
- **THEN** the upper learning area MUST render a periodic-table selection card focused on area and element selection
- **AND** the lower learning area MUST render a smart recommendation or continue-learning card when a recommended profile exists
- **AND** the lower card MUST provide a clear action to enter the recommended chapter or area.
- **AND** the periodic-table selector MUST NOT default to a selected area, selected element, or recommendation-derived focus state.

#### Scenario: Recommendation does not decorate the periodic table
- **WHEN** the learning root has a recommended profile
- **THEN** the periodic-table legend MUST NOT show yellow recommendation badges
- **AND** periodic-table element cells MUST NOT show gold recommendation outlines
- **AND** recommendation text such as `推荐学习` MUST live in the separate smart recommendation card rather than inside the periodic-table selector.

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning root that hands off to a selected-area detail page, which then hands off to one current family or chapter learning detail page.

#### Scenario: Student chooses an area from the periodic table
- **WHEN** a student selects an area control or periodic-table element cell from the learning root
- **THEN** the H5 app MUST open the matching selected-area route as a second-level detail page
- **AND** the bottom navigation MUST be hidden while the selected-area detail route is visible
- **AND** the selected-area page MUST show the chapter entries for that area.

#### Scenario: Student chooses hydrogen
- **WHEN** a student selects the hydrogen area or H element cell from the learning root
- **THEN** the H5 app MUST open the hydrogen selected-area route
- **AND** the selected-area page MUST include CH22 as the hydrogen learning context
- **AND** the route MUST NOT use the removed combined `氢与稀有气体` area id.

#### Scenario: Student chooses a noble gas
- **WHEN** a student selects He, Ne, Ar, Kr, Xe, Rn, or Og from the learning root
- **THEN** the H5 app MUST open the p-area selected-area route
- **AND** CH22 MUST remain reachable from that p-area context for noble-gas learning
- **AND** the noble-gas selection MUST NOT navigate to the hydrogen selected-area route.

#### Scenario: Student chooses f area
- **WHEN** a student selects the f area or an f-block element from the learning root
- **THEN** the H5 app MUST open the f selected-area route
- **AND** the selected-area page MUST show the CH21 chapter entry when the CH21 profile is enabled
- **AND** returning from a CH21 chapter detail MUST restore the f selected-area route where browser history allows.

#### Scenario: Student chooses a family from the selected-area page
- **WHEN** a student selects a family, group, or chapter entry from the selected-area detail page
- **THEN** the H5 app MUST open the corresponding current family or chapter as a second-level chapter learning route
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the bottom navigation MUST remain hidden while the chapter learning detail route is visible
- **AND** returning from the chapter detail route MUST restore the selected-area route where browser history allows.

#### Scenario: Existing recommendation is used as fallback
- **WHEN** a student reaches learning without choosing a family, chapter, or area explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as separate recommendation guidance on the learning root only
- **AND** the selected-area page MUST remain a plain area title and chapter-list handoff surface without recommendation chrome
- **AND** the H5 app MUST render that resolved profile as a current chapter detail page only when a detail route is opened
- **AND** the learning root MUST remain a periodic-table entry surface rather than a selected-area chapter list or a hidden default detail page.

### Requirement: Family catalog navigation keeps context
The student H5 learning flow SHALL keep the selected family/chapter context while navigating catalog directories within that chapter.

#### Scenario: Student opens a root catalog directory
- **WHEN** a student opens a directory from a selected family/chapter page
- **THEN** the app MUST navigate to the directory content while preserving selected profile and chapter context
- **AND** the visible page MUST remain a family catalog shell with the same compact element context header
- **AND** the catalog body MUST update to the selected directory's child entries.

#### Scenario: Student navigates deeper directories
- **WHEN** a student opens a nested directory from another directory inside the family catalog shell
- **THEN** the app MUST preserve the same selected profile context
- **AND** the header MUST continue to represent the original family/chapter rather than the current directory title alone
- **AND** breadcrumbs or path text MAY appear in the catalog body to show the current directory position.

#### Scenario: Student returns through history
- **WHEN** the student returns from a nested directory route
- **THEN** browser or WebView history MUST restore the previous catalog level where possible
- **AND** the selected family context and selected element state SHOULD remain stable when route state allows.

### Requirement: Chapter catalog header uses two-line breadcrumb navigation
The student H5 learning flow SHALL render chapter catalog orientation as a two-line mobile breadcrumb rail where the root learning scope remains fixed above horizontally scrollable child directory breadcrumbs.

#### Scenario: Root catalog displays fixed learning scope and tools
- **WHEN** a student views the root of a family/chapter catalog
- **THEN** the catalog header MUST display the current learning scope as the first-row root chip
- **AND** it MUST display `搜索` and `更多` actions in the first-row action cluster
- **AND** it MUST NOT display `章节学习目录` or `章节学习目录下` as a visible header label
- **AND** it MUST NOT display an `上一级` action
- **AND** it MUST NOT render a child breadcrumb row when the student is already at the catalog root.

#### Scenario: Nested catalog displays child breadcrumb rail
- **WHEN** a student navigates from the catalog root into one or more directory nodes
- **THEN** the first row MUST keep the root learning scope chip separate from the child path
- **AND** the second row MUST render child directory chips from left to right in ancestor-to-current order
- **AND** the current directory MUST be the rightmost chip and MUST use selected styling
- **AND** each non-current ancestor chip MUST be tappable and navigate directly to that directory
- **AND** the root chip MUST be tappable and navigate directly to the catalog root.

#### Scenario: Breadcrumb chips preserve full text
- **WHEN** a directory name or learning scope name is longer than the available row width
- **THEN** the breadcrumb chip MUST retain its full natural text width
- **AND** the breadcrumb rail MUST handle overflow with horizontal scrolling
- **AND** the chip text MUST NOT be protected by `max-width`, ellipsis, or clipping.

#### Scenario: Search results emphasize direct parent directory
- **WHEN** a student searches chapter catalog content and receives matching directory or point results
- **THEN** each result MUST show the matching item title as primary text
- **AND** it MUST show the direct parent directory as primary path metadata
- **AND** any ancestor chain MUST be secondary, weak metadata
- **AND** the secondary ancestor chain MUST NOT include the result title as part of a long full-path string.
