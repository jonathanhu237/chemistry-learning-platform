## MODIFIED Requirements

### Requirement: Student H5 assistant presentation
The student H5 assistant SHALL present model answers, point starter guidance, point context, per-turn status, and source summaries in a student-readable form while preserving existing student guardrail enforcement.

#### Scenario: Student chat renders chemistry answer
- **WHEN** the student assistant streams a markdown or chemistry-formatted answer
- **THEN** the H5 app MUST render the answer with markdown-compatible formatting
- **AND** it MUST keep the streaming fallback behavior for plain text answers

#### Scenario: Student chat receives final response metadata
- **WHEN** the student assistant stream emits a final response with sources
- **THEN** the H5 app MUST retain the final response metadata for that turn
- **AND** it MUST show a compact source or evidence summary suitable for students

#### Scenario: Student chat starts from point context
- **WHEN** a student opens the assistant from a property section or experiment point
- **THEN** the H5 app MUST include the selected chapter, experiment, point, and context summary in the request
- **AND** quick prompts MUST be relevant to the active property or point

#### Scenario: Student point starter copy is guardrail-safe
- **WHEN** the student H5 assistant renders point starter group choices, point choices, templates, preview text, loading text, empty states, or errors
- **THEN** the copy MUST remain student-facing and course-scoped
- **AND** it MUST NOT expose teacher/admin diagnostics, policy codes, raw retrieval traces, RAG internals, evidence review grades, or implementation jargon.

#### Scenario: Redundant bottom status copy is removed
- **WHEN** a student sends or receives an assistant message in the H5 chat
- **THEN** the app MUST NOT render a separate bottom status bubble or text row below the composer solely to repeat states such as generating, completed, or answered
- **AND** assistant running, done, and error state MUST remain visible in or near the relevant assistant message turn.

#### Scenario: Student AI switch is disabled
- **WHEN** student AI entry or student AI capability is disabled by admin settings
- **THEN** the H5 app MUST hide or disable the student assistant entry after app-config refresh
- **AND** the backend MUST continue to reject stale student assistant requests
