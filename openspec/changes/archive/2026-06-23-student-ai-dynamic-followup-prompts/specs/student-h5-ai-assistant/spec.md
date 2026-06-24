## ADDED Requirements

### Requirement: Dynamic follow-up prompts
The student H5 Atom assistant SHALL display model-generated follow-up prompts only for the latest successful assistant turn.

#### Scenario: Successful answer returns follow-up prompts
- **WHEN** the student assistant stream emits a successful `final` event for a completed answer
- **THEN** the final response MAY include `suggested_prompts` as an array of student-facing follow-up questions
- **AND** the H5 app MUST store those suggestions on that assistant turn's metadata
- **AND** the H5 app MUST render the suggestions in the quick prompt row when at least one valid suggestion is present.

#### Scenario: Suggestions are absent
- **WHEN** a successful `final` event does not include valid `suggested_prompts`
- **THEN** the H5 app MUST NOT render static fallback prompt chips for that turn
- **AND** the chat composer MUST remain usable for free-form student input.

#### Scenario: Turn is still streaming
- **WHEN** a student sends a question and the assistant turn is loading or streaming
- **THEN** the H5 app MUST hide any previous quick prompt suggestions
- **AND** it MUST NOT show new suggestions until the current turn receives a successful `final` event.

#### Scenario: Assistant turn fails
- **WHEN** the student assistant stream emits an `error` event or the frontend catches a failed assistant request
- **THEN** the H5 app MUST show no follow-up prompt chips for that failed turn
- **AND** stale suggestions from previous successful turns MUST remain hidden.

#### Scenario: New successful turn replaces previous suggestions
- **WHEN** a later assistant turn completes successfully with valid `suggested_prompts`
- **THEN** the quick prompt row MUST show only that latest turn's suggestions
- **AND** suggestions from earlier turns MUST NOT be accumulated, merged, or reused.

#### Scenario: Restored history has suggestions
- **WHEN** the student restores a local chat history entry whose latest assistant turn includes valid `suggested_prompts`
- **THEN** the H5 app MAY render those latest-turn suggestions
- **AND** activating a suggestion MUST submit it using the restored active context and restored visible conversation history.

### Requirement: Follow-up prompt stream contract
The student H5 assistant stream SHALL return follow-up prompts as sanitized student-only final metadata without changing the existing answer streaming contract.

#### Scenario: Backend attaches suggestions to final metadata
- **WHEN** `/api/student/assistant/ask/stream` completes a student answer successfully
- **THEN** the backend SHOULD attempt to generate follow-up prompts from the current student question, completed answer, active assistant context, and recent conversation history
- **AND** the backend MUST attach valid suggestions as `response.suggested_prompts` on the `final` event rather than as answer text.

#### Scenario: Suggestion generation fails
- **WHEN** the answer succeeds but follow-up suggestion generation fails, times out, returns malformed output, or filters to zero valid suggestions
- **THEN** the backend MUST still send the successful answer final event
- **AND** the backend MUST omit `suggested_prompts` or send it as an empty array
- **AND** the frontend MUST render no quick prompt chips for that turn.

#### Scenario: Suggestion count is sanitized
- **WHEN** the model returns follow-up suggestions
- **THEN** the backend MUST keep at most five valid suggestions
- **AND** the backend MAY return fewer than three suggestions when only one or two valid suggestions remain after filtering
- **AND** the frontend MUST display any valid suggestions returned by the backend.

#### Scenario: Suggestion text is sanitized
- **WHEN** a model-generated follow-up suggestion is evaluated for display
- **THEN** the backend MUST trim whitespace, remove empty values, remove duplicates, and reject suggestions outside the 8-24 visible-character range
- **AND** the backend MUST reject values that are not plain student-facing question strings.

#### Scenario: Static context prompts no longer drive post-turn chips
- **WHEN** a chat turn has started or completed
- **THEN** the H5 app MUST NOT render post-turn quick prompt chips from frontend-authored `AssistantContext.prompts`
- **AND** any retained `AssistantContext.prompts` field MUST NOT override latest-turn model-generated suggestions.

#### Scenario: Student activates a generated suggestion
- **WHEN** the student taps a displayed follow-up suggestion
- **THEN** the H5 app MUST submit the suggestion text through the existing student assistant stream path
- **AND** the request MUST include the current active assistant context and recent conversation history exactly as a manually typed follow-up would.
