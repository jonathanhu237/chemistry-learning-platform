## ADDED Requirements

### Requirement: Teacher editor friendly guidance uses contextual cards
The teacher catalog editor SHALL present routine guidance and shortcuts as contextual editor cards instead of full-width system alert banners.

#### Scenario: Teacher sees the video upload shortcut
- **WHEN** a teacher opens the video binding panel for a point-capable catalog node
- **THEN** the panel MUST show a compact video resource shortcut card near the panel header
- **AND** the shortcut MUST link to the video resource upload page
- **AND** it MUST NOT use a full-width system alert for the upload hint.

#### Scenario: Teacher reviews static fallback evidence state
- **WHEN** a teacher opens the AI context panel for a point-capable catalog node
- **THEN** the static fallback evidence section MUST show a lifecycle/state transition card
- **AND** the current evidence state MUST be visually highlighted using existing evidence status data
- **AND** the section MUST avoid broad explanatory system alert styling for routine missing, searching, available, stale, or failed states.

#### Scenario: Teacher runs real RAG search diagnostics
- **WHEN** a teacher opens or runs the RAG diagnostics in the AI context panel
- **THEN** visible labels and button text MUST refer to real RAG search
- **AND** the panel MUST show search results or failure state without redundant explanatory alert copy.
