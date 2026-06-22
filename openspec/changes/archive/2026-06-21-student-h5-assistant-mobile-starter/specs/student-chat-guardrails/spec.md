## MODIFIED Requirements

### Requirement: Student H5 assistant presentation
The student H5 assistant SHALL present starter guidance, model answers, point context, chat status, and source summaries in a student-readable form while preserving existing student guardrail enforcement.

#### Scenario: Student chat renders chemistry answer
- **WHEN** the student assistant streams a markdown or chemistry-formatted answer
- **THEN** the H5 app MUST render the answer with markdown-compatible formatting
- **AND** it MUST support student-facing chemistry notation used elsewhere in the student H5, including formulas rendered by the shared student markdown or equivalent chemistry renderer
- **AND** it MUST keep the streaming fallback behavior for plain text answers.

#### Scenario: Student chat receives final response metadata
- **WHEN** the student assistant stream emits a final response with sources
- **THEN** the H5 app MUST retain the final response metadata for that turn
- **AND** it MUST show a compact source or evidence summary suitable for students
- **AND** it MUST NOT show raw retrieval traces, rerank scores, guardrail arrays, runtime health, or JSON diagnostics in the student chat surface.

#### Scenario: Student chat starts from global context
- **WHEN** a student opens the assistant from the bottom navigation without a current chapter, experiment, or point handoff
- **THEN** the H5 app MUST submit assistant requests with a valid `learning_home` context
- **AND** the page MUST provide starter guidance for ordinary course questions before the first turn.

#### Scenario: Student chat starts from point context
- **WHEN** a student opens the assistant from a property section or experiment point
- **THEN** the H5 app MUST include the selected chapter, experiment, point, and context summary in the request
- **AND** quick prompts or starter intents MUST be relevant to the active property or point
- **AND** the active context MUST be visible and dismissible rather than trapping the student in that point.

#### Scenario: Student chat shows streaming progress
- **WHEN** the student assistant request is running and no final answer has arrived
- **THEN** the H5 app MUST show an in-chat running state near the active assistant turn
- **AND** the running state MUST use student-readable language such as checking scope, looking up course material, or generating an answer
- **AND** it MUST fall back to a generic generating state when stream status text is unavailable.

#### Scenario: Student chat handles failure
- **WHEN** a student assistant request fails
- **THEN** the H5 app MUST show the failure in the active chat turn or composer area
- **AND** the student MUST remain able to edit or send another question without reloading the page.

#### Scenario: Student AI switch is disabled
- **WHEN** student AI entry or student AI capability is disabled by admin settings
- **THEN** the H5 app MUST hide or disable the student assistant entry after app-config refresh
- **AND** the backend MUST continue to reject stale student assistant requests.
