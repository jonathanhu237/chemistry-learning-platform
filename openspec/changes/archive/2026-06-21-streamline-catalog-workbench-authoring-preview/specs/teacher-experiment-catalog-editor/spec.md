## MODIFIED Requirements

### Requirement: Node editor tabs follow node capability
The right editor SHALL show primary authoring panels based on whether the selected node is a directory or point, and SHALL keep read-only diagnostics out of the primary configuration tab strip.

#### Scenario: Directory node is selected
- **WHEN** a directory node is selected
- **THEN** the editor MUST show only the `内容` primary authoring panel for that directory
- **AND** the directory primary panel MUST focus on directory title and teacher-only teaching note where applicable
- **AND** it MUST NOT show point principle, video binding, related point links, assessment, search-document controls, node status diagnostics, AI context diagnostics, advanced debug controls, or student-card presentation controls as primary tabs.

#### Scenario: Point node is selected
- **WHEN** a point node is selected
- **THEN** the editor MUST show exactly the primary configuration tabs `内容`, `视频`, and `相关实验`
- **AND** those tabs MUST respectively own point learning content, the one experiment-video binding, and the ordered related-experiment learning list
- **AND** the editor MUST NOT show `学生卡片`, `节点状态`, `AI 上下文`, or `高级` as primary configuration tabs.

#### Scenario: Removed node type is selected
- **WHEN** stale data or a stale client references a hybrid or shortcut node
- **THEN** the editor MUST render a controlled migration/unavailable state or normalized directory/point editor
- **AND** it MUST NOT expose hybrid or shortcut editing controls.

### Requirement: Focused selected-node editor information architecture
The right editor SHALL present selected-node editing as a focused workspace with primary authoring fields first and operational/debug fields separated into secondary inspection surfaces.

#### Scenario: Point node default editor opens
- **WHEN** a teacher selects a point node
- **THEN** the default editor view MUST prioritize point title, teacher-only note, principle mode and principle content, phenomenon explanation, safety note, video presence, related experiments, and primary publish actions
- **AND** raw node id, parent id, display order, search-index diagnostics, validation internals, AI/RAG evidence details, and related-link sort internals MUST NOT appear in the default point content view.

#### Scenario: Directory node default editor opens
- **WHEN** a teacher selects a directory node
- **THEN** the default editor view MUST prioritize directory title and teacher-only note where applicable
- **AND** it MUST NOT show point principle, video binding, related experiment links, assessment, search-document controls, student-card description, card image, card icon, card accent, or card layout as directory-owned fields.

#### Scenario: Teacher needs less-common metadata
- **WHEN** a teacher opens node status, AI context, or advanced/debug inspection
- **THEN** the editor MUST open those details from a secondary `高级` or `更多` entry
- **AND** those details MUST be visually and navigationally secondary to the content/video/related authoring workflow.

#### Scenario: Selected node header renders
- **WHEN** any catalog node is selected
- **THEN** the editor MUST show a stable selected-node header with primary status, node kind, title, breadcrumb path, preview action, diagnostics entry, and primary publication/archive actions
- **AND** point nodes MUST show compact binary video status such as `有视频` or `无视频` in the header or video panel.

#### Scenario: Node status is needed during authoring
- **WHEN** a selected node has missing content, missing video, sync attention, or structural exception status
- **THEN** the header and tree MUST keep a compact primary status signal visible
- **AND** detailed status conditions MUST remain available through the secondary diagnostics surface instead of adding another primary tab.

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

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Directory card editor
**Reason**: Manual directory card configuration is no longer a useful product surface and is being removed from the database/API contract.

**Migration**: Directory student presentation is derived from directory title, structure, and stable student frontend defaults. Existing stored card values are discarded by the destructive migration.

### Requirement: Point card editor remains constrained
**Reason**: Even constrained point-card overrides create a second authoring model that competes with the point primitive and real student preview.

**Migration**: Point cards derive from point title, learning content summary where available, video presence, and bound video thumbnail where available. Existing stored point-card overrides are discarded by the destructive migration.
