## ADDED Requirements

### Requirement: Question bank baseline is empty after catalog reset
The system SHALL treat legacy question-bank seed data as invalid after the authoritative catalog reset.

#### Scenario: Catalog reset completes
- **WHEN** the authoritative catalog seed replaces legacy point identity
- **THEN** old question-bank seed rows depending on legacy point identity MUST be deleted, archived, or marked inactive
- **AND** teacher question-bank pages MUST not present those rows as the current default bank.

#### Scenario: Teacher opens question bank before regeneration
- **WHEN** no fresh catalog-node question bank exists
- **THEN** the teacher console MUST show an empty or pending-regeneration state
- **AND** it MUST NOT imply that old questions are still valid for the new catalog.

### Requirement: AI question generation requires catalog-node evidence readiness
AI question generation SHALL be blocked until usable evidence exists for the requested catalog node scope.

#### Scenario: Teacher requests generation for a point
- **WHEN** a teacher requests AI question generation for one or more catalog point nodes
- **THEN** the backend MUST verify that each target point has a fresh catalog-node evidence package or an allowed dynamic RAG evidence package
- **AND** it MUST reject generation if evidence is missing, stale, legacy-keyed, or incompatible with the requested point ids.

#### Scenario: Evidence package uses legacy identity
- **WHEN** an evidence package only references legacy `(experiment_id, point_key)` identity
- **THEN** the generation gate MUST treat it as invalid
- **AND** it MUST return a diagnostic explaining that catalog-node evidence regeneration is required.

#### Scenario: Dynamic RAG evidence is used instead of static binding
- **WHEN** runtime policy permits dynamic RAG evidence for generation and static binding is absent
- **THEN** the backend MUST record that the evidence came from dynamic RAG
- **AND** the generated drafts MUST include source audit metadata derived from that evidence package.

### Requirement: Generated questions use catalog point context
Question generation SHALL consume structured catalog point context, not only generic experiment text.

#### Scenario: Prompt is built for generation
- **WHEN** the backend prepares an AI generation request
- **THEN** it MUST include catalog node id, full catalog path, point title, normalized equations, phenomenon explanation, safety note, related point context, video context, and evidence sources where available
- **AND** it MUST exclude teacher-only teaching notes unless explicitly allowed for teacher-only drafting context.

#### Scenario: Multiple points are targeted
- **WHEN** a generation request targets multiple catalog point nodes
- **THEN** the prompt context MUST preserve each point's identity and evidence separately
- **AND** generated question metadata MUST identify the primary point node ids used by each draft.

### Requirement: Generated drafts remain teacher-reviewed and objective
AI-generated questions SHALL remain drafts until validated and explicitly accepted by a teacher.

#### Scenario: Candidate is generated
- **WHEN** AI generation succeeds
- **THEN** each candidate MUST be stored or returned as a teacher-reviewable draft
- **AND** it MUST NOT become student-facing until a teacher explicitly publishes it.

#### Scenario: Candidate is validated
- **WHEN** a generated candidate is validated
- **THEN** its question type MUST be objective and machine-gradable
- **AND** answer, explanation, primary point node ids, source audit, and evidence lineage MUST be present before publication is allowed.

#### Scenario: Candidate lacks evidence lineage
- **WHEN** a generated candidate lacks compatible catalog-node evidence lineage
- **THEN** publication MUST be blocked
- **AND** the UI MUST guide the teacher to regenerate or refresh evidence.

### Requirement: Coverage and regeneration audit are required
The system SHALL provide coverage and audit reporting for regenerated question banks.

#### Scenario: Regeneration batch completes
- **WHEN** a catalog-node question generation batch completes
- **THEN** the system MUST report counts by chapter, catalog directory, point node, question type, evidence source, accepted drafts, rejected drafts, and unresolved points
- **AND** points without accepted questions MUST be listed.

#### Scenario: Teacher inspects generated bank
- **WHEN** a teacher opens regenerated question-bank content
- **THEN** the console MUST show linked catalog point titles, source/evidence status, deterministic answer data, and generation lineage
- **AND** it MUST not expose invalid legacy point keys as authoritative metadata.
