## ADDED Requirements

### Requirement: Root AI chat history entry
The student H5 AI root SHALL provide a history entry point for reviewing prior student AI conversations from the AI root page.

#### Scenario: Student opens history from AI root
- **WHEN** an authenticated student opens the `/ai` root route
- **THEN** the page MUST show a student-readable history action in the root chat top area
- **AND** activating the action MUST open a history list, panel, or sheet without leaving the AI root route.

#### Scenario: Contextual chat omits history entry
- **WHEN** a student opens the contextual `/ai/chat` detail route from another page
- **THEN** the contextual chat page MUST NOT show the root history action
- **AND** history review MUST remain reachable by returning to the `/ai` root route.

### Requirement: First-round local conversation history
The student H5 AI chat SHALL persist first-round conversation history in client-side browser storage without requiring a backend chat-session migration.

#### Scenario: Root chat is saved
- **WHEN** a student sends a question from the `/ai` root chat shell
- **THEN** the app MUST create or update a local history entry for that conversation
- **AND** the entry MUST include enough information to restore visible user and assistant turns.

#### Scenario: Contextual chat is saved without exposing local history chrome
- **WHEN** a student sends a question from `/ai/chat`
- **THEN** the app MAY save the contextual conversation into the same local history store
- **AND** the contextual page MUST still omit the root history action.

#### Scenario: Student restores a local history entry
- **WHEN** a student selects a history entry from the `/ai` root history list
- **THEN** the root chat shell MUST restore the saved conversation turns
- **AND** follow-up questions MUST send recent restored turns as `conversation_history`.

#### Scenario: No local history exists
- **WHEN** the student opens the history panel and no local conversations are available
- **THEN** the app MUST show an empty state that explains there are no recent AI conversations
- **AND** the student MUST be able to return to the root chat composer.

### Requirement: History rows identify context
The student H5 AI history SHALL identify whether a conversation was global or contextual without exposing teacher/admin diagnostics.

#### Scenario: History row comes from global root chat
- **WHEN** a history entry was created from the `/ai` root route
- **THEN** the row MUST label it as a global course assistant conversation or equivalent student-facing copy.

#### Scenario: History row comes from contextual chat
- **WHEN** a history entry was created from a point, chapter, video result, or assessment context
- **THEN** the row MUST show a concise context title or context type cue
- **AND** it MUST NOT expose raw RAG traces, policy codes, internal node diagnostics, or admin-only metadata.
