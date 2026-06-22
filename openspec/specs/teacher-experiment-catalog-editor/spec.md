# teacher-experiment-catalog-editor Specification

## Purpose
TBD - created by archiving change experiment-catalog-tree-point-architecture. Update Purpose after archive.
## Requirements
### Requirement: Point content autosaves like an online document
The teacher catalog editor SHALL autosave routine point and directory content edits while clearly separating save state from downstream ES/RAG sync state.

#### Scenario: Teacher edits point content
- **WHEN** a teacher changes point title, teaching note, principle mode, reaction equations, text principle, phenomenon explanation, or safety note
- **THEN** the editor MUST autosave the changed content without requiring a persistent `保存点位内容` button
- **AND** the visible save indicator MUST describe backend persistence using states such as `正在保存`, `已保存`, and `保存失败`.

#### Scenario: Teacher edits directory content
- **WHEN** a teacher changes a directory title or teaching note
- **THEN** the editor MUST autosave the changed directory content without requiring a persistent `保存目录内容` button
- **AND** the directory title editing interaction MUST keep the teacher in context rather than opening a separate title-edit window for routine inline edits.

#### Scenario: Autosave succeeds before downstream sync completes
- **WHEN** content is saved to the backend but ES or RAG has not yet consumed the change
- **THEN** the editor MUST still show the content save state as saved
- **AND** ES/RAG status MUST remain in diagnostics or secondary status surfaces rather than being represented as an unsaved content state.

#### Scenario: Autosave fails
- **WHEN** an autosave request fails validation or network persistence
- **THEN** the editor MUST show a save failure state near the edited content
- **AND** it MUST keep the teacher's current unsaved input available for correction or retry.

### Requirement: Autosave copy explains delayed search consumption
The teacher catalog editor SHALL explain that autosaved content and student search consumption are separate lifecycle states.

#### Scenario: Teacher views autosave help or sync diagnostics
- **WHEN** the editor shows helper copy, status details, or diagnostics for autosaved point content
- **THEN** the copy MUST say that routine edits are saved first and then consumed by ES/RAG asynchronously
- **AND** it MUST state the expected ES timing policy: normally after about 30 seconds without further edits, and at least once within about 3 minutes during continuous editing.

#### Scenario: Teacher views a published point after editing
- **WHEN** a published point has saved content changes that have not yet been consumed by ES/RAG
- **THEN** the editor MUST keep the point's publication status visually separate from sync status
- **AND** it MUST NOT imply that the point is unpublished, draft-only, missing video, or missing learning content merely because downstream sync is pending.

#### Scenario: Teacher opens retrieval diagnostics
- **WHEN** the teacher opens point diagnostics from the editor
- **THEN** the diagnostics surface MUST show ES and RAG states as downstream consumption states such as `已同步`, `待同步`, `同步中`, or `失败`
- **AND** it MUST not reuse the content autosave labels as if they were ES/RAG execution results.

### Requirement: Current video card shows left-aligned playback metadata
The teacher catalog editor SHALL present the current bound-video card like a mature video product: playable thumbnail first, then left-aligned title and student playback metadata beside it.

#### Scenario: Point has a bound ready video
- **WHEN** a teacher opens the video tab for a point with an active ready video binding
- **THEN** the current-video card MUST show the playable thumbnail on the left
- **AND** it MUST show exactly one prominent title block to the right of the thumbnail
- **AND** the title block MUST be left-aligned rather than horizontally centered in the empty right side
- **AND** the metadata under the title MUST include student playback file size when available
- **AND** the metadata MUST include upload time formatted to seconds, such as `2026-06-22 14:31:09`.

#### Scenario: Detailed playback facts are available
- **WHEN** the current binding payload includes bitrate, frame rate, codec, mime type, duration, or source-size comparison fields
- **THEN** the current-video card SHOULD show those facts as a compact one-property-per-line details list
- **AND** those facts MUST remain visually subordinate to the video title
- **AND** they MUST NOT duplicate the title or present the original file name as a second title.

#### Scenario: Playback resolution is available
- **WHEN** the current binding payload includes playback width and height
- **THEN** the current-video metadata MUST include the student playback resolution
- **AND** it MUST display the resolution as a compact fact near the playback size and upload time.

#### Scenario: Playback metadata is incomplete
- **WHEN** the current binding payload lacks playback size or resolution
- **THEN** the current-video card MUST omit only the missing fact or show a neutral pending-size message
- **AND** it MUST NOT show the original file name as a duplicate title line
- **AND** it MUST NOT imply that source size is the student playback size.

#### Scenario: Teacher manages the current binding
- **WHEN** the teacher needs to replace or remove the bound video
- **THEN** replace and remove actions MUST remain visually secondary
- **AND** the actions MUST stay anchored to the lower-right of the current-video information area without disturbing the title and metadata layout.

### Requirement: Left tree and right editor workspace
The teacher admin console SHALL provide a catalog authoring workspace with a navigable tree on the left and the selected node editor on the right.

#### Scenario: Teacher opens catalog management
- **WHEN** a teacher opens experiment catalog management
- **THEN** the page MUST show chapter selection and a tree of catalog nodes for the selected chapter
- **AND** selecting a node MUST open its editor without leaving the workspace.

#### Scenario: Teacher searches the tree
- **WHEN** a teacher searches by node title, alias, reagent, point text, teacher note, or legacy code
- **THEN** the workspace MUST show matching nodes in a search overlay anchored to the tree search input
- **AND** the overlay MUST provide enough breadcrumb or ancestor context for each result
- **AND** the overlay MUST NOT push the catalog tree downward or become a second in-flow tree.

#### Scenario: Teacher selects a search result
- **WHEN** a teacher selects a result from the search overlay
- **THEN** the workspace MUST reveal the matching node in the existing catalog tree with enough ancestors expanded to preserve context
- **AND** selecting the result MUST focus the matching node in the editor.

#### Scenario: Search overlay is dismissed
- **WHEN** the teacher clears the query, changes chapter, presses Escape, clicks outside the overlay, or selects a result
- **THEN** the search overlay MUST close or reset appropriately
- **AND** the underlying tree layout, scroll container, and selected editor state MUST remain stable.

### Requirement: In-context tree editing
The teacher catalog tree SHALL support fast in-context creation, movement, ordering, and cleanup of directory and point nodes.

#### Scenario: Teacher adds a child node
- **WHEN** a teacher adds a child under a selected directory node
- **THEN** the system MUST create the node under that parent with server-controlled identity
- **AND** the teacher MUST be able to choose whether the new child is a directory or point.

#### Scenario: Teacher attempts to add under a point
- **WHEN** a teacher attempts to add a child under a point node
- **THEN** the editor MUST prevent or reject the operation
- **AND** the UI MUST make clear that point nodes are learning leaves.

#### Scenario: Teacher reorders nodes
- **WHEN** a teacher drags a node within the same parent or uses an accessible fallback reorder action
- **THEN** the system MUST persist display order
- **AND** sibling order MUST remain stable after refresh.

#### Scenario: Teacher moves a node
- **WHEN** a teacher moves a node to another directory parent
- **THEN** the system MUST validate that the move does not create a cycle and does not place children under a point
- **AND** all point identities and bindings under the moved subtree MUST remain stable.

#### Scenario: Teacher archives a node
- **WHEN** a teacher archives a node
- **THEN** the system MUST hide it from normal student catalog responses
- **AND** it MUST preserve historical data and allow teacher-side recovery or audit according to admin rules.

### Requirement: Node editor tabs follow node capability
The right editor SHALL show primary authoring panels based on whether the selected node is a directory or point, and SHALL keep read-only diagnostics out of the primary configuration tab strip.

#### Scenario: Directory node is selected
- **WHEN** a directory node is selected
- **THEN** the editor MUST show a direct `目录信息` authoring surface without a tab selector
- **AND** the directory surface MUST explain that directories provide student navigation and classification, and do not own point knowledge content or video binding
- **AND** directory title editing MUST remain in the selected-node header instead of appearing as a duplicate content-body field
- **AND** the directory primary surface MUST focus on teacher-only teaching note where applicable
- **AND** it MUST NOT show point principle, video binding, related point links, assessment, search-document controls, node status diagnostics, AI context diagnostics, advanced debug controls, or student-card presentation controls as primary tabs.

#### Scenario: Point node is selected
- **WHEN** a point node is selected
- **THEN** the editor MUST show exactly the primary configuration tabs `知识内容`, `实验视频`, and `相关实验`
- **AND** those tabs MUST respectively own point knowledge content, the one experiment-video binding, and the ordered related-experiment learning list
- **AND** the editor MUST NOT show `学生卡片`, `节点状态`, `AI 上下文`, or `高级` as primary configuration tabs.

#### Scenario: Removed node type is selected
- **WHEN** stale data or a stale client references a hybrid or shortcut node
- **THEN** the editor MUST render a controlled migration/unavailable state or normalized directory/point editor
- **AND** it MUST NOT expose hybrid or shortcut editing controls.

### Requirement: Teacher-authored point content form
The editor SHALL let teachers maintain point content without AI generation.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits a point node
- **THEN** the form MUST provide fields for point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related point links, bound videos, and publication state.
- **AND** the teacher-only note MUST be visually and technically separated from student-facing point knowledge.

#### Scenario: Teacher edits teacher-only note
- **WHEN** a teacher enters remarks, non-experiment knowledge, operational comments, or authoring hints in the teacher-only note field
- **THEN** the editor MUST save the note for teacher/admin reuse
- **AND** the editor MUST indicate that this note is not shown to students and is not part of student video-library search.

#### Scenario: Teacher saves draft content
- **WHEN** required publish fields are incomplete
- **THEN** the system MUST allow draft save
- **AND** it MUST show validation messages explaining what is missing before publication.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes point content
- **THEN** the system MUST validate required fields, update student visibility, and queue search indexing.
- **AND** queued search indexing MUST use student-facing point title and point knowledge rather than the teacher-only note.

### Requirement: Video binding inside node editor
The editor SHALL bind existing videos to point nodes from within the selected node workspace.

#### Scenario: Teacher binds existing video
- **WHEN** a teacher selects an existing media asset for a point node
- **THEN** the system MUST create a point-node media binding
- **AND** the asset MUST become eligible for student display only through that point binding and publication rules.

#### Scenario: Teacher needs to upload a new video
- **WHEN** a teacher needs media that is not yet in the media library
- **THEN** the catalog editor MUST direct the teacher to the media/video upload page or workflow
- **AND** it MUST NOT include local file upload controls or create new media assets inside the catalog editor.

#### Scenario: Teacher manages an existing binding
- **WHEN** a teacher publishes, unpublishes, previews, or removes a point-node media binding
- **THEN** the editor MUST update only the binding state
- **AND** it MUST NOT alter the underlying media asset upload lifecycle.

### Requirement: Publication and validation are explicit
The teacher catalog editor SHALL separate draft editing from student-visible publication.

#### Scenario: Teacher reviews validation
- **WHEN** a teacher selects a node or subtree
- **THEN** the editor MUST show validation status for required title, directory card fields, point content, video binding status where relevant, related links, and search-index readiness.

#### Scenario: Teacher publishes a subtree
- **WHEN** a teacher publishes a directory subtree
- **THEN** the system MUST publish eligible child directory and point nodes according to explicit teacher action
- **AND** it MUST report any nodes skipped because they are incomplete.

### Requirement: Engineering boundaries for catalog editor
The teacher catalog editor SHALL follow the established admin frontend architecture.

#### Scenario: Developer updates catalog editor
- **WHEN** a developer changes the catalog tree, node editor, point content form, video binding panel, or search preview
- **THEN** the code MUST live in feature-scoped modules under the catalog/experiments feature
- **AND** shared API calls MUST be owned by domain API client modules rather than a monolithic API barrel.

### Requirement: Natural equation editor in point content form
The teacher catalog editor SHALL use a natural multiline equation editor as the default UI for point content whose principle mode is chemical equation.

#### Scenario: Teacher opens equation principle mode
- **WHEN** a teacher selects chemical equation principle mode
- **THEN** the editor MUST show one primary multiline input for reaction equations
- **AND** the editor MUST explain in Chinese that each non-empty line is treated as one reaction.

#### Scenario: Teacher types naturally
- **WHEN** a teacher types or pastes reaction text such as `CL2+H2=HCL` or `Cl2 + 2KBr -> 2KCl + Br2`
- **THEN** the editor MUST keep focus in the text input
- **AND** it MUST show backend preview feedback without requiring the teacher to click common-symbol controls.

#### Scenario: Teacher has multiple reactions
- **WHEN** the point requires multiple reaction equations
- **THEN** the teacher MUST be able to enter them as separate lines in the same input
- **AND** the UI MUST show corresponding preview results in the same line order.

#### Scenario: Preview results are shown
- **WHEN** backend preview returns normalized or suggested equations
- **THEN** the editor MUST show a compact "系统理解为" preview area below the text input
- **AND** it MUST include correction warnings, balance suggestions, and invalid-line explanations in Chinese.

#### Scenario: Teacher accepts a suggestion
- **WHEN** the preview presents a corrected or balanced candidate
- **THEN** the editor MUST provide an explicit "采用" action
- **AND** accepting the suggestion MUST update the multiline input so the teacher remains in control of the saved raw text.

#### Scenario: Common symbols are available
- **WHEN** the editor offers chemistry symbols or snippets
- **THEN** those controls MUST be secondary to keyboard input
- **AND** they MUST NOT appear as the main interaction model for authoring equations.

#### Scenario: AI assistance is available
- **WHEN** AI equation assistance is configured and healthy
- **THEN** the editor MAY show explicit actions such as "AI 修正" or "AI 生成反应式"
- **AND** AI candidates MUST be shown as drafts requiring teacher acceptance before insertion.

#### Scenario: AI assistance is unavailable
- **WHEN** AI equation assistance is unavailable
- **THEN** the editor MUST still support natural input, deterministic preview, save, and publication validation
- **AND** it MUST NOT make AI a required step for equation authoring.

#### Scenario: Existing saved equations are loaded
- **WHEN** a point with existing reaction equation rows is opened
- **THEN** the editor MUST hydrate the multiline input from stored raw equation rows in display order
- **AND** the backend-normalized records MUST remain available for preview, save, AI, ES, and RAG consumers.

### Requirement: Teacher-friendly equation authoring surface
The teacher catalog editor SHALL present reaction equation authoring as a Chinese, card-based input and preview workflow for point-capable nodes whose principle mode is equation.

#### Scenario: Teacher opens equation principle mode
- **WHEN** a teacher selects equation principle mode for a point-capable catalog node
- **THEN** the editor MUST show an experiment reaction equation area in Chinese
- **AND** the main authoring surface MUST be organized around individual equation cards rather than a permanent row of global snippet buttons.

#### Scenario: Teacher edits a reaction equation row
- **WHEN** a teacher types into an equation card
- **THEN** the editor MUST preserve the raw teacher-entered text for backend preview and save
- **AND** the frontend MUST NOT derive authoritative AI, ES, or RAG fields from its local preview.

#### Scenario: Teacher inserts common chemistry notation
- **WHEN** a teacher opens common chemistry controls
- **THEN** the editor MUST present grouped helpers for reaction symbols, physical states, ions, and common reagents
- **AND** choosing a helper MUST insert text into the currently targeted equation input without changing backend normalization rules.

#### Scenario: Teacher checks equations
- **WHEN** a teacher runs equation checking
- **THEN** the primary visible action MUST use teacher-facing Chinese wording such as “检查”
- **AND** it MUST NOT expose backend implementation wording such as “后端预览” as the main workflow label.

#### Scenario: Backend preview returns normalized equations
- **WHEN** the backend preview or save response returns normalized equation records
- **THEN** each matching equation card MUST show inline normalized display text, validation status, and teacher-readable warnings near the raw input
- **AND** the UI MUST treat the backend response as authoritative over any frontend formatting preview.

#### Scenario: Teacher manages multiple equations
- **WHEN** a point contains multiple reaction equations
- **THEN** the editor MUST support adding, deleting, and reordering equation cards
- **AND** these controls MUST remain compact enough that the equation content remains the visual focus.

#### Scenario: Advanced structure drawing is not the default
- **WHEN** the teacher authors ordinary high-school experiment reaction equations
- **THEN** the default editor MUST remain text-plus-preview
- **AND** it MUST NOT require loading a full chemical structure drawing tool such as Ketcher, MarvinJS, ChemDoodle, or PubChem Sketcher.

### Requirement: Teacher editor friendly guidance uses contextual cards
The teacher catalog editor SHALL present routine guidance and shortcuts as contextual editor cards instead of full-width system alert banners.

#### Scenario: Teacher sees the video upload shortcut
- **WHEN** a teacher opens the video binding panel for a point-capable catalog node
- **THEN** the panel MUST show a compact video resource shortcut card near the panel header
- **AND** the shortcut MUST link to the video resource upload page
- **AND** it MUST NOT use a full-width system alert for the upload hint.

#### Scenario: Teacher reviews static fallback evidence state
- **WHEN** a teacher opens the AI context panel for a point-capable catalog node
- **THEN** the static fallback evidence section MUST show a lifecycle/state transition card
- **AND** the current evidence state MUST be visually highlighted using existing evidence status data
- **AND** the section MUST avoid broad explanatory system alert styling for routine missing, searching, available, stale, or failed states.

#### Scenario: Teacher runs real RAG search diagnostics
- **WHEN** a teacher opens or runs the RAG diagnostics in the AI context panel
- **THEN** visible labels and button text MUST refer to real RAG search
- **AND** the panel MUST show search results or failure state without redundant explanatory alert copy.

### Requirement: Chapter switching lives in the workspace title area
The teacher catalog editor SHALL avoid duplicate chapter selectors and use the current chapter title area as the primary chapter-switching control.

#### Scenario: Teacher changes chapter
- **WHEN** a teacher opens the catalog workspace and wants to switch chapters
- **THEN** the current chapter title area MUST provide a clear chapter switching interaction
- **AND** the editor MUST NOT show a redundant left-sidebar chapter dropdown that repeats the same title.

#### Scenario: Chapter changes
- **WHEN** the teacher selects a different chapter
- **THEN** the tree, selection, validation summary, and right workspace MUST refresh to that chapter's catalog context
- **AND** stale node details from the previous chapter MUST NOT remain actionable.

### Requirement: Right workspace uses a contextual title card and tab surface
The selected node workspace SHALL present node identity, status, and work panels as one coherent surface.

#### Scenario: Directory node is selected
- **WHEN** a teacher selects a directory node
- **THEN** the workspace MUST show a title card with directory identity, publication/status summary, child point counts, and actionable checks
- **AND** it MUST avoid repeating the same title as both labels and content tags.

#### Scenario: Point node is selected
- **WHEN** a teacher selects a point node
- **THEN** the workspace MUST show a title card with point title, catalog path context, video/content/evidence/status indicators, and publish/archive actions
- **AND** the edit panels MUST sit in a tabbed workbench below the title card.

#### Scenario: No node is selected
- **WHEN** no catalog node is selected
- **THEN** the workspace MUST render a visually consistent empty state aligned with the surrounding editor shell
- **AND** it MUST invite selecting or creating a node without looking like a detached blank card.

### Requirement: Modern tree drag-and-drop behavior
The catalog tree SHALL behave like a modern online file tree during move and reorder operations.

#### Scenario: Teacher drags a node
- **WHEN** a teacher starts dragging a catalog node
- **THEN** the tree MUST show a visible drag preview or drag overlay
- **AND** potential drop targets MUST provide clear hover/drop feedback.

#### Scenario: Teacher hovers over a collapsed directory
- **WHEN** a dragged node hovers over a collapsed directory long enough to indicate intent
- **THEN** the directory MUST auto-expand or expose an intentional expand affordance
- **AND** the drop target MUST remain understandable after expansion.

#### Scenario: Move succeeds
- **WHEN** a node move or reorder operation succeeds
- **THEN** the tree MUST refresh or update local state immediately
- **AND** the moved node MUST remain visible and selected in its new location when possible.

#### Scenario: Move fails
- **WHEN** a move is rejected by validation or network failure
- **THEN** the tree MUST restore the previous layout
- **AND** it MUST show a teacher-readable error without leaving a phantom row or stale target highlight.

### Requirement: Tree connector geometry is consistent across depths
The catalog tree SHALL draw indentation and branch connectors without overlapping expand controls or node icons.

#### Scenario: First-level directory is rendered
- **WHEN** a first-level directory row is displayed
- **THEN** its horizontal connector MUST extend only far enough to indicate hierarchy
- **AND** it MUST NOT overlap the child expand/collapse control.

#### Scenario: Deeper rows are rendered
- **WHEN** second-level or deeper directory and point rows are displayed
- **THEN** each row MUST show the same short horizontal connector convention as first-level rows
- **AND** vertical guide lines MUST align with the correct ancestor depth.

### Requirement: Teaching note is the only teacher-only note field
The catalog editor SHALL use one teacher-only note concept named teaching note.

#### Scenario: Teacher edits point notes
- **WHEN** a teacher edits point content
- **THEN** the form MUST expose a single teacher-only teaching note field
- **AND** it MUST NOT separately expose overlapping labels such as management summary and teacher note for the same semantic purpose.

#### Scenario: New point is created
- **WHEN** a teacher creates a new point or directory
- **THEN** default authoring fields MUST use teaching note wording wherever teacher-only remarks are collected
- **AND** student-facing descriptions MUST remain separate from teaching notes.

### Requirement: Modern catalog tree drag movement
The teacher catalog editor SHALL make node movement behave like a modern file-directory tree, with continuous drag feedback, navigable drop targets, immediate visible updates, and reliable reconciliation after persistence.

#### Scenario: Teacher starts dragging a catalog node
- **WHEN** a teacher starts dragging a directory or point node in the left catalog tree
- **THEN** the dragged source row MUST enter a visible dragging state
- **AND** a drag preview MUST follow the pointer
- **AND** the preview MUST identify the moved item using the node icon and title when a single node is dragged.

#### Scenario: Teacher drags over reorder positions
- **WHEN** a teacher drags a node over a valid same-level or cross-level reorder position
- **THEN** the tree MUST show a visible insertion indicator at the exact before-or-after position that will be used on drop
- **AND** the indicator MUST be visually distinct from normal hover and selection states.

#### Scenario: Teacher drags over a directory target
- **WHEN** a teacher drags a node over a valid directory target for moving into that directory
- **THEN** the directory row MUST show a visible drop-target state that communicates the node will be placed inside that directory
- **AND** point rows MUST NOT appear as valid parent drop targets.

#### Scenario: Collapsed directory expands while dragging
- **WHEN** a teacher holds a dragged node over a valid collapsed directory drop target for approximately 500 milliseconds
- **THEN** the directory MUST expand without requiring the teacher to release the mouse
- **AND** unloaded directory children MUST be loaded so the teacher can continue navigating into the destination before dropping
- **AND** the directory MUST remain expanded after the drag completes.

#### Scenario: Teacher drops a valid reorder
- **WHEN** a teacher drops a node into a valid position within the same parent
- **THEN** the visible tree order MUST update immediately without requiring manual refresh
- **AND** the system MUST persist sibling display order
- **AND** the refreshed server order MUST keep the same result after reconciliation.

#### Scenario: Teacher drops a valid move into another parent
- **WHEN** a teacher drops a node into another valid directory parent or the chapter root
- **THEN** the node MUST immediately disappear from the visible source list when the source is loaded
- **AND** the node MUST appear in the visible destination list when the destination is loaded or opened
- **AND** the selected node and editor context MUST remain on the moved node where practical
- **AND** source and destination branches MUST refresh after persistence so stale lazy-loaded children are not shown.

#### Scenario: Move persistence fails
- **WHEN** the server rejects or fails a move or reorder after the tree performed an optimistic update
- **THEN** the tree MUST restore the previous visible ordering and parent placement
- **AND** the teacher MUST see a controlled error message
- **AND** the selected node MUST NOT be lost.

#### Scenario: Teacher attempts an invalid drop
- **WHEN** a teacher drags a node over a point node, a descendant of itself, or an unsupported cross-chapter target
- **THEN** the tree MUST prevent the drop from persisting
- **AND** the visual feedback MUST NOT imply that the target is valid
- **AND** a controlled warning MUST explain why the drop is unavailable when the teacher releases the node.

### Requirement: Selected-node summary adapts to catalog node purpose
The teacher catalog editor SHALL adapt the selected-node summary header to the selected node's purpose instead of rendering the same fixed metric blocks for directories and point nodes.

#### Scenario: Teacher selects a directory node
- **WHEN** a teacher selects a directory node
- **THEN** the summary header MUST identify it with a directory icon or equivalent visual cue
- **AND** it MUST emphasize structure and subtree readiness, such as child composition and publication-check state, rather than a large textual `目录` metric.

#### Scenario: Teacher selects a point node
- **WHEN** a teacher selects a point-capable node
- **THEN** the summary header MUST identify it with an experiment or point icon or equivalent visual cue
- **AND** it MUST emphasize learning-content, video, student-card, related-experiment, and publication-check readiness rather than generic structure metrics.

### Requirement: Summary header avoids low-value filler fields
The teacher catalog editor SHALL avoid promoting redundant or low-actionability metadata to first-class summary tiles.

#### Scenario: Counts overlap for a directory
- **WHEN** direct child count and descendant point count do not provide meaningfully separate decisions
- **THEN** the header MUST merge, suppress, or subordinate one of the counts
- **AND** it MUST not render duplicate-looking count blocks solely to fill a fixed grid.

#### Scenario: A selected node has no blocking issues
- **WHEN** publication checks pass and required resources are complete
- **THEN** the header MUST keep the healthy state visible but visually calm
- **AND** it MUST reserve stronger emphasis for missing or blocking states.

#### Scenario: A selected node has missing content or resources
- **WHEN** learning content, video binding, student card setup, or publication checks are incomplete
- **THEN** the header MUST make the incomplete area easy to spot before the teacher opens deeper editor panels.

### Requirement: Selected-node editor presents a title summary card
The right-side teacher catalog editor SHALL present the selected directory or point with a prominent title summary card that combines object identity, status information, and node actions without relying on tiny status tags as the primary header.

#### Scenario: Teacher selects a catalog node
- **WHEN** a teacher selects a directory, point, hybrid, or shortcut node
- **THEN** the editor MUST show the selected node title as the dominant header text
- **AND** it MUST show supporting breadcrumb or alias context without repeating the same title as a second dominant heading immediately below.

#### Scenario: Teacher reviews node status
- **WHEN** a selected node is visible in the editor
- **THEN** publication state, node kind, child count, and relevant content indicators MUST be presented as readable information blocks or equivalent summary fields
- **AND** archive, restore, publish, cancel-publish, and preview actions MUST remain available according to the existing node state rules.

### Requirement: Editor panel switching uses a clear tab-view control
The selected-node editor SHALL present mutually exclusive editing panels through a visually clear tab-view or segmented workbench switcher that remains attached to the selected-node workbench.

#### Scenario: Teacher switches between editing panels
- **WHEN** a teacher changes between content, student card, video, publication check, or advanced panels
- **THEN** the switcher MUST make the active panel visually obvious
- **AND** the active panel content MUST remain part of the same right-side workbench rather than appearing as an unrelated floating card.

#### Scenario: Teacher selects a directory-only node
- **WHEN** a directory-only node is selected
- **THEN** the editor MUST keep directory-appropriate panel availability
- **AND** it MUST NOT show point-only video or learning-content panels solely because the switcher presentation changed.

#### Scenario: Teacher selects a point-capable node
- **WHEN** a point or hybrid node is selected
- **THEN** the editor MUST keep point-appropriate panel availability
- **AND** existing save, validation, media binding, related-link, and publication behavior MUST remain unchanged.

### Requirement: Chapter switching is integrated into the catalog heading
The teacher catalog workspace SHALL allow chapter changes from the current-chapter heading without rendering a second full-width chapter dropdown that repeats the same selected chapter title.

#### Scenario: Teacher views the selected chapter context
- **WHEN** a teacher opens the catalog workspace with a chapter selected
- **THEN** the left panel MUST show the selected chapter as the primary current-chapter title
- **AND** the title area MUST expose an accessible chapter-switching affordance.

#### Scenario: Teacher changes chapter from the heading
- **WHEN** a teacher activates the current-chapter title switcher and selects a different chapter
- **THEN** the workspace MUST load the selected chapter's catalog tree
- **AND** it MUST clear any previously selected node using the existing chapter-change behavior.

#### Scenario: Teacher searches catalog nodes
- **WHEN** a teacher uses the left search input
- **THEN** the search MUST remain scoped to catalog directories, points, notes, aliases, or identities
- **AND** it MUST NOT duplicate the chapter switching control.

### Requirement: Selected-node editor renders as a cohesive workbench
The right editor SHALL present the selected-node header, tabs, and active panel as one cohesive workbench surface rather than multiple disconnected cards.

#### Scenario: Teacher selects a directory or point
- **WHEN** a teacher selects a directory or point in the catalog tree
- **THEN** the right side MUST show the node status, kind, title, breadcrumb, actions, tabs, and active editing panel within a single visually unified workbench.
- **AND** publication, archive/restore, preview, validation, save, media binding, related-link, and advanced actions MUST keep their existing behavior.

#### Scenario: Teacher switches editor tabs
- **WHEN** a teacher changes tabs inside the selected-node editor
- **THEN** the tab navigation MUST remain visually attached to the selected-node workbench
- **AND** the active tab content MUST not appear as an unrelated floating card.

### Requirement: No-selection state matches the editor workbench
The teacher catalog workspace SHALL show an intentional no-selection state that uses the same right-side workbench shell as the selected-node editor.

#### Scenario: Teacher has not selected a catalog node
- **WHEN** no directory or point is selected and the editor is not loading or errored
- **THEN** the right side MUST show a coordinated empty state inviting the teacher to select a directory or point
- **AND** the empty state MUST align with the selected editor workbench's spacing, border, radius, and background treatment.

### Requirement: Sidebar tree row metadata is localized and scan-friendly
The teacher catalog tree SHALL render row metadata with Chinese-facing labels, compact status dots, and sidebar-style trailing numbers instead of raw backend enum text.

#### Scenario: Directory row renders in the sidebar tree
- **WHEN** a directory row is visible in the teacher catalog tree
- **THEN** the row MUST show a folder icon sized clearly for the sidebar row density
- **AND** it MUST show the directory title and directory kind without overlapping trailing metadata
- **AND** it MUST render the directory status as a compact colored status dot with a Chinese accessible label
- **AND** it MUST NOT render raw backend status values such as `published`, `draft`, or `archived` as visible row text.

#### Scenario: Point row renders in the sidebar tree
- **WHEN** a point row is visible in the teacher catalog tree
- **THEN** the row MUST show an experiment-specific icon such as a flask or test tube, sized clearly for the sidebar row density
- **AND** it MUST preserve the same title alignment as directory rows by reserving disclosure space
- **AND** it MUST render point status with the same compact Chinese status-dot system
- **AND** it MUST NOT use a generic document icon as the primary point identity.

#### Scenario: Selected row needs explicit status clarity
- **WHEN** a directory or point row is selected, hovered, focused, or inspected by assistive technology
- **THEN** the UI MUST expose the status using Chinese-facing labels such as `已发布`, `草稿`, or `已归档`
- **AND** it MUST NOT expose raw backend status enum text in the visible left tree.

#### Scenario: Validation and publication status both apply
- **WHEN** a node has validation warnings or errors
- **THEN** the row MUST keep validation warning affordances visually distinct from the publication status dot
- **AND** the warning state MUST NOT replace or redefine the node's publication status.

### Requirement: Directory rows expose authoritative recursive point counts
The teacher catalog tree SHALL show directory point counts from a backend-provided recursive node-card field rather than from the currently loaded client subtree.

#### Scenario: Teacher views a directory with descendant points
- **WHEN** a directory has point descendants at any depth under the same chapter
- **THEN** the directory row MUST be able to show the total count of non-archived descendant point nodes as trailing sidebar metadata
- **AND** the count MUST remain correct even when some descendant directories are not currently expanded or loaded in the client.

#### Scenario: Teacher views an empty directory
- **WHEN** a directory has zero non-archived descendant point nodes
- **THEN** the row MUST avoid presenting a misleading loaded-child count as a total point count
- **AND** the UI MUST either hide the zero count or show `0` as an authoritative backend-provided zero count.

#### Scenario: Teacher views a point row
- **WHEN** a point row is visible
- **THEN** the row MUST NOT show the directory descendant point count as if the point had children
- **AND** point-specific trailing metadata MUST be limited to point-owned information such as video binding completion where applicable.

#### Scenario: Tree structure changes
- **WHEN** a teacher creates, moves, archives, restores, or deletes a point under a directory subtree
- **THEN** subsequent catalog root, child, detail, or search fetches MUST return updated recursive point counts for affected directory cards.

### Requirement: Catalog node cards include recursive directory point count
The teacher catalog read model SHALL expose a stable recursive point-count field on catalog node cards used by the admin tree.

#### Scenario: Root directory cards are loaded
- **WHEN** the admin frontend loads root catalog nodes for a chapter
- **THEN** every returned `CatalogNodeCard` MUST include `descendant_point_count` as a number
- **AND** directory values MUST count non-archived descendant point nodes recursively.

#### Scenario: Child directory cards are loaded lazily
- **WHEN** the admin frontend loads children for a directory
- **THEN** every returned child `CatalogNodeCard` MUST include `descendant_point_count`
- **AND** the count MUST NOT depend on which sibling or descendant nodes the client has already loaded.

#### Scenario: Point cards are loaded
- **WHEN** a `CatalogNodeCard` represents a point node
- **THEN** `descendant_point_count` MUST be `0`
- **AND** consumers MUST use point-owned media fields for video completion metadata.

#### Scenario: Selected node detail is loaded
- **WHEN** the admin frontend loads selected node detail
- **THEN** the detail payload's node card and child cards MUST include the same `descendant_point_count` contract as tree list payloads.

### Requirement: Tree header has one root creation surface
The teacher catalog tree SHALL expose a single compact chapter-root creation surface in the left tree toolbar.

#### Scenario: Teacher views the selected chapter heading
- **WHEN** a teacher views the left catalog panel for a selected chapter
- **THEN** the chapter heading MUST show chapter context such as `当前章节` and the chapter title
- **AND** it MUST NOT also show duplicate visible `目录` and `点位` root creation buttons.

#### Scenario: Teacher creates a root node
- **WHEN** a teacher wants to create a top-level node under the selected chapter
- **THEN** the tree toolbar MUST provide one compact add action
- **AND** that add action MUST offer Chinese menu items for creating a directory and creating a point.

#### Scenario: Secondary tree actions exist
- **WHEN** refresh, expand-all, collapse-all, or similar secondary tree commands are available
- **THEN** they MUST live in a subtle toolbar icon or more menu
- **AND** they MUST NOT create another competing root-add surface.

#### Scenario: Root creation wording is visible
- **WHEN** root creation controls are visible
- **THEN** the UI MUST use teacher-facing Chinese wording such as `新建目录`, `新建点位`, or `添加到本章`
- **AND** it MUST NOT expose implementation wording such as `root node` as primary visible text.

### Requirement: Sidebar row layout remains stable under actions and counts
The teacher catalog tree SHALL keep row alignment stable when counts, status dots, warnings, and contextual actions appear.

#### Scenario: Teacher hovers a directory row
- **WHEN** a directory row is hovered, focused, or selected
- **THEN** child-add and more-actions controls MUST be available without being permanently visible on every unselected row
- **AND** their appearance MUST NOT shift the chevron, icon, title, status dot, or count positions.

#### Scenario: Teacher hovers a point row
- **WHEN** a point row is hovered, focused, or selected
- **THEN** point-appropriate more-actions controls MUST be available without being permanently visible on every unselected row
- **AND** child-add controls MUST NOT appear for point rows.

#### Scenario: Row title is long
- **WHEN** a directory or point title is longer than the available row title area
- **THEN** the title MUST truncate or otherwise fit without overlapping the trailing count, status dot, warning icon, or actions.

### Requirement: Arborist sidebar navigation tree
The teacher catalog editor SHALL render the chapter catalog tree through an Arborist-backed sidebar navigation tree inspired by the shared Dribbble sidebar navigation reference and `react-arborist` Gmail/sidebar demo.

#### Scenario: Teacher views the catalog tree
- **WHEN** a teacher opens a chapter catalog
- **THEN** the tree MUST render as a single coherent sidebar row system rather than an Ant Design Tree wrapper containing a separate custom row
- **AND** the tree MUST NOT expose Ant Design Tree switcher/indent/content-wrapper visuals as part of the visible row language.

#### Scenario: Directory row renders
- **WHEN** a directory row is visible
- **THEN** a disclosure chevron MUST appear immediately before the directory icon
- **AND** the directory icon MUST use a sidebar-appropriate folder icon
- **AND** the row MUST be able to display trailing metadata such as status or child count without overlapping the title.

#### Scenario: Point row renders
- **WHEN** a point row is visible
- **THEN** it MUST reserve the same disclosure width as directory rows so titles align
- **AND** it MUST use experiment-specific iconography such as a flask or test-tube icon rather than a generic document/file icon
- **AND** video availability MUST appear as trailing metadata, not as the primary node-kind icon.

#### Scenario: Teacher selects a row
- **WHEN** a teacher selects a directory or point row
- **THEN** the selected state MUST be a full-row rounded sidebar highlight
- **AND** it MUST NOT look like a bordered card embedded inside the tree.

#### Scenario: Teacher scans nested directories
- **WHEN** the catalog contains at least three nested levels
- **THEN** the tree MUST render soft nested guide lines or an equivalent stable hierarchy affordance
- **AND** indentation, chevrons, icons, labels, trailing metadata, and actions MUST remain aligned at common admin desktop widths.

### Requirement: Sidebar tree actions remain available without visual clutter
The teacher catalog tree SHALL keep add, drag, status, and secondary actions available while preserving the clean sidebar tree appearance.

#### Scenario: Teacher hovers or focuses a directory row
- **WHEN** a directory row is hovered, focused, or selected
- **THEN** a child-add action MUST be available for creating a child directory or child point
- **AND** the action MUST NOT be permanently visible on every unselected row.

#### Scenario: Teacher hovers or focuses any row
- **WHEN** a row is hovered, focused, or selected
- **THEN** a more-actions menu MUST provide secondary actions such as copy id, archive or restore, publish or unpublish, and fallback movement
- **AND** these controls MUST NOT shift title, icon, or trailing metadata layout when they appear.

#### Scenario: Teacher sees drag affordance
- **WHEN** dragging is available for a row
- **THEN** the implementation MUST provide a visually subtle drag affordance through the row itself or a hover-only handle
- **AND** the UI MUST NOT show always-visible six-dot drag grips on every row.

#### Scenario: Teacher adds a top-level node
- **WHEN** a teacher adds a node at the selected chapter root
- **THEN** the UI MUST use teacher-facing wording such as "add to chapter"
- **AND** it MUST NOT expose implementation wording such as "root node" as the primary visible label.

### Requirement: Arborist drag movement preserves catalog semantics
The teacher catalog tree SHALL map Arborist drag and move events to existing catalog move and reorder semantics without changing backend APIs.

#### Scenario: Teacher drags within the same parent
- **WHEN** a teacher drags a directory or point row to a valid sibling position under the same parent
- **THEN** the UI MUST show a clear Arborist drop cursor
- **AND** the system MUST persist the new sibling order through the existing reorder API.

#### Scenario: Teacher drags into a directory
- **WHEN** a teacher drags a directory or point row into a valid directory parent
- **THEN** the UI MUST show that the directory can receive the drop
- **AND** the system MUST persist the new parent id and display order through the existing move API.

#### Scenario: Teacher attempts an invalid drop
- **WHEN** a teacher attempts to drop a node into a point node, into its own descendant, or across an unsupported chapter boundary
- **THEN** the UI MUST prevent the drop or show a controlled validation warning
- **AND** no partial move or reorder MUST be persisted.

#### Scenario: Teacher cannot use drag precisely
- **WHEN** a teacher uses a row menu or keyboard-accessible command instead of drag
- **THEN** the editor MUST provide fallback movement commands
- **AND** those commands MUST apply the same directory, cycle, and chapter validation as drag.

### Requirement: Arborist lazy loading preserves directory affordances
The teacher catalog tree SHALL bridge server-loaded catalog children into Arborist without losing directory disclosure or drop behavior.

#### Scenario: Directory has children that are not loaded yet
- **WHEN** a directory node reports child availability but its children have not yet been fetched
- **THEN** the tree MUST still render the node as expandable and directory-like
- **AND** opening the node MUST fetch its children and merge them into the tree without clearing the selected node.

#### Scenario: Directory is currently empty
- **WHEN** a directory has no child nodes
- **THEN** the tree MUST still render it as a directory that can receive newly created child nodes where allowed
- **AND** it MUST NOT render as a point-like leaf.

#### Scenario: Search or creation selects a nested node
- **WHEN** search results or a newly created node select a nested node
- **THEN** the tree MUST open known ancestors and scroll the selected node into view where the client has enough loaded context
- **AND** it MUST preserve the selected stable node id.

### Requirement: Polished source-list catalog tree
The teacher catalog editor SHALL render the chapter catalog as a polished source-list/file-tree surface with a coherent visual language for hierarchy, node kind, selection, and status.

#### Scenario: Teacher views a mixed directory and point tree
- **WHEN** a teacher opens a chapter catalog containing expandable directories, collapsed directories, and point leaves
- **THEN** expandable directories MUST show a consistent disclosure affordance
- **AND** point leaves MUST reserve equivalent disclosure space so titles align with directory titles
- **AND** directory and point icons MUST use the same optical size, stroke weight, and color system.

#### Scenario: Teacher selects a point row
- **WHEN** a teacher selects a point row in the tree
- **THEN** the row MUST use a full-row selected state that stays aligned with the tree hierarchy
- **AND** it MUST NOT render as a large bordered card inside the tree.

#### Scenario: Teacher scans a deep catalog
- **WHEN** the tree contains at least three nested levels and long chemistry node titles
- **THEN** indentation, guide lines, title truncation, status display, and row actions MUST remain visually stable
- **AND** node text, status, disclosure controls, drag handles, and action controls MUST NOT overlap at common admin desktop widths.

#### Scenario: Row actions are available
- **WHEN** a teacher hovers, focuses, or selects a row
- **THEN** contextual actions such as add child, archive or restore, publish action where supported, copy id, and more actions MAY appear
- **AND** every row MUST NOT show large always-visible move-up or move-down controls.

### Requirement: Mature drag movement with accessible fallback
The teacher catalog tree SHALL support reorder and move through a mature draggable tree interaction with a non-mouse fallback.

#### Scenario: Teacher drags a node to a valid position
- **WHEN** a teacher drags a directory or point row to a valid sibling position or valid directory parent
- **THEN** the UI MUST show a clear drop indicator before persistence
- **AND** the saved tree MUST preserve the moved node id, child subtree where relevant, and sibling order after refresh.

#### Scenario: Teacher drags to an invalid target
- **WHEN** a teacher attempts to drop a node onto a point, into its own descendant, or across a disallowed chapter boundary
- **THEN** the UI MUST prevent the drop or show a controlled validation error
- **AND** no partial move or reorder MUST be persisted.

#### Scenario: Teacher cannot use drag precisely
- **WHEN** a teacher uses keyboard navigation, focus actions, or a row menu instead of drag
- **THEN** the editor MUST provide a fallback way to move or reorder the selected node where movement is allowed
- **AND** the fallback MUST apply the same directory/point and cycle validation as drag.

### Requirement: Focused selected-node editor information architecture
The right editor SHALL present selected-node editing as a focused workspace with primary authoring fields first and operational/debug fields separated into secondary inspection surfaces.

#### Scenario: Point node default editor opens
- **WHEN** a teacher selects a point node
- **THEN** the default editor view MUST prioritize teacher-only note, principle mode and principle content, phenomenon explanation, safety note, video presence, related experiments, and primary publish actions
- **AND** the point title MUST be maintained as selected-point identity in the header instead of appearing as a routine content form field
- **AND** shared-experiment reuse indicators such as `多目录共享实验` MUST appear with selected-point identity/status, not inside the content form body
- **AND** raw node id, parent id, display order, search-index diagnostics, validation internals, AI/RAG evidence details, and related-link sort internals MUST NOT appear in the default point content view.

#### Scenario: Directory node default editor opens
- **WHEN** a teacher selects a directory node
- **THEN** the default editor view MUST prioritize `目录信息` guidance and teacher-only note where applicable
- **AND** directory title editing MUST be available from selected-node header identity controls and MUST NOT be duplicated as a routine content-body input
- **AND** it MUST NOT show point principle, video binding, related experiment links, assessment, search-document controls, student-card description, card image, card icon, card accent, or card layout as directory-owned fields.

#### Scenario: Teacher needs less-common metadata
- **WHEN** a teacher opens node status, AI context, or advanced/debug inspection
- **THEN** the editor MUST open those details from a secondary `高级` or `更多` entry
- **AND** those details MUST be visually and navigationally secondary to the content/video/related authoring workflow.

#### Scenario: Selected node header renders
- **WHEN** any catalog node is selected
- **THEN** the editor MUST show a stable selected-node header with primary status, node kind, title, breadcrumb path, compact readiness/status summaries, and one state-machine-driven primary action where an action is needed
- **AND** generic inspection actions such as `预览学生端`, `节点状态`, `点位检索诊断`, and `高级调试` MUST live in a secondary `更多` menu
- **AND** lifecycle actions such as unpublish and archive MUST NOT be rendered as peers of preview or diagnostics in the main header row
- **AND** point nodes MUST show compact binary video status such as `有视频` or `无视频` in the header or video panel.

#### Scenario: Point header separates maintenance summaries from node status
- **WHEN** the selected point header renders summary information
- **THEN** learning content, video, and related experiments MUST remain grouped as routine maintenance summary cards
- **AND** node status MUST render as a separate right-aligned status plaque that preserves the status label, primary status, and concise description
- **AND** the node status plaque MUST use distinct visual treatment from the routine maintenance cards, such as material tint, icon emphasis, or internal divider
- **AND** the node status plaque MUST NOT stretch the routine maintenance cards or create empty vertical space inside them.

#### Scenario: Node status is needed during authoring
- **WHEN** a selected node has missing content, missing video, sync attention, or structural exception status
- **THEN** the header and tree MUST keep a compact primary status signal visible
- **AND** detailed status conditions MUST remain available through the secondary diagnostics surface instead of adding another primary tab.

### Requirement: Point title is a single visible authoring concept
The teacher editor SHALL avoid exposing duplicate primary title concepts for point nodes.

#### Scenario: Teacher edits a point title
- **WHEN** a teacher edits the primary title for a point node
- **THEN** the UI MUST expose the edit affordance from the selected-node header
- **AND** the UI MUST treat the edited value as the point name shown in the tree and point detail editor
- **AND** the save flow MUST keep node title and point title synchronized unless an explicit advanced override is later introduced.

#### Scenario: Backend data contains divergent titles
- **WHEN** loaded point data contains a node title and point title that differ
- **THEN** the default editor MUST choose one teacher-facing primary title according to documented mapping rules
- **AND** any mismatch diagnostics MUST appear only in advanced/debug context.

### Requirement: Selected-point primary action state machine
The selected-point header SHALL compute at most one primary action from resolved node status, shared content state, video readiness, and student visibility.

#### Scenario: Point is archived
- **WHEN** a selected point is archived
- **THEN** the primary action MUST be `恢复节点`
- **AND** preview, diagnostics, and destructive actions MUST remain secondary.

#### Scenario: Point has structural errors
- **WHEN** a selected point has blocking validation or identity errors
- **THEN** the primary action MUST be `查看问题`
- **AND** publish actions MUST NOT be shown as the primary action.

#### Scenario: Point content is incomplete
- **WHEN** a selected point is missing required learning content fields
- **THEN** the primary action MUST be `补齐内容`
- **AND** clicking the action MUST open a focused content editing window that reuses the same point content authoring model as the `内容` tab
- **AND** the window MUST highlight missing required fields and focus or clearly mark the first missing required field
- **AND** saving in the window MUST use the same point-content save behavior as the normal content form
- **AND** the action MUST NOT call AI, auto-fill text, or publish stale content
- **AND** publishing to students MUST NOT be the primary action.

#### Scenario: Shared learning content is ready but unpublished
- **WHEN** required learning content fields are complete and the shared point content is not published
- **THEN** the primary action MUST be `发布学习内容`
- **AND** the action MUST publish shared point content rather than only changing catalog placement status.
- **AND** if the content form has unsaved edits, the action MUST open the focused content editing window and require saving those edits before publishing.

#### Scenario: Point is missing video
- **WHEN** shared learning content is publishable or published and no publishable video is bound
- **THEN** the primary action MUST be `绑定视频`
- **AND** clicking the action MUST open the existing `选择视频素材` picker window for the selected point
- **AND** if no ready video asset exists, the picker window MUST show the video-resource entry point
- **AND** the action MUST NOT upload or bind media automatically before the teacher explicitly selects a media asset.

#### Scenario: Point is ready for student visibility
- **WHEN** shared learning content is published, a publishable video exists, and the catalog placement is not published
- **THEN** the primary action MUST be `发布到学生端`
- **AND** the action MUST publish the selected catalog placement.

#### Scenario: Published point has sync attention
- **WHEN** a selected point is student-visible but ES or AI/RAG consumption is failed or unavailable
- **THEN** the primary action MUST be `查看同步`
- **AND** clicking the action MUST open diagnostics focused on ES and AI/RAG sync state
- **AND** routine unpublish/archive actions MUST remain in the secondary menu.

#### Scenario: Point is fully published
- **WHEN** a selected point has published shared content, a publishable video, published placement, and no blocking sync attention
- **THEN** the header MUST show the published status without a competing primary lifecycle button
- **AND** unpublish MUST be available only from the secondary menu with confirmation.

### Requirement: Teacher preview is a secondary inspection action
The selected-point editor SHALL treat student preview as a secondary inspection action that can render non-published states.

#### Scenario: Teacher previews a draft point
- **WHEN** a teacher chooses `预览学生端` for a non-published but renderable point
- **THEN** the system MUST open a preview scoped to that point
- **AND** the preview MUST render the current draft content, missing-content placeholders, or missing-video state as applicable.

#### Scenario: Preview action is shown
- **WHEN** a point node is selected
- **THEN** `预览学生端` MUST be available from the secondary `更多` menu
- **AND** it MUST NOT occupy the header primary action position.

### Requirement: Student availability requires placement and content publication
Catalog point status summaries SHALL only mark a point as student-available when both the selected catalog placement and the shared point content are published.

#### Scenario: Placement is published but shared content is draft
- **WHEN** a point placement is `published` and its shared point content is `draft`
- **THEN** the status summary MUST report `student_available` as false
- **AND** the selected-point primary action MUST continue to direct the teacher toward publishing learning content.

#### Scenario: Shared content is published but placement is draft
- **WHEN** shared point content is `published` and the selected placement is `draft`
- **THEN** the status summary MUST report `student_available` as false
- **AND** the selected-point primary action MUST direct the teacher toward publishing to the student side.

### Requirement: Catalog video panel remains binding-only
The selected-node editor SHALL keep video upload separate from catalog authoring and only manage existing media bindings for point nodes.

#### Scenario: Teacher opens the point video panel
- **WHEN** a teacher opens video management for a point node
- **THEN** the panel MUST allow selecting existing media assets, binding, previewing, publishing, unpublishing, or removing point media bindings
- **AND** it MUST NOT render a local file input, tus upload control, or upload-and-bind action.

#### Scenario: Teacher needs a new video asset
- **WHEN** the needed video asset is not available in the existing media selector
- **THEN** the catalog editor MUST provide a clear navigation hint or link to the media/video upload workflow
- **AND** the upload lifecycle MUST remain owned by the media/video feature.

### Requirement: Catalog workspace visual acceptance is verified
The teacher catalog editor SHALL include visual and interaction acceptance checks for the tree, selected-node editor, simplified authoring tabs, preview flow, and secondary diagnostics surfaces.

#### Scenario: Tree visual QA runs
- **WHEN** implementation validates the catalog tree UI
- **THEN** QA MUST cover expanded directory, collapsed directory, selected point, long title, hover or focus row action, drag/drop indicator, needs-content marker, needs-video marker, descendant aggregate marker, exception marker, and sync-attention marker states
- **AND** QA MUST inspect at least one narrow laptop-width admin viewport where row actions, counts, and status markers are likely to collide.

#### Scenario: Editor visual QA runs
- **WHEN** implementation validates the selected-node editor UI
- **THEN** QA MUST cover directory content-only editor, point content tab, point video tab, related experiments tab, header preview action, and header diagnostics action
- **AND** QA MUST verify that the primary tab strip does not contain student-card, node-status, AI-context, or advanced-debug tabs.
- **AND** related experiments QA MUST verify the compact row list, row-level drag behavior, row-between drop indicator, absence of visible drag grips, absence of always-visible up/down reorder buttons, absence of short-name inputs, compact search/add rows, and narrow viewport non-overlap.

#### Scenario: Preview visual QA runs
- **WHEN** implementation validates `预览学习卡片`
- **THEN** QA MUST open at least one point in a phone-sized preview viewport
- **AND** it MUST verify the preview uses a standard phone mockup/frame with the real student point/detail layout inside it
- **AND** it MUST verify at least the default modern iPhone preset and one alternate phone preset
- **AND** it MUST verify the preview does not expose teacher-only diagnostics.

#### Scenario: Diagnostics visual QA runs
- **WHEN** implementation validates the secondary diagnostics surfaces
- **THEN** QA MUST cover node status, AI context, and advanced debug access from the selected-node header
- **AND** QA MUST verify those surfaces remain visually secondary to routine content/video/related authoring.

### Requirement: Professional draggable tree interaction
The teacher catalog tree SHALL use a polished draggable tree interaction instead of always-visible up/down row controls.

#### Scenario: Teacher reorders by dragging
- **WHEN** a teacher drags a directory or point row to a valid sibling or directory drop target
- **THEN** the UI MUST show a clear drop indicator and persist the new parent/order after drop
- **AND** the selected node and expanded ancestor context SHOULD remain stable after refresh.

#### Scenario: Invalid drop is attempted
- **WHEN** a teacher drags a node onto a point, across a disallowed chapter boundary, or into its own descendant
- **THEN** the UI MUST prevent the drop or show a controlled validation error
- **AND** no partial move MUST be persisted.

#### Scenario: Row actions are needed
- **WHEN** a teacher hovers, focuses, or selects a tree row
- **THEN** add, archive, duplicate-if-supported, and more actions MAY appear contextually
- **AND** rows MUST NOT show large always-visible move-up and move-down buttons for every node.

### Requirement: Teacher preview displays inline equation annotations as part of the same row
The teacher catalog editor SHALL render inline annotation text returned by backend preview/save responses as visibly attached to its reaction equation row.

#### Scenario: Preview returns an annotated equation
- **WHEN** backend preview returns a normalized reaction record with both an equation core and annotation text
- **THEN** the editor MUST show the normalized equation and the annotation in the same equation card or row
- **AND** it MUST NOT show the annotation as a separate failed reaction candidate.

#### Scenario: Teacher edits annotated multiline input
- **WHEN** the teacher edits a multiline equation input containing `//` annotations
- **THEN** preview state, validation warnings, and accepted suggestions MUST remain aligned by source line order
- **AND** annotation display MUST update with the same row as its equation core.

### Requirement: Teacher authoring preserves annotation suffixes non-destructively
The teacher catalog editor SHALL preserve raw annotated reaction lines during hydration, editing, preview, save, and AI suggestion application.

#### Scenario: Existing annotated equations are loaded
- **WHEN** a point with saved annotated reaction rows is opened
- **THEN** the editor MUST hydrate the authoring input from stored raw rows including the `//` annotation suffix
- **AND** the teacher MUST be able to save without losing the annotation text.

#### Scenario: AI correction is applied to one equation
- **WHEN** the teacher applies an AI correction that changes only the equation core
- **THEN** the editor MUST keep the existing `//` annotation suffix on that line
- **AND** the resulting line MUST remain one saved reaction row.

#### Scenario: Teacher intentionally edits annotation text
- **WHEN** the teacher edits text after `//`
- **THEN** the editor MUST send the full raw line to backend preview/save
- **AND** backend-derived annotation fields MUST reflect the edited suffix after preview or save.

### Requirement: Catalog editor diagnostic navigation uses retrieval wording
The teacher catalog editor SHALL distinguish point authoring from point retrieval diagnostics so teachers do not confuse editing content with AI/RAG/ES operational state.

#### Scenario: Teacher selects a point node
- **WHEN** a teacher selects a point node in the catalog editor
- **THEN** the primary editor MUST continue to prioritize point title, three-element content, equation authoring, publication state, and video binding
- **AND** retrieval diagnostics MUST appear as a secondary tab, panel, or action with wording such as `点位检索诊断`.

#### Scenario: Teacher selects a directory node
- **WHEN** a teacher selects a directory node
- **THEN** the editor MUST focus on directory metadata, recursive point counts, movement, visibility, and child organization
- **AND** it MUST NOT present directory nodes as if they had the same point-level ES/RAG content diagnostics as experiment points.

#### Scenario: Teacher opens advanced diagnostics
- **WHEN** a teacher opens point diagnostics from the editor
- **THEN** the diagnostics surface MUST show ES/RAG/AI/search-preview state for the selected placement
- **AND** it MUST be clearly separated from default authoring controls so operational debug data does not crowd routine editing.

### Requirement: Catalog tree semantics are visible to retrieval diagnostics
The catalog editor SHALL expose enough selected-node context for diagnostics to explain placement identity, canonical identity, and directory-derived recall.

#### Scenario: Same canonical point appears twice
- **WHEN** the editor displays two placements of the same canonical point under different directories
- **THEN** each selected placement MUST expose its placement node id and catalog path to diagnostics
- **AND** diagnostics MUST also expose the shared canonical point id for grouping and smart-pointer explanation.

#### Scenario: Directory context affects point search
- **WHEN** a teacher changes or inspects a directory that contributes to descendant point paths
- **THEN** diagnostics MUST be able to explain that descendant point placement documents may need reindexing
- **AND** the editor MUST avoid implying that a directory title change is purely cosmetic for search.

#### Scenario: Point publication changes from editor
- **WHEN** a teacher publishes, unpublishes, hides, or archives a point from the catalog editor
- **THEN** the editor MUST surface index/evidence state transitions through diagnostics or status badges
- **AND** it MUST preserve the existing save-vs-publish boundary for student search visibility.

### Requirement: Header preview and diagnostics actions
The selected-node header SHALL provide the entry points for student preview and read-only diagnostics.

#### Scenario: Teacher previews a point
- **WHEN** a point node is selected
- **THEN** the header MUST show a `预览学习卡片` action
- **AND** the action MUST launch the teacher-authorized student preview flow for that point
- **AND** the preview shell MUST allow selecting from a small set of standard phone presets while keeping the student point page read-only.

#### Scenario: Teacher opens diagnostics
- **WHEN** a teacher opens the header `高级` or `更多` action
- **THEN** the menu MUST provide access to `节点状态`, `AI 上下文`, and `高级调试`
- **AND** choosing one MUST open the corresponding inspection surface without changing the primary authoring tab selection.

#### Scenario: Browser blocks auxiliary window
- **WHEN** the diagnostics or preview window cannot be opened
- **THEN** the teacher frontend MUST show a controlled fallback such as an in-app route, modal, or drawer
- **AND** the fallback MUST preserve the same separation between authoring and diagnostics.

### Requirement: Related experiments editor is a compact ordered list
The teacher catalog editor SHALL present related experiments as a lightweight ordered learning list that matches the catalog tree's row-level interaction language.

#### Scenario: Related experiments tab opens for a point
- **WHEN** a teacher opens the `相关实验` tab for a point node
- **THEN** each related experiment MUST render as a compact single row rather than a form card
- **AND** the row MUST prioritize the target experiment title, a compact source/status tag such as `同目录默认`, `已调整默认`, or `手动添加`, and secondary row actions
- **AND** the panel MUST NOT render per-row student-facing display-name, short-name, or label inputs.

#### Scenario: Teacher reorders related experiments by dragging
- **WHEN** a teacher drags a related experiment row within the list
- **THEN** the whole row MUST act as the draggable object
- **AND** the UI MUST show a subdued source row, a lightweight drag preview, and a thin row-between drop indicator
- **AND** the UI MUST NOT require or show an always-visible `⋮⋮`, six-dot, grip, or equivalent drag handle.

#### Scenario: Related experiment row is idle
- **WHEN** the teacher is not hovering, focusing, or dragging a row
- **THEN** the row MUST remain visually quiet and close to the catalog tree row rhythm
- **AND** it MUST NOT show always-visible up/down reorder buttons or a permanent multi-button action cluster.

#### Scenario: Teacher needs secondary row actions
- **WHEN** the teacher hovers, focuses, or opens the row actions for a related experiment
- **THEN** delete/remove and any precision reorder fallback commands MAY be available through a quiet hover action or `...` menu
- **AND** those fallback commands MUST remain visually secondary to the row title and source tag.

#### Scenario: Related experiment title is long
- **WHEN** a related experiment title is too long for the row
- **THEN** the title MUST truncate or wrap according to the list layout without colliding with the source tag or actions
- **AND** dragging, hovering, or opening actions MUST NOT resize the row in a way that shifts surrounding rows unexpectedly.

#### Scenario: Related experiments are defaults
- **WHEN** no manual related-link override has been saved
- **THEN** the panel MAY show the generated same-parent related experiments as compact rows or a controlled empty/default state
- **AND** the default rows MUST be clear enough to review and reorder without exposing raw link internals.

#### Scenario: Teacher adds a related experiment
- **WHEN** the teacher clicks the dashed add placeholder in the related experiments panel
- **THEN** the system MUST open a catalog tree picker in a modal or equivalent window
- **AND** the picker MUST show directory hierarchy with lazy-loaded children and point rows that can be selected
- **AND** the panel itself MUST NOT render an inline search box, inline search results region, or manual save button.

#### Scenario: Teacher selects a related experiment from the picker
- **WHEN** the teacher selects an eligible point node in the catalog tree picker
- **THEN** the point MUST be appended to the ordered related-experiment list as a manual related link
- **AND** the system MUST persist the updated related-link order immediately without requiring a separate save action
- **AND** the current point and already-selected related points MUST be disabled or ignored.

#### Scenario: Teacher edits related experiment membership or order
- **WHEN** the teacher removes a related experiment, reorders rows by drag/drop, uses a menu reorder fallback command, or resets the list to same-directory defaults
- **THEN** the system MUST persist the updated related-link payload immediately
- **AND** the UI MUST keep the compact ordered-list rhythm without adding a persistent save control.

#### Scenario: Visible instructional copy is rendered
- **WHEN** the related experiments panel renders headings or helper copy
- **THEN** visible copy MUST explain the learning-list purpose at most briefly
- **AND** it MUST NOT rely on prominent instructional text such as `拖动可调整顺序` to compensate for unclear interaction design.

### Requirement: Student-card authoring is removed from the teacher workbench
The teacher catalog editor SHALL remove manual student-card configuration as an authoring concept.

#### Scenario: Teacher edits a point
- **WHEN** a teacher selects a point node
- **THEN** the editor MUST NOT expose fields for point card short description, point card cover image, point card icon key, point card accent, or point card emphasis
- **AND** the editor MUST direct the teacher to preview the real learning card/page instead of manually configuring a card.

#### Scenario: Teacher edits a directory
- **WHEN** a teacher selects a directory node
- **THEN** the editor MUST NOT expose fields for student card description, card image asset id, card icon key, card accent, card layout, or card presentation
- **AND** directory presentation in the student catalog MUST be derived by the student read model and frontend defaults.

#### Scenario: Existing stale frontend code references student-card fields
- **WHEN** frontend tests or type checks inspect the catalog editor
- **THEN** no primary tab, form item, mapper field, or update payload MUST depend on removed student-card configuration fields.

### Requirement: Video tab shows a single current video slot
The teacher catalog editor SHALL present the point video tab as one current-video slot, because each catalog point can bind at most one video.

#### Scenario: Point has no bound video
- **WHEN** a teacher opens the video tab for a point with no active video binding
- **THEN** the tab MUST show an empty video slot or dashed placeholder inviting the teacher to choose a video
- **AND** it MUST NOT show a multi-select dropdown, batch bind button, or binding table.

#### Scenario: Point has a bound video
- **WHEN** a teacher opens the video tab for a point with an active video binding
- **THEN** the tab MUST show exactly one selected-video card or row with thumbnail, title, file name, upload/processing readiness, and preview access
- **AND** it MUST expose only visually secondary replace and remove actions.

#### Scenario: Bound video is processing or not ready
- **WHEN** the active binding's media asset is not ready
- **THEN** the selected-video slot MUST show the processing/unready state clearly
- **AND** it MUST avoid implying the video is already playable for students.

### Requirement: Teacher selects videos from a media picker
The teacher catalog editor SHALL use a media-library style picker for choosing or replacing a point video.

#### Scenario: Teacher chooses a video
- **WHEN** a teacher clicks the empty video slot or replace action
- **THEN** the editor MUST open a modal or equivalent picker listing existing video assets
- **AND** each selectable item MUST include a thumbnail or video placeholder, title, file name, upload/processing state, and preview affordance where available.

#### Scenario: Teacher searches videos
- **WHEN** a teacher types in the picker search field
- **THEN** the picker MUST filter or query video assets by title or file name
- **AND** it MUST keep metadata and thumbnail context visible in results.

#### Scenario: Teacher selects an eligible video
- **WHEN** a teacher selects a ready eligible video from the picker
- **THEN** the editor MUST immediately persist that video as the point's current video
- **AND** it MUST close the picker and keep the teacher on the video tab after detail refresh.

#### Scenario: Teacher inspects an unready video
- **WHEN** a video asset is still processing, failed, or otherwise not ready
- **THEN** the picker MAY show it for context
- **AND** it MUST disable or clearly prevent selecting it as a student-playable video until it is ready.

### Requirement: Video binding edits auto-save without binding publication controls
The teacher catalog editor SHALL make video selection, replacement, and removal direct persisted actions.

#### Scenario: Teacher replaces a video
- **WHEN** a teacher chooses a new video for a point that already has a current video
- **THEN** the editor MUST persist the replacement immediately
- **AND** it MUST show the replacement as the only current video after refresh.

#### Scenario: Teacher removes a video
- **WHEN** a teacher confirms removal of the current video
- **THEN** the editor MUST persist the removal immediately
- **AND** it MUST return the video tab to the empty slot state after refresh.

#### Scenario: Teacher edits video binding
- **WHEN** the video tab renders
- **THEN** it MUST NOT show binding-level `发布`, `取消发布`, `draft`, or `published` controls as authoring actions
- **AND** it MUST NOT require a separate save button after choosing or removing a video.

#### Scenario: Teacher needs to upload a new video
- **WHEN** a teacher needs a video that is not yet in the asset library
- **THEN** the video tab MAY provide a shortcut to the video resource page
- **AND** upload and processing MUST remain owned by the video resource workflow rather than embedded as the primary point binding action.

### Requirement: Point content form uses compact grouped authoring layout
The teacher catalog editor SHALL present point knowledge content as a compact grouped form while preserving existing chemical-equation authoring behavior.

#### Scenario: Teacher opens point knowledge content
- **WHEN** a teacher opens the `知识内容` panel for a point node
- **THEN** the form MUST visually group teacher-only note, experiment principle, and student-facing content as related authoring sections
- **AND** the teacher-only note MUST remain visibly secondary to student-facing point knowledge.

#### Scenario: Teacher edits equation principle mode
- **WHEN** the point principle mode is `化学方程式`
- **THEN** the editor MUST keep the existing natural multiline reaction input, debounced backend preview, AI assistance, suggestion adoption, inline annotation display, and autosave behavior
- **AND** the visible equation area MUST be compact enough that phenomenon explanation and safety note remain easy to reach in the same form.

#### Scenario: Principle controls render
- **WHEN** the experiment principle section is visible
- **THEN** the `化学方程式` / `文字描述` mode selector MUST be placed with the experiment-principle section heading or equivalent section controls
- **AND** the AI equation action MUST be placed with that same section control area when chemical-equation mode is active.

#### Scenario: Equation preview contains many rows
- **WHEN** backend preview returns multiple normalized reaction rows or AI candidates
- **THEN** the editor MUST keep row order visible and preserve per-row candidate adoption actions
- **AND** the preview area MUST use bounded scrolling or an equivalent compact treatment instead of expanding without limit and pushing the student-facing prose fields far down the page.

#### Scenario: Teacher edits student-facing prose
- **WHEN** the teacher edits `现象解释` or `安全提示`
- **THEN** both fields MUST remain textarea controls suitable for longer prose
- **AND** the fields MUST be presented as a coherent student-facing content group that can use two columns on wide surfaces and stack on constrained surfaces.

#### Scenario: Edit-content modal reuses the form
- **WHEN** the teacher opens the reused `编辑内容` modal
- **THEN** the modal MUST use the same content editing behavior as the main `知识内容` panel
- **AND** the layout MUST adapt without relying on sticky equation panes or oversized workbench spacing that would crowd the modal viewport.

### Requirement: Principle mode switching protects existing content
The teacher catalog editor SHALL require explicit confirmation before switching experiment principle mode when the current mode already contains authored content.

#### Scenario: Teacher switches away from equation content
- **WHEN** the current principle mode is `化学方程式`
- **AND** the reaction equation input contains non-empty content
- **AND** the teacher attempts to switch to `文字描述`
- **THEN** the editor MUST show a confirmation dialog explaining that current chemical-equation content will be cleared and only the selected mode will be saved
- **AND** it MUST NOT change the principle mode or autosave the mode switch unless the teacher confirms.
- **AND** the confirmation action MUST be visually marked as dangerous with the label `确认切换`, while the cancel action MUST use the label `放弃切换`.

#### Scenario: Teacher switches away from text principle content
- **WHEN** the current principle mode is `文字描述`
- **AND** the text principle field contains non-empty content
- **AND** the teacher attempts to switch to `化学方程式`
- **THEN** the editor MUST show a confirmation dialog explaining that current text content will be cleared and only the selected mode will be saved
- **AND** it MUST NOT change the principle mode or autosave the mode switch unless the teacher confirms.
- **AND** the confirmation action MUST be visually marked as dangerous with the label `确认切换`, while the cancel action MUST use the label `放弃切换`.

#### Scenario: Teacher switches from an empty mode
- **WHEN** the current principle mode has no authored content
- **AND** the teacher switches to the other principle mode
- **THEN** the editor MAY switch immediately without confirmation
- **AND** it MUST continue to save only the active principle mode.
