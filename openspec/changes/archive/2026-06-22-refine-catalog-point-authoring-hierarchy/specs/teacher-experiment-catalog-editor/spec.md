## MODIFIED Requirements

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
- **THEN** the default editor view MUST prioritize directory title and teacher-only note where applicable
- **AND** it MUST NOT show point principle, video binding, related experiment links, assessment, search-document controls, student-card description, card image, card icon, card accent, or card layout as directory-owned fields.

#### Scenario: Teacher needs less-common metadata
- **WHEN** a teacher opens node status, AI context, or advanced/debug inspection
- **THEN** the editor MUST open those details from a secondary `更多` entry
- **AND** those details MUST be visually and navigationally secondary to the content/video/related authoring workflow.

#### Scenario: Selected node header renders
- **WHEN** any catalog node is selected
- **THEN** the editor MUST show a stable selected-node header with primary status, node kind, title, breadcrumb path, compact readiness/status summaries, and one state-machine-driven primary action where an action is needed
- **AND** generic inspection actions such as `预览学生端`, `节点状态`, `点位检索诊断`, and `高级调试` MUST live in a secondary `更多` menu
- **AND** lifecycle actions such as unpublish and archive MUST NOT be rendered as peers of preview or diagnostics in the main header row
- **AND** point nodes MUST show compact binary video status such as `有视频` or `无视频` in the header or video panel.

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

## ADDED Requirements

### Requirement: Selected-point primary action state machine
The selected-point header SHALL compute at most one primary action from resolved node status, shared content state, video readiness, and student visibility.

#### Scenario: Point is archived
- **WHEN** a selected point is archived
- **THEN** the primary action MUST be `恢复点位`
- **AND** preview, diagnostics, and destructive actions MUST remain secondary.

#### Scenario: Point has structural errors
- **WHEN** a selected point has blocking validation or identity errors
- **THEN** the primary action MUST be `查看问题`
- **AND** publish actions MUST NOT be shown as the primary action.

#### Scenario: Point content is incomplete
- **WHEN** a selected point is missing required learning content fields
- **THEN** the primary action MUST be `编辑内容`
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
