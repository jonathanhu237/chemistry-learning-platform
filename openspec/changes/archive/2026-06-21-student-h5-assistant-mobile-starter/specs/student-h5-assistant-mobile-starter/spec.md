## ADDED Requirements

### Requirement: Mobile assistant starter surface
The student H5 `问答` tab SHALL provide a phone-first starter surface before the first assistant turn so students can start from a useful course question without needing to invent prompt wording from scratch.

#### Scenario: Student opens global assistant with no prior messages
- **WHEN** an authenticated student opens the `问答` tab with the default `learning_home` context and no chat turns
- **THEN** the app MUST render a mobile starter surface instead of only a blank chat stream
- **AND** the starter surface MUST present student-readable course question directions such as复习顺序, 实验现象, 元素性质联系, and 易错点
- **AND** the normal free-form composer MUST remain available on the same screen.

#### Scenario: Starter appears only before the first turn
- **WHEN** the student sends the first starter or free-form question
- **THEN** the app MUST transition into the normal chat stream
- **AND** any follow-up quick prompts shown after the first turn MUST remain compact and MUST NOT reoccupy the entire chat area.

#### Scenario: Starter copy stays student-facing
- **WHEN** the starter surface renders labels, descriptions, status, or preview text
- **THEN** the copy MUST use student-facing learning language
- **AND** it MUST NOT expose teacher/admin diagnostics, policy codes, raw retrieval traces, or implementation jargon.

### Requirement: Starter intent choices
The student H5 assistant starter SHALL offer compact learning-intent choices inspired by the teacher learning assistant while adapting labels and density for phone use.

#### Scenario: Context supports structured starter intents
- **WHEN** the active assistant context is `learning_profile`, `experiment_group`, `experiment_detail`, or `learning_point`
- **THEN** the starter surface MUST offer intent choices including at least observation, phenomenon explanation, principle explanation, and mistake review
- **AND** it MUST include experiment design or comparison intents when the context contains experiment or point information.

#### Scenario: Intent choice is selected
- **WHEN** the student taps a starter intent
- **THEN** the app MUST mark that intent as selected
- **AND** it MUST update the starter question preview to match the active context and selected intent.

#### Scenario: Student chooses custom asking
- **WHEN** the student selects the custom asking intent
- **THEN** the app MUST preserve the active assistant context
- **AND** it MUST guide the student to type their own question rather than sending an empty or generic prompt.

### Requirement: Starter question preview and launch
The student H5 assistant starter SHALL show the question that will be sent before launching a structured starter question.

#### Scenario: Preview is available for selected intent
- **WHEN** the active context and selected intent can produce a starter question
- **THEN** the app MUST display a `准备提问` style preview or equivalent student-readable preview region
- **AND** the preview MUST include the relevant context title or point title when available.

#### Scenario: Student launches starter question
- **WHEN** the student activates the starter launch action
- **THEN** the app MUST submit the previewed question through the existing student assistant stream endpoint
- **AND** the request MUST include the active `AssistantContext` fields already used by the student assistant.

#### Scenario: Preview and composer both contain text
- **WHEN** a starter preview exists and the student has also typed free-form input
- **THEN** the app MUST make the sent text unambiguous
- **AND** it MUST either send the typed input with the active context or clearly label separate actions for sending the preview versus the typed input.

### Requirement: Active context header
The student H5 assistant starter SHALL make the active assistant context visible, understandable, and dismissible without duplicating separate "current content" cards on the first screen.

#### Scenario: Global context is active
- **WHEN** the assistant context is the default `learning_home`
- **THEN** the merged context header or equivalent context area MUST identify the assistant as a global course Q&A entry
- **AND** it MUST avoid implying that a chapter, experiment, or point is bound.

#### Scenario: Learning or experiment context is active
- **WHEN** the assistant context is provided by a chapter, experiment group, experiment detail, or point handoff
- **THEN** the merged context header or equivalent context area MUST show the context title and a concise context type cue
- **AND** the subsequent assistant request MUST include the same `chapter_id`, `experiment_id`, `point_key`, and `context_summary` values when present.

#### Scenario: Student clears context
- **WHEN** the student activates the context clear action
- **THEN** the app MUST return to the default `learning_home` assistant context
- **AND** the UI MUST make clear whether existing chat turns were preserved or a new starter state was started.

### Requirement: Optional experiment starter data
The student H5 assistant SHALL remain useful with or without optional student-visible experiment data in the global starter.

#### Scenario: Experiment starter data is not loaded
- **WHEN** the global assistant starter opens before experiment data is available or if the experiment request fails
- **THEN** the starter MUST still provide general course question directions and free-form input
- **AND** it MUST NOT block student asking on experiment data loading.

#### Scenario: Experiment module starter is exposed
- **WHEN** the implementation exposes an `按实验提问` path using student-visible modules
- **THEN** the starter MUST load those modules through existing student APIs
- **AND** it MUST NOT introduce a new backend starter-suggestion contract unless a later change explicitly adds one.
