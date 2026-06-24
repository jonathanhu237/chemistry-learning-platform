## MODIFIED Requirements

### Requirement: Teacher preview is a secondary inspection action
The selected-node editor SHALL treat student preview as a secondary inspection action that can render non-published directory and point states.

#### Scenario: Teacher previews a draft point
- **WHEN** a teacher chooses `预览学生端` for a non-published but renderable point
- **THEN** the system MUST open a preview scoped to that point
- **AND** the preview MUST render the current draft content, missing-content placeholders, or missing-video state as applicable.

#### Scenario: Teacher previews a draft directory
- **WHEN** a teacher chooses `预览学生端` for a directory node
- **THEN** the system MUST open a preview scoped to that directory
- **AND** the preview MUST render the student-facing catalog directory page with that directory selected
- **AND** it MUST include renderable child directories and child points in catalog order without requiring the teacher to open the full student sandbox.

#### Scenario: Preview action is shown
- **WHEN** a directory or point node is selected
- **THEN** `预览学生端` MUST be available from the secondary `更多` menu or equivalent selected-node preview affordance
- **AND** it MUST NOT occupy the header primary action position.

#### Scenario: Directory preview does not imply point editing controls
- **WHEN** a directory node is selected
- **THEN** the editor MAY offer the selected-node preview action
- **AND** it MUST NOT expose point-only video binding, point detail, related experiment, or learning-card editing controls as if the directory were a point.

### Requirement: Header preview and diagnostics actions
The selected-node header SHALL provide the entry points for student preview and read-only diagnostics.

#### Scenario: Teacher previews a selected node
- **WHEN** a directory or point node is selected
- **THEN** the header MUST show a student preview action such as `预览学生端` or `预览学习卡片`
- **AND** the action MUST launch the teacher-authorized student preview flow for that selected node
- **AND** the preview shell MUST allow selecting from a small set of standard phone presets while keeping the student page read-only.

#### Scenario: Teacher opens diagnostics
- **WHEN** a teacher opens the header `高级` or `更多` action
- **THEN** the menu MUST provide access to `节点状态`, `AI 上下文`, and `高级调试`
- **AND** choosing one MUST open the corresponding inspection surface without changing the primary authoring tab selection.

#### Scenario: Browser blocks auxiliary window
- **WHEN** the diagnostics or preview window cannot be opened
- **THEN** the teacher frontend MUST show a controlled fallback such as an in-app route, modal, or drawer
- **AND** the fallback MUST preserve the same separation between authoring and diagnostics.
