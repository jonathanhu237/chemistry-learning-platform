## MODIFIED Requirements

### Requirement: Student H5 assistant presentation
The student H5 assistant SHALL present model answers, point context, and source summaries in a dedicated `问答` tab while preserving existing student guardrail enforcement.

#### Scenario: Student opens assistant tab
- **WHEN** a student opens `问答` from the authenticated bottom navigation
- **THEN** the H5 app MUST render a full-page student assistant surface
- **AND** it MUST NOT require or expose a global floating `问 AI` button on authenticated learning pages.

#### Scenario: Student chat renders chemistry answer
- **WHEN** the student assistant streams a markdown or chemistry-formatted answer
- **THEN** the H5 app MUST render the answer with markdown-compatible formatting
- **AND** it MUST keep the streaming fallback behavior for plain text answers.

#### Scenario: Student chat receives final response metadata
- **WHEN** the student assistant stream emits a final response with sources
- **THEN** the H5 app MUST retain the final response metadata for that turn
- **AND** it MUST show a compact source or evidence summary suitable for students.

#### Scenario: Student chat starts from global context
- **WHEN** the student opens the assistant tab without a current chapter or point handoff
- **THEN** the app MUST submit assistant requests with a valid student context such as `learning_home`
- **AND** the page MUST provide student-readable starter prompts or an empty state for course questions.

#### Scenario: Student chat starts from point context
- **WHEN** a student opens the assistant from a property section or experiment point handoff
- **THEN** the H5 app MUST include the selected chapter, experiment, point, and context summary in the request
- **AND** the assistant tab MUST show the active context as a visible, dismissible context cue rather than trapping the student in that point.

#### Scenario: Student AI switch is disabled
- **WHEN** student AI entry or student AI capability is disabled by admin settings
- **THEN** the H5 app MUST hide or disable the student assistant tab after app-config refresh
- **AND** the backend MUST continue to reject stale student assistant requests.
