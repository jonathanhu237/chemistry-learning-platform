## ADDED Requirements

### Requirement: Root assistant supports learning-background attachment action
The student H5 Atom root assistant SHALL treat the composer `+` as a supported learning-background action while preserving direct free-form asking.

#### Scenario: Root assistant composer renders plus action
- **WHEN** the `/ai` root assistant composer renders
- **THEN** the `+` action MUST be available only as a learning-background picker entry
- **AND** it MUST NOT imply generic file upload, image upload, model selection, microphone input, or unsupported external tools.

#### Scenario: Student asks globally
- **WHEN** the student submits text from the root assistant without selecting a point
- **THEN** the assistant request MUST use the existing active global or restored context
- **AND** the UI MUST NOT block submission with a required point-selection step.

#### Scenario: Student asks with selected point
- **WHEN** the student submits text from the root assistant after selecting a point background
- **THEN** the assistant request MUST use the selected point `AssistantContext`
- **AND** the user-authored question text MUST be preserved without adding visible picker text into the question field.

### Requirement: Root assistant preserves bound context across local history
The student H5 Atom root assistant SHALL preserve selected point context when saving and restoring local chat history.

#### Scenario: Bound point chat is saved
- **WHEN** a student sends the first question from a root chat with a selected point
- **THEN** the local history entry for that conversation MUST include enough context to restore the selected point title, context type, ids, summary, and catalog path
- **AND** restoring the entry MUST continue sending follow-up turns with that restored point context.

#### Scenario: Global chat is saved
- **WHEN** a student sends from the root chat without selecting a point
- **THEN** the local history entry MUST remain a global Atom conversation
- **AND** restoring the entry MUST NOT show a false selected-point chip.

#### Scenario: New root chat starts from restored bound chat
- **WHEN** a restored bound-point conversation is visible
- **AND** the student activates the new-chat action
- **THEN** the root assistant MUST clear the visible conversation and selected point binding
- **AND** the new chat MUST use the default global context.

### Requirement: Root assistant communicates one-point lock
The student H5 Atom root assistant SHALL make the selected point binding understandable before and after the first submitted message.

#### Scenario: Selected point is editable before sending
- **WHEN** the root chat has a selected point and no submitted user message
- **THEN** the selected-point chip MUST communicate that this learning background will be used for the next question
- **AND** the student MUST be able to remove or replace the selected point before submitting.

#### Scenario: Selected point is locked after sending
- **WHEN** the root chat has submitted at least one user message with a selected point context
- **THEN** the selected-point chip MUST communicate that the chat is bound to that point
- **AND** the app MUST require a new chat before binding a different point.
