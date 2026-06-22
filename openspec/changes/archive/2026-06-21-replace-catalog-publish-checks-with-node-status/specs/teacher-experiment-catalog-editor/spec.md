## MODIFIED Requirements

### Requirement: Publication and validation are explicit
The teacher catalog editor SHALL separate draft editing, student-visible publication, node status diagnosis, and downstream ES/RAG consumption health.

#### Scenario: Teacher reviews node status
- **WHEN** a teacher selects a node or subtree
- **THEN** the editor MUST show a `节点状态` surface instead of a `发布检查` surface
- **AND** the surface MUST group issues into `核心完整性`, `学生可见性`, and `同步诊断`
- **AND** the surface MUST include required title or card fields where relevant, point learning content, binary video state, placement visibility, shared content visibility, related links, and search/RAG consumption state without merging them into one warning list.

#### Scenario: Teacher publishes a subtree
- **WHEN** a teacher publishes a directory subtree
- **THEN** the system MUST publish eligible child directory and point nodes according to explicit teacher action
- **AND** missing learning content or missing video MUST NOT by itself cause a point to be skipped
- **AND** any structurally skipped-node messages MUST use node-status groups and Chinese repair actions rather than raw backend validation strings.

#### Scenario: Core point readiness does not block node publication
- **WHEN** a point is missing one of the required learning fields or has no experiment video
- **THEN** the editor MUST mark the node as needing content or needing video
- **AND** node publication MUST remain available when the node structure is valid
- **AND** the student endpoint MUST be able to render a title-first placeholder for missing learning content.

#### Scenario: Downstream sync is pending during publication
- **WHEN** ES indexing or AI/RAG evidence work is pending, running, or stale after a teacher save or publish action
- **THEN** the editor MUST keep the core publication result visible
- **AND** it MUST place downstream state in `同步诊断`
- **AND** it MUST NOT present pending async work as if the point's content or video were missing.

### Requirement: Sidebar tree row metadata is localized and scan-friendly
The teacher catalog tree SHALL render row metadata with Chinese-facing labels, compact status markers, and sidebar-style trailing numbers while showing at most one primary status signal per row.

#### Scenario: Directory row renders in the sidebar tree
- **WHEN** a directory row is visible in the teacher catalog tree
- **THEN** the row MUST show a folder icon sized clearly for the sidebar row density
- **AND** it MUST show the directory title and directory kind without overlapping trailing metadata
- **AND** it MUST render at most one primary directory status or descendant-action marker with a Chinese accessible label
- **AND** it MUST NOT render raw backend status values such as `published`, `draft`, or `archived` as visible row text.

#### Scenario: Point row renders in the sidebar tree
- **WHEN** a point row is visible in the teacher catalog tree
- **THEN** the row MUST show an experiment-specific icon such as a flask or test tube, sized clearly for the sidebar row density
- **AND** it MUST preserve the same title alignment as directory rows by reserving disclosure space
- **AND** it MUST render point status through the same compact Chinese primary-status system
- **AND** it MUST NOT use a generic document icon as the primary point identity.

#### Scenario: Selected row needs explicit status clarity
- **WHEN** a directory or point row is selected, hovered, focused, or inspected by assistive technology
- **THEN** the UI MUST expose the primary status using Chinese-facing labels such as `已发布`, `草稿`, `缺内容`, `缺视频`, `同步异常`, or `已归档`
- **AND** it MUST expose the short primary reason without showing raw backend enum text in the visible left tree.

#### Scenario: Many status conditions apply
- **WHEN** a node has validation, publication, content, video, ES, and RAG conditions at the same time
- **THEN** the row MUST keep exactly one primary status marker visible by default
- **AND** detailed conditions MUST be available through tooltip, selection, focused filtering, or the `节点状态` panel.

#### Scenario: Directory descendants need action
- **WHEN** a directory has descendant points that need teacher action
- **THEN** the row MUST show a compact aggregate count or marker
- **AND** it MUST NOT display separate badges for every descendant status group in the default tree row.

#### Scenario: Async consumption is not primary row clutter
- **WHEN** ES or RAG state is pending, running, or stale
- **THEN** the default tree row MUST NOT add another visible status badge for that async state
- **AND** failed or unavailable async state MUST be discoverable through `同步异常` filtering and the selected-node status panel.

### Requirement: Focused selected-node editor information architecture
The right editor SHALL present selected-node editing as a focused workspace with primary authoring fields first and operational/debug fields separated into task-specific panels.

#### Scenario: Point node default editor opens
- **WHEN** a teacher selects a point node
- **THEN** the default editor view MUST prioritize point title, teacher-only note, principle mode and principle content, phenomenon explanation, safety note, video presence, and primary publish actions
- **AND** raw node id, parent id, display order, search-index diagnostics, validation internals, and related-link sort internals MUST NOT appear in the default point content view.

#### Scenario: Directory node default editor opens
- **WHEN** a teacher selects a directory node
- **THEN** the default editor view MUST prioritize directory title, teacher-only note, student-visible description, and directory card presentation entry points
- **AND** it MUST NOT show point principle, video binding, related experiment links, assessment, or search-document controls as directory-owned fields.

#### Scenario: Teacher needs less-common metadata
- **WHEN** a teacher opens node status, student card, related experiments, video binding, or advanced/debug panels
- **THEN** the editor MUST show the fields specific to that task
- **AND** those panels MUST be visually secondary to the main content authoring view.

#### Scenario: Selected node header renders
- **WHEN** any catalog node is selected
- **THEN** the editor MUST show a stable selected-node header with primary status, node kind, title, breadcrumb path, and primary actions
- **AND** point nodes MUST show compact binary video status such as `有视频` or `无视频` in the header or video panel.

#### Scenario: Node status panel opens
- **WHEN** a teacher opens the `节点状态` panel
- **THEN** the panel MUST show product-level status before operational diagnostics
- **AND** it MUST show placement-node context and shared-canonical-point context when both identities affect the selected point.

### Requirement: Related experiments are readable defaults with teacher overrides
The teacher catalog editor SHALL present related experiments as an ordered learning list, not as raw link records.

#### Scenario: Related experiments default from the same direct parent
- **WHEN** a teacher opens the related experiments panel for a point
- **THEN** generated defaults MUST represent other point nodes under the same direct parent directory
- **AND** generated defaults MUST preserve the parent directory display order
- **AND** generated defaults MUST NOT silently include points from sibling directories.

#### Scenario: Teacher edits related experiment order
- **WHEN** the related experiments panel contains one or more items
- **THEN** the teacher MUST be able to reorder them with a visible drag handle
- **AND** the teacher MUST be able to use explicit up/down controls as a non-drag fallback
- **AND** the panel MUST keep raw `sort_order` out of the primary UI.

#### Scenario: Teacher adds or labels related experiments
- **WHEN** the teacher searches for experiments to add
- **THEN** search results MUST show readable experiment titles instead of requiring Node ID entry
- **AND** manually added items MUST be visually distinguished from same-parent defaults
- **AND** each item MAY have an optional student-facing display name.

#### Scenario: Teacher resets custom related experiments
- **WHEN** the teacher chooses to reset related experiments
- **THEN** the system MUST remove stored manual/default-override rows for the current point
- **AND** the returned detail MUST again show the generated same-parent default list.

#### Scenario: Shared experiment wording appears in teacher UI
- **WHEN** the UI refers to the canonical experiment identity reused across placements
- **THEN** teacher-facing copy SHOULD use `多目录共享实验` or `共享目录`
- **AND** it SHOULD reserve `相关实验` for the ordered related-experiment list consumed by students, search, and AI context.

### Requirement: Catalog video panel remains binding-only
The selected-node editor SHALL keep video upload separate from catalog authoring and only manage the point's existing media binding while presenting teacher-facing video state as binary.

#### Scenario: Teacher opens the point video panel
- **WHEN** a teacher opens video management for a point node
- **THEN** the panel MUST allow selecting an existing media asset, binding it to the point, previewing it, publishing or unpublishing the binding, or removing the binding
- **AND** it MUST NOT render a local file input, tus upload control, or upload-and-bind action
- **AND** the teacher-facing point status MUST describe video readiness as `有视频` or `无视频`.

#### Scenario: Teacher has not completed learning content
- **WHEN** a point is missing one or more of the three learning fields
- **THEN** the video panel MUST prevent creating a new video binding
- **AND** existing historical bindings MUST remain visible and manageable so data can be cleaned up without dead ends.

#### Scenario: Teacher needs a new video asset
- **WHEN** the needed video asset is not available in the existing media selector
- **THEN** the catalog editor MUST provide a clear navigation hint or link to the media/video upload workflow
- **AND** the upload lifecycle MUST remain owned by the media/video feature.

#### Scenario: Teacher manages an existing binding
- **WHEN** a teacher publishes, unpublishes, previews, or removes a point-node media binding
- **THEN** the editor MUST update only the binding state
- **AND** it MUST NOT alter the underlying media asset upload lifecycle
- **AND** node status MUST update the binary video state after the binding change is saved or refreshed.

#### Scenario: Legacy data exposes multiple bindings
- **WHEN** a point has multiple historical media bindings
- **THEN** the panel MUST still present the product-level status as `有视频` when a usable bound video exists
- **AND** any cleanup detail about multiple bindings MUST remain in advanced diagnostics rather than the primary tree row.

### Requirement: Catalog workspace visual acceptance is verified
The teacher catalog editor SHALL include visual and interaction acceptance checks for the tree, selected-node editor, and node-status surface.

#### Scenario: Tree visual QA runs
- **WHEN** implementation validates the catalog tree UI
- **THEN** QA MUST cover expanded directory, collapsed directory, selected point, long title, hover or focus row action, drag/drop indicator, needs-content marker, needs-video marker, descendant aggregate marker, and sync-attention marker states
- **AND** QA MUST inspect at least one narrow laptop-width admin viewport where row actions, counts, and status markers are likely to collide.

#### Scenario: Editor visual QA runs
- **WHEN** implementation validates the selected-node editor UI
- **THEN** QA MUST cover directory default editor, point default editor, video panel, related experiments panel, `节点状态`, and advanced/debug fields
- **AND** QA MUST verify that default point content editing is not visually dominated by debug/search/order metadata.

#### Scenario: Node status visual QA runs
- **WHEN** implementation validates the `节点状态` panel
- **THEN** QA MUST cover complete point, missing-content point, missing-video point, published placement with unpublished shared content, ES/RAG pending state, and ES/RAG failed state
- **AND** QA MUST verify that raw English backend messages do not appear in primary teacher-facing status copy.
