## MODIFIED Requirements

### Requirement: Mobile assistant starter surface
The student H5 AI root SHALL prioritize a direct mobile chat composer before any structured starter surface; starter prompts, if present, SHALL be secondary and MUST NOT block free-form asking.

#### Scenario: Student opens global assistant with no prior messages
- **WHEN** an authenticated student opens the `/ai` root with the default `learning_home` context and no chat turns
- **THEN** the app MUST render a mobile chat shell with a visible free-form composer
- **AND** the page MUST NOT require the student to choose a starter prompt, point, or intent before asking.

#### Scenario: Optional starter appears without occupying the primary flow
- **WHEN** optional starter prompts or question directions are shown before the first turn
- **THEN** they MUST remain visually secondary to the free-form composer
- **AND** they MUST NOT reoccupy the entire chat area after the first sent question.

#### Scenario: Starter copy stays student-facing
- **WHEN** optional starter copy renders labels, descriptions, status, or preview text
- **THEN** the copy MUST use student-facing learning language
- **AND** it MUST NOT expose teacher/admin diagnostics, policy codes, raw retrieval traces, or implementation jargon.

### Requirement: Starter intent choices
When the student H5 assistant exposes compact learning-intent choices inspired by the teacher learning assistant, those choices SHALL remain optional secondary controls that preserve direct free-form asking.

#### Scenario: Optional structured starter intents are exposed
- **WHEN** the implementation exposes optional starter intents for `learning_profile`, `experiment_group`, `experiment_detail`, or `learning_point` contexts
- **THEN** the starter surface MUST offer student-readable choices such as observation, phenomenon explanation, principle explanation, or mistake review
- **AND** it MUST include experiment design or comparison intents only when the context contains experiment or point information.

#### Scenario: Intent choice is selected
- **WHEN** the student taps an optional starter intent
- **THEN** the app MUST mark that intent as selected
- **AND** it MUST make the text that will be sent unambiguous before submission.

#### Scenario: Student chooses custom asking
- **WHEN** the student selects a custom asking intent
- **THEN** the app MUST preserve the active assistant context
- **AND** it MUST guide the student to type their own question rather than sending an empty or generic prompt.

### Requirement: Starter question preview and launch
The student H5 assistant SHALL only show starter previews when an optional structured starter is active, and the preview MUST NOT replace the direct composer as the default first-screen action.

#### Scenario: Preview is available for selected optional intent
- **WHEN** the active context and selected optional intent can produce a starter question
- **THEN** the app MUST display a student-readable preview region
- **AND** the preview MUST include the relevant context title or point title when available.

#### Scenario: Student launches optional starter question
- **WHEN** the student activates the optional starter launch action
- **THEN** the app MUST submit the previewed question through the existing student assistant stream endpoint
- **AND** the request MUST include the active `AssistantContext` fields already used by the student assistant.

#### Scenario: Preview and composer both contain text
- **WHEN** a starter preview exists and the student has also typed free-form input
- **THEN** the app MUST make the sent text unambiguous
- **AND** it MUST either send the typed input with the active context or clearly label separate actions for sending the preview versus the typed input.

### Requirement: Active context header
The student H5 assistant SHALL make active contextual chat understandable and dismissible without duplicating separate "current content" cards on the first screen.

#### Scenario: Global context is active
- **WHEN** the assistant context is the default `learning_home`
- **THEN** the root chat shell MUST identify the assistant as a global course Q&A entry
- **AND** it MUST avoid implying that a chapter, experiment, or point is bound.

#### Scenario: Learning or experiment context is active
- **WHEN** the assistant context is provided by a chapter, experiment group, experiment detail, point handoff, video result, or assessment report
- **THEN** the contextual chat shell MUST show the context title and a concise context type cue
- **AND** the subsequent assistant request MUST include available `chapter_id`, `experiment_id`, `point_key`, and `context_summary` values.

#### Scenario: Student clears context
- **WHEN** the student activates the context clear action
- **THEN** the app MUST return to the default `learning_home` assistant context
- **AND** the UI MUST make clear whether existing chat turns were preserved or a new global chat state was started.

### Requirement: Optional experiment starter data
The student H5 assistant SHALL remain useful without loading optional experiment starter data in the global AI root.

#### Scenario: Experiment starter data is not loaded
- **WHEN** the global AI root opens before experiment starter data is available or if an experiment request fails
- **THEN** the direct chat composer MUST remain usable
- **AND** student asking MUST NOT be blocked on experiment data loading.

#### Scenario: Experiment module starter is exposed later
- **WHEN** a later implementation exposes an `按实验提问` path using student-visible modules
- **THEN** the starter MUST load those modules through existing student APIs
- **AND** it MUST NOT introduce a new backend starter-suggestion contract unless a later change explicitly adds one.
