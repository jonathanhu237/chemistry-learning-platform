## ADDED Requirements

### Requirement: Experiment point content management
The admin experiment management workspace SHALL let teachers manage experiment point identity, media bindings, human-authored point content, related links, publication state, and search indexing state from the experiment context.

#### Scenario: Teacher opens experiment detail workspace
- **WHEN** a teacher opens an experiment detail workspace
- **THEN** the console MUST show the experiment's stable video points
- **AND** each point MUST expose its title, publication status, content completeness, video binding status, related-link status, and search index status where available.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits a point in the experiment workspace
- **THEN** the console MUST allow editing principle mode, equation or text principle value, phenomenon explanation, safety note, and related point links
- **AND** it MUST keep video binding controls in the same point context without making video assets own the learning copy.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes point content from the experiment workspace
- **THEN** the backend MUST validate required fields and persist publication audit data
- **AND** it MUST trigger or queue search index synchronization for the point.

#### Scenario: Teacher views generic video resource page
- **WHEN** a teacher opens the generic video resource page
- **THEN** the page MAY continue to manage asset upload, processing, duplication, preview, and lifecycle
- **AND** it MUST NOT be the primary place for authoring experiment principle, phenomenon explanation, safety note, or related point links.

#### Scenario: Existing point evidence exists
- **WHEN** a point has AI/manual-reviewed evidence bindings for assistant use
- **THEN** the admin point editor MAY expose that evidence only as separate diagnostic or reference context if implemented
- **AND** it MUST NOT publish that evidence as student-facing point content without teacher editing.
