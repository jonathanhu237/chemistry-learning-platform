## MODIFIED Requirements

### Requirement: Mobile assistant starter surface
The student H5 `AI` tab SHALL provide a phone-first fullscreen direct-chat starter before the first assistant turn so students can start asking immediately without passing through a card-based AI center or multi-step prompt picker.

#### Scenario: Student opens global assistant with no prior messages
- **WHEN** an authenticated student opens the `AI` tab with the default `learning_home` context and no chat turns
- **THEN** the app MUST render a fullscreen chat canvas between the app header and bottom navigation
- **AND** the app MUST render the normal free-form composer on the same first screen
- **AND** the app MUST NOT require selecting a prompt type, point, model, attachment, or voice mode before asking.

#### Scenario: Starter appears as low prompt block only
- **WHEN** the global assistant canvas has no chat turns
- **THEN** the app MUST place at most one compact student-facing prompt block near the composer
- **AND** the prompt block MUST NOT be styled as a centered intro card, card grid, or multi-card landing section
- **AND** the page MUST leave a large calm middle canvas above the prompt block.

#### Scenario: Student sends the first question
- **WHEN** the student sends the first free-form question
- **THEN** the app MUST transition into the normal chat stream
- **AND** any follow-up quick prompts shown after the first turn MUST remain compact and MUST NOT reoccupy the entire chat area.

#### Scenario: Starter copy stays student-facing
- **WHEN** the starter surface renders labels, descriptions, status, or prompt text
- **THEN** the copy MUST use concise student-facing chemistry learning language
- **AND** it MUST NOT expose teacher/admin diagnostics, policy codes, raw retrieval traces, implementation jargon, unsupported model controls, upload controls, or voice controls.

## ADDED Requirements

### Requirement: Grok-like root assistant visual target
The student H5 `AI` root SHALL visually approximate the provided Grok-style mobile chat target while remaining consistent with the chemistry course visual system.

#### Scenario: Root assistant fills available phone space
- **WHEN** the `AI` root renders at 360px to 430px CSS-pixel phone widths
- **THEN** the assistant canvas MUST occupy the available route width and height without appearing as a floating card
- **AND** the canvas MUST extend visually close to the route content edges while still respecting safe-area and app shell constraints
- **AND** the chat composer MUST remain above the bottom navigation with visible separation.

#### Scenario: Root assistant top identity is lightweight
- **WHEN** the root assistant first screen renders
- **THEN** the top identity area MUST show concise assistant identity such as `课程 AI` and `AI 学习助手`
- **AND** the history action MUST appear as a compact icon action near the top-right of the chat canvas
- **AND** the identity area MUST NOT become a framed intro card.

#### Scenario: Unsupported controls are absent
- **WHEN** the root assistant composer renders
- **THEN** the composer MUST expose only supported text-entry and send controls
- **AND** it MUST NOT show upload, attachment, model picker, microphone, voice waveform, image generation, or external X/Grok controls.
