# catalog-node-status-model Specification

## Purpose
Define the teacher-facing catalog node status read model so readiness, visibility, and downstream ES/RAG consumption are presented as separate product states instead of raw validation strings.
## Requirements
### Requirement: Node status separates readiness, visibility, and downstream consumption
The system SHALL derive a node status read model that keeps core authoring readiness, student visibility, and asynchronous ES/RAG consumption as separate status groups.

#### Scenario: Point node status is requested
- **WHEN** the teacher frontend requests a point node card, detail, or status payload
- **THEN** the response MUST provide or allow deriving one `node_status.primary_state`
- **AND** it MUST keep `core_readiness`, `visibility`, `async_consumption`, and detailed `conditions` as separate concepts
- **AND** the frontend MUST NOT need to reinterpret raw validation strings as the authoritative product status.

#### Scenario: Directory node status is requested
- **WHEN** the teacher frontend requests a directory node card, detail, or status payload
- **THEN** the response MUST provide or allow deriving one directory-level `node_status.primary_state`
- **AND** it MUST expose descendant action counts separately from the directory's own publication/archive state.

#### Scenario: Raw validation still exists
- **WHEN** backend validation errors, validation warnings, ES job state, or RAG job state exist for the same node
- **THEN** the node status model MUST classify each teacher-visible issue into a status group
- **AND** raw validation arrays MUST remain lower-level diagnostic inputs rather than the teacher-facing status model.

### Requirement: Point core readiness uses three learning fields and one experiment video
The system SHALL treat a point's core product primitive as three learning fields plus one experiment video presence state.

#### Scenario: Point has complete content and video
- **WHEN** a point has all three required learning fields filled and one experiment video present
- **THEN** `core_readiness.content_fields` MUST be `complete`
- **AND** `core_readiness.video` MUST be `present`
- **AND** the core readiness group MUST NOT create missing-content or missing-video blocking conditions.

#### Scenario: Point is missing one or more learning fields
- **WHEN** a point has no saved shared learning content or lacks any required learning field such as principle content, phenomenon explanation, or safety note
- **THEN** `core_readiness.content_fields` MUST be `missing`
- **AND** the status conditions MUST list the missing fields with teacher-readable Chinese names
- **AND** the primary state MUST prioritize content completion ahead of video and downstream ES/RAG state.

#### Scenario: Point has no experiment video
- **WHEN** a point has complete learning content and no usable experiment video binding for the teacher-facing point model
- **THEN** `core_readiness.video` MUST be `absent`
- **AND** the teacher-facing copy MUST use binary wording equivalent to `无视频`
- **AND** it MUST NOT describe the condition as "at least one publishable video" or as a video count requirement.

#### Scenario: Legacy data contains multiple bindings
- **WHEN** legacy or imported data contains multiple media bindings for one point
- **THEN** the teacher-facing point status MUST still reduce video readiness to `有视频` or `无视频`
- **AND** any multi-binding cleanup warning MUST appear only as an advanced diagnostic condition.

### Requirement: Primary node state follows stable priority rules
The system SHALL choose a single primary node state using stable priority rules so every tree row can remain lightweight.

#### Scenario: Multiple status conditions apply to one point
- **WHEN** a point has several conditions across core readiness, visibility, and async consumption
- **THEN** the system MUST choose exactly one `primary_state`
- **AND** the chosen state MUST follow the priority order `archived`, `blocked`, `needs_content`, `needs_video`, `draft`, `ready`, `published`, `sync_attention`
- **AND** the remaining conditions MUST stay available in the selected-node status panel.

#### Scenario: Structural blocked state is presented as an exception
- **WHEN** the chosen `primary_state` is `blocked`
- **THEN** teacher-facing labels MUST call it `异常`
- **AND** tree markers, selected-node tags, and summary cards MUST use the red error treatment instead of the yellow warning treatment.

#### Scenario: Core readiness is incomplete while sync state also failed
- **WHEN** a point is missing content or video and its ES/RAG job state is failed
- **THEN** the primary state MUST be `needs_content` or `needs_video` according to the core-readiness priority
- **AND** the ES/RAG failure MUST remain in the async-consumption condition group.

#### Scenario: Published point has failed downstream consumption
- **WHEN** a point is otherwise core-complete and student-visible but ES or RAG consumption is failed or unavailable
- **THEN** the primary state MUST be `sync_attention`
- **AND** the detailed condition MUST make clear that student-visible content readiness is separate from the downstream failure.

#### Scenario: Downstream work is pending or stale
- **WHEN** ES or RAG consumption is pending, running, or stale for a point
- **THEN** the primary state MUST NOT be replaced by a sync state
- **AND** the async status MUST appear in the sync diagnostics group and relevant filters.

### Requirement: Placement and canonical point visibility remain explicit
The system SHALL preserve the distinction between placement node visibility and shared canonical point content visibility in node status.

#### Scenario: Placement is published but shared content is not published
- **WHEN** a placement node is published but its shared canonical point content is missing, draft, or unpublished
- **THEN** `visibility.placement` MUST reflect the published placement state
- **AND** `visibility.shared_content` MUST reflect the non-published shared content state
- **AND** `visibility.student_available` MUST be `true` unless the node has structural errors or an archived shared identity
- **AND** the student detail response MUST be allowed to fall back to the placement title and empty learning fields.

#### Scenario: Student can open a point detail
- **WHEN** the placement path is student-visible and the shared point identity is not archived
- **THEN** `visibility.student_available` MUST be `true`
- **AND** the status panel MUST communicate that path visibility is separate from learning-content completeness.

#### Scenario: Teacher edits a reused shared point
- **WHEN** a selected placement is backed by a shared canonical experiment point
- **THEN** the status panel MUST show both the placement node identity and the shared experiment identity
- **AND** it MUST explain when content/video/AI changes affect every placement that reuses that canonical point.

### Requirement: Directory status aggregates descendant actionability
The system SHALL summarize directory status from child actionability without exposing every descendant implementation detail in the default tree row.

#### Scenario: Directory contains incomplete descendant points
- **WHEN** a directory contains descendant points that need content, video, or visibility work
- **THEN** the directory status MUST expose an aggregate action count
- **AND** the default row MUST show at most one aggregate status marker and one compact count.

#### Scenario: Directory contains descendant sync failures only
- **WHEN** a directory's descendants are core-complete and student-visible but have ES/RAG failed or unavailable states
- **THEN** the directory status MUST expose sync attention in an aggregate or filterable form
- **AND** it MUST NOT render separate ES and RAG badges for every descendant in the default tree.

#### Scenario: Directory is selected
- **WHEN** a teacher selects a directory node
- **THEN** the node status panel MUST show grouped descendant issue summaries
- **AND** each group MUST let the teacher navigate, filter, or search toward the affected descendant nodes.

### Requirement: Teacher-facing status copy is localized and action-oriented
The system SHALL expose node status messages and actions using Chinese teacher-facing product language.

#### Scenario: Backend has canonical-content validation errors
- **WHEN** a point has an internal validation message such as `Canonical point content must be saved before publishing`
- **THEN** the teacher-facing status condition MUST translate it into Chinese product copy
- **AND** it MUST explain the needed action in terms of completing or saving shared point content.

#### Scenario: Teacher opens advanced diagnostics
- **WHEN** raw ids, raw backend messages, job payloads, or implementation enum values are useful for diagnosis
- **THEN** they MUST be confined to an advanced or debug surface
- **AND** they MUST NOT appear as primary tree row text or primary status panel copy.

#### Scenario: Assistive technology reads a status marker
- **WHEN** a status marker is rendered in the tree, header, or status panel
- **THEN** it MUST have a Chinese accessible label
- **AND** the label MUST name the status group or action rather than only color or icon shape.

### Requirement: Node status supports focused workbench filters
The system SHALL support focused status filters so complexity is carried by views rather than by dense row decorations.

#### Scenario: Teacher filters to work needing action
- **WHEN** the teacher activates a filter such as `待处理`, `缺内容`, or `缺视频`
- **THEN** the tree or results surface MUST show affected nodes with enough ancestors to preserve catalog context
- **AND** the filter MUST be based on node status conditions rather than string matching raw validation text.

#### Scenario: Teacher filters to sync exceptions
- **WHEN** the teacher activates a sync-exception filter
- **THEN** the result MUST include nodes with failed or unavailable ES/RAG consumption
- **AND** it MUST NOT include ordinary pending, running, or stale states unless the filter explicitly asks for them.

#### Scenario: Teacher clears a filter
- **WHEN** the teacher clears status filtering
- **THEN** the default tree MUST return to the lightweight navigation view
- **AND** rows MUST again show only the primary row marker and compact count allowed by the tree status rules.

### Requirement: Missing learning fields are structured
The node status model SHALL expose missing learning fields with stable identifiers and teacher-readable labels.

#### Scenario: Point is missing experiment principle only
- **WHEN** a point lacks active experiment principle content but has phenomenon explanation and safety note
- **THEN** `core_readiness.content_fields` MUST be `missing`
- **AND** the status payload MUST identify the missing field with a stable key for experiment principle
- **AND** teacher-facing copy MUST say `缺少实验原理` rather than listing fields that are already complete.

#### Scenario: Point is missing two learning fields
- **WHEN** a point is missing experiment principle and phenomenon explanation but has safety note
- **THEN** the status payload MUST identify only those two missing fields
- **AND** teacher-facing copy MUST say `缺少实验原理、现象解释`.

#### Scenario: Point has no saved learning content
- **WHEN** a point has no saved shared learning content
- **THEN** the status payload MUST identify experiment principle, phenomenon explanation, and safety note as missing
- **AND** the primary state MUST remain `needs_content`.

#### Scenario: Missing-field copy is localized
- **WHEN** the frontend renders node status, tooltips, filter chips, or inline editor guidance
- **THEN** it MUST use the teacher-readable labels from the status contract or an equivalent stable label map
- **AND** it MUST NOT parse localized status sentences to decide which field is missing.

### Requirement: Directory aggregates include filterable state and missing-field counts
Directory node status SHALL expose descendant aggregates that cover every status filter and every missing-content field facet.

#### Scenario: Directory contains published descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `published`
- **THEN** `core_readiness.descendant_status_counts.published` MUST reflect that count
- **AND** the `已发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains ready descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `ready`
- **THEN** `core_readiness.descendant_status_counts.ready` MUST reflect that count
- **AND** the `待发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains draft descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `draft`
- **THEN** `core_readiness.descendant_status_counts.draft` MUST reflect that count
- **AND** the `待发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains missing-field descendants
- **WHEN** a directory contains descendant points missing experiment principle, phenomenon explanation, or safety note
- **THEN** directory status MUST expose descendant missing-field counts for each missing field key
- **AND** focused missing-field filters MUST be able to keep the directory visible.

#### Scenario: Directory action count is computed
- **WHEN** a directory has descendant status counts for blocked, needs content, needs video, ready, draft, or sync attention
- **THEN** its descendant action count MUST remain a compact workflow count
- **AND** published descendants MUST NOT increase the action count solely because they are published.

### Requirement: Chapter summary exposes missing-field counts
The chapter tree summary SHALL expose missing-field counts for the required student-visible learning fields.

#### Scenario: Chapter has missing content details
- **WHEN** the chapter summary is requested
- **THEN** it MUST include the existing coarse point status counts
- **AND** it MUST include counts for missing experiment principle, missing phenomenon explanation, and missing safety note.

#### Scenario: Missing-field filter chips are rendered
- **WHEN** the teacher frontend renders focused missing-field filter chips
- **THEN** each chip count MUST come from chapter-level missing-field counts
- **AND** zero-count chips MAY remain visible in a low-emphasis disabled or inactive state but MUST NOT show misleading non-zero values.

### Requirement: Incomplete content guidance is inline and targetable
The teacher content editor SHALL surface missing-content guidance inline with the affected student-visible fields.

#### Scenario: Selected point is missing fields
- **WHEN** the selected point status reports one or more missing learning fields
- **THEN** the content editor MUST show a compact inline warning summary near `学生可见内容`
- **AND** the summary MUST name only the missing fields.

#### Scenario: Teacher activates a missing-field link
- **WHEN** the teacher clicks or keyboard-activates a missing-field name in the inline summary
- **THEN** the editor MUST move focus to the corresponding field or field group
- **AND** it MUST NOT navigate away from the selected point.

#### Scenario: Teacher is typing incomplete content
- **WHEN** the teacher is editing a point with missing content
- **THEN** the inline guidance MUST not block typing, autosave, preview, or mode switching
- **AND** publication validation remains responsible for blocking publish attempts that require complete content.
