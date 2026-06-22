## MODIFIED Requirements

### Requirement: Existing video point binding
The system SHALL bind regenerated experiment questions to existing canonical experiment points while preserving placement context for chapter/path presentation.

#### Scenario: Question is accepted into the regenerated bank
- **WHEN** a regenerated question is accepted
- **THEN** it SHALL reference one or more existing canonical experiment point ids
- **AND** each referenced canonical point id SHALL resolve to current canonical point title, available placement contexts, and chapter context where available.

#### Scenario: Question covers multiple experimental points
- **WHEN** a question requires evidence from more than one canonical experiment point
- **THEN** the question SHALL store all primary canonical point ids needed to justify the stem, answer, and explanation
- **AND** it SHALL preserve a reviewer note explaining why multiple points are needed.

#### Scenario: Placement context is recorded
- **WHEN** a question is generated, reviewed, or browsed from a specific catalog placement
- **THEN** the workflow SHALL preserve the source placement id and catalog path as context metadata
- **AND** placement context SHALL NOT replace the required canonical point binding.

#### Scenario: Coverage concept is recorded
- **WHEN** a question also covers a cross-point concept such as observation method, oxidation order, or reagent role
- **THEN** the question SHALL store coverage tags when those tags are part of the accepted review record
- **AND** coverage tags SHALL NOT replace the required canonical point bindings.

### Requirement: Option-level diagnostic links
The system SHALL support option-level diagnostic links for single-choice questions using canonical experiment point ids and optional placement context.

#### Scenario: Single-choice question has a correct option
- **WHEN** a single-choice question is accepted
- **THEN** its correct option MUST reference the canonical point id or coverage tag that supports the correct answer where point-specific evidence exists
- **AND** it SHALL include deterministic answer data.

#### Scenario: Wrong option has diagnostic meaning
- **WHEN** a distractor represents a misconception, reversed relation, adjacent experiment, adjacent point, or unrelated distractor
- **THEN** the option link SHALL record the option label, role, optional canonical point id, optional source placement context, and diagnostic note.

#### Scenario: Wrong option has no meaningful diagnostic target
- **WHEN** a distractor is only a weak or unrelated distractor
- **THEN** the option link SHALL mark it as `weak_distractor` or `unrelated_distractor`
- **AND** the review SHALL flag the question for rewrite if the weak options make the item non-diagnostic.

### Requirement: Review decision lineage
The system SHALL store the review decision and lineage for every generated candidate question with canonical point references and placement context where available.

#### Scenario: Candidate question is reviewed
- **WHEN** a candidate question is reviewed
- **THEN** it SHALL be marked `keep`, `rewrite`, or `reject`
- **AND** it SHALL include quality flags, reviewer notes, canonical point ids, any source placement ids, and any legacy point mapping used during migration.

#### Scenario: Candidate question is rewritten
- **WHEN** a candidate question is marked `rewrite`
- **THEN** the review artifact SHALL include a concrete proposed rewritten question
- **AND** the proposed question SHALL include type, stem, answer, explanation, canonical point ids, source placement context where available, and source audit metadata.

#### Scenario: Candidate question is rejected
- **WHEN** a candidate question is marked `reject`
- **THEN** the review artifact SHALL preserve rejection reasons
- **AND** the candidate SHALL NOT be imported into the active default bank.

### Requirement: Existing evidence chain is preserved during point-node migration
The question workbench SHALL preserve the existing evidence-source semantics while migrating point references to canonical experiment point ids.

#### Scenario: Teacher point content is included in workbench context
- **WHEN** a question generation or review context includes teacher-authored canonical point content
- **THEN** that content SHALL remain labeled as `student_page_context_only` unless a separate evidence workflow promotes it
- **AND** it SHALL NOT be treated as the accepted evidence source unless a reviewer or separate evidence workflow explicitly records it as evidence.

#### Scenario: Accepted evidence is resolved
- **WHEN** a question candidate, accepted question, or diagnostic link requires evidence
- **THEN** the system SHALL continue to use reviewed canonical/RAG source refs as the evidence chain
- **AND** the migration SHALL replace legacy point or placement-only identity with canonical experiment point ids while preserving source placement context when available.

#### Scenario: Point knowledge changes
- **WHEN** a teacher edits canonical point title, principle, phenomenon explanation, safety note, related links, videos, or teacher-only note
- **THEN** the edit MUST NOT automatically rewrite accepted question evidence bindings
- **AND** any future evidence refresh MUST be an explicit question/evidence workflow outside this catalog-placement migration.
