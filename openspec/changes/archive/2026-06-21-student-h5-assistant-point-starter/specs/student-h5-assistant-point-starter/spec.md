## ADDED Requirements

### Requirement: Point starter mode entry
The student H5 `问答` tab SHALL offer an optional experiment/video-point starter mode before the first assistant turn while preserving the existing global course Q&A starter.

#### Scenario: Student opens assistant starter
- **WHEN** an authenticated student opens the `问答` tab with no chat turns
- **THEN** the app MUST show a way to choose between global course asking and experiment/video-point asking
- **AND** global course asking MUST remain available without requiring experiment or point selection.

#### Scenario: Student chooses point starter mode
- **WHEN** the student activates the experiment/video-point starter mode
- **THEN** the app MUST reveal point-selection controls within the assistant starter
- **AND** it MUST keep the composer available for free-form asking with the active context.

#### Scenario: Student leaves point starter mode before sending
- **WHEN** the student switches back to global course asking before the first point starter question is sent
- **THEN** the app MUST return to the global starter choices
- **AND** it MUST NOT submit a point-context question or retain a misleading selected point context.

### Requirement: Student-visible experiment data loading
The student H5 assistant point starter SHALL load experiment and point choices only from student-visible APIs and SHALL remain usable if optional point data is unavailable.

#### Scenario: Point mode loads experiment groups
- **WHEN** the student opens point starter mode
- **THEN** the app MUST load available experiment groups through the existing student learning home API or equivalent student-visible data source
- **AND** it MUST NOT use teacher/admin experiment APIs or admin-only experiment objects.

#### Scenario: Student selects an experiment group
- **WHEN** the student chooses an experiment group in point starter mode
- **THEN** the app MUST load that group's student-visible experiments through the existing student experiment-group API
- **AND** it MUST show enough student-readable metadata to distinguish the available experiments.

#### Scenario: Student selects an experiment
- **WHEN** the student chooses an experiment in point starter mode
- **THEN** the app MUST load experiment detail through the existing student experiment-detail API
- **AND** it MUST derive selectable point options from published videos and/or video candidates in that detail payload.

#### Scenario: Optional point data fails
- **WHEN** experiment group or experiment detail loading fails
- **THEN** the point starter MUST show a student-readable retry or fallback state
- **AND** the global course starter and free-form composer MUST remain usable.

### Requirement: Video point option derivation
The student H5 assistant point starter SHALL derive stable, student-readable video point options from student experiment detail data.

#### Scenario: Published video has point metadata
- **WHEN** experiment detail includes videos with `point_key` or `point_title`
- **THEN** the point starter MUST create point options from those videos
- **AND** each option MUST identify the point title and whether it has a published video resource.

#### Scenario: Only video candidates are available
- **WHEN** experiment detail has no usable published video point metadata but includes `video_candidates`
- **THEN** the point starter MUST create deterministic candidate point options from those candidate titles
- **AND** it MUST avoid implying that candidate-only points are playable videos.

#### Scenario: Point list contains duplicate titles
- **WHEN** videos or candidates contain duplicate point titles or keys
- **THEN** the point starter MUST de-duplicate or stabilize rendered options so selecting one point maps to a consistent `point_key`
- **AND** no duplicate React/list keys or ambiguous selected states may appear.

### Requirement: Point starter templates
The student H5 assistant point starter SHALL provide student-readable question templates for the selected experiment/video point.

#### Scenario: Point context supports templates
- **WHEN** a student has selected an experiment and point
- **THEN** the app MUST offer templates including observation, phenomenon explanation, principle explanation, experiment design, comparison, mistake review, and custom asking
- **AND** template labels and descriptions MUST be adapted for students, not copied from admin diagnostics.

#### Scenario: Student selects a template
- **WHEN** the student taps a point starter template
- **THEN** the app MUST mark the selected template
- **AND** it MUST update the starter preview to reflect the selected experiment, point, and template.

#### Scenario: Student selects custom template
- **WHEN** the student selects the custom asking template
- **THEN** the app MUST preserve the selected point context
- **AND** it MUST guide the student to type their own question instead of sending an empty generated question.

### Requirement: Point starter preview and launch
The student H5 assistant point starter SHALL preview the generated point question before sending and SHALL submit it through the existing student assistant stream endpoint.

#### Scenario: Generated preview is available
- **WHEN** the student has selected a point and a structured template
- **THEN** the app MUST display a `准备提问` preview or equivalent preview region
- **AND** the preview MUST include student-readable experiment or point context such as the experiment title, point title, or point index when available.

#### Scenario: Student launches point starter question
- **WHEN** the student activates the point starter launch action
- **THEN** the app MUST send the previewed question through `streamStudentAssistantAsk`
- **AND** the request MUST use `context_type: "learning_point"` with the selected experiment and point context.

#### Scenario: Typed input and preview both exist
- **WHEN** the student has typed free-form input while a generated point preview is visible
- **THEN** the app MUST make it clear whether the send action submits typed input or the preview
- **AND** it MUST NOT silently replace typed student text with a generated point question.

### Requirement: Point-aware assistant context construction
The student H5 assistant point starter SHALL construct point-aware `AssistantContext` values from selected student-visible data without changing the backend request schema.

#### Scenario: Point context is constructed
- **WHEN** the student selects an experiment point for assistant asking
- **THEN** the constructed context MUST include the selected `experiment_id`, `point_key`, relevant `chapter_id` when available, and a concise `context_summary`
- **AND** the context title MUST be the selected point title or a clear fallback point label.

#### Scenario: Request is sent with point context
- **WHEN** the app sends a point starter question
- **THEN** the request MUST include the same `experiment_id`, `point_key`, `chapter_id`, and `context_summary` values from the constructed context
- **AND** it MUST preserve conversation history behavior used by existing assistant chat.

#### Scenario: Backend schema remains unchanged
- **WHEN** point starter is implemented
- **THEN** it MUST use existing student assistant request fields
- **AND** it MUST NOT require a new backend starter-suggestion endpoint or new required assistant request fields.

### Requirement: Point starter transition to normal chat
The student H5 assistant point starter SHALL transition into normal chat after the first point starter or free-form question is sent.

#### Scenario: First point starter question is sent
- **WHEN** the student sends a point starter question
- **THEN** the starter selection surface MUST stop occupying the primary chat area
- **AND** the app MUST show normal user and assistant turns with per-turn running, done, or error state.

#### Scenario: Follow-up question uses selected context
- **WHEN** the student sends a follow-up after launching from a point starter
- **THEN** the assistant request MUST continue to include the active point context unless the student explicitly clears or changes context
- **AND** quick prompts, if shown, MUST remain relevant to the active point context.

#### Scenario: Student clears point context
- **WHEN** the student activates the context clear action after selecting or launching a point context
- **THEN** the app MUST return to the global `learning_home` assistant context
- **AND** it MUST make clear that a new global starter state has begun.
