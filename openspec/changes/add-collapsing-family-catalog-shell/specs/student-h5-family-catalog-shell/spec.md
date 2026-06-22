## ADDED Requirements

### Requirement: Family page renders as catalog browser shell
The student H5 family/chapter page SHALL render as a family-scoped catalog browser shell that keeps compact element context above the catalog body.

#### Scenario: Student opens a family chapter
- **WHEN** a student opens a selected family or chapter route such as `halogens-17`
- **THEN** the page MUST show the selected family title and a compact element context header
- **AND** the page MUST show the chapter catalog tree as the primary body content below that header
- **AND** the catalog body MUST be discoverable within the first phone viewport without requiring the student to scroll past a large element detail card
- **AND** the compact element context header MUST NOT repeat the detail page title already shown by the page bar
- **AND** the root chapter catalog body MUST NOT repeat the chapter/family title as a second large heading below the element context
- **AND** the page MUST NOT split the experience into separate `元素` and `目录` tabs.

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
- **AND** the section MUST present itself as `章节学习目录`
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
- **AND** the lower sheet search field MUST remain pinned to the bottom of the fixed page
- **AND** the search field MUST use a full-width bottom bar treatment comparable to mobile bottom navigation, with the input fully visible above the safe area.

#### Scenario: Student searches current catalog layer
- **WHEN** the student enters text in the lower sheet search field
- **THEN** the currently visible catalog rows MUST filter by available title, summary, meta, or path text
- **AND** the search MUST NOT navigate away or change the selected element context
- **AND** an empty result state MUST be shown when no visible entries match.

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
- **AND** the lower catalog browser MUST expose the current path under the chapter-learning-catalog label
- **AND** the lower catalog browser MUST provide compact `up one level` and `more` controls, with `more` opening a bottom sheet.

#### Scenario: Student opens a point
- **WHEN** a student taps a point node from the chapter root or any child directory inside the family shell
- **THEN** the app MUST open the existing point detail route
- **AND** the point route MUST retain available profile, chapter, source node, path, and selected element context in search parameters where available.

#### Scenario: Directory URL has no family context
- **WHEN** a catalog directory route is opened directly without a selected profile context
- **THEN** the app MAY render the existing plain directory page
- **AND** the page MUST remain usable and MUST NOT crash because the family shell cannot be resolved.
