## MODIFIED Requirements

### Requirement: Existing experiment video point binding
The system SHALL use existing catalog point nodes as the final binding target for demo and post-learning question banks.

#### Scenario: Video point is used for the demo
- **WHEN** a point-aware demo binding is created
- **THEN** it SHALL reference an existing point node id from the published or teacher-reviewed catalog
- **AND** it SHALL include the human-readable point title, canonical source chunk ids, legacy mapping when applicable, and reviewer note.

#### Scenario: Coverage concept is not a point node
- **WHEN** a method or conclusion concept such as CCl4 observation or oxidation order is recorded
- **THEN** it MAY be stored as a coverage tag
- **AND** it SHALL NOT replace the existing point node id as the final binding target.

#### Scenario: Source evidence is insufficient
- **WHEN** a candidate binding cannot be justified by canonical evidence
- **THEN** it SHALL be marked as `needs_evidence`
- **AND** it SHALL NOT be used as an accepted question binding.

### Requirement: Manual point binding authority
The system SHALL treat manual review as the authority for final question-to-point-node bindings.

#### Scenario: Candidate binding is suggested automatically
- **WHEN** a candidate binding is suggested by keyword, embedding, model output, or legacy point-key mapping
- **THEN** it SHALL remain provisional until a reviewer records an accepted, rejected, or uncertain decision.

#### Scenario: Reviewer accepts a binding
- **WHEN** a reviewer accepts a question-to-point binding
- **THEN** the binding SHALL record the linked point node id, binding role, evidence chunk ids, reviewer note, and confidence.

#### Scenario: Teacher-authored point knowledge exists
- **WHEN** a point has teacher-authored principle, phenomenon explanation, safety note, related links, or teacher-only note
- **THEN** these fields MAY help reviewers understand the student page context
- **AND** they SHALL NOT replace canonical evidence chunk ids required for accepted evidence-backed bindings.

## ADDED Requirements

### Requirement: Point-node assessment handoff
The student point detail page SHALL start post-learning assessment with stable point-node context.

#### Scenario: Student starts test from point detail
- **WHEN** a student taps the fixed test handoff from a point detail page
- **THEN** the assessment session MUST include the canonical point node id and chapter context
- **AND** it MAY include the opening catalog path for analytics and return behavior.

#### Scenario: Assessment result is stored
- **WHEN** a student submits answers for a point-linked assessment
- **THEN** the result metadata MUST retain the point node id
- **AND** reports and analytics MUST resolve point title through the catalog node model.
