## ADDED Requirements

### Requirement: Existing experiment video point binding
The system SHALL use existing experiment video points as the final binding target for the demo question bank.

#### Scenario: Video point is used for the demo
- **WHEN** a point-aware demo binding is created
- **THEN** it SHALL reference an existing video point key from the formal experiment video point list
- **AND** it SHALL include the human-readable point title, canonical source chunk ids, and reviewer note.

#### Scenario: Coverage concept is not a video point
- **WHEN** a method or conclusion concept such as CCl4 observation or oxidation order is recorded
- **THEN** it MAY be stored as a coverage tag
- **AND** it SHALL NOT replace the existing video point key as the final binding target.

#### Scenario: Source evidence is insufficient
- **WHEN** a candidate binding cannot be justified by canonical evidence
- **THEN** it SHALL be marked as `needs_evidence`
- **AND** it SHALL NOT be used as an accepted question binding.

### Requirement: Manual point binding authority
The system SHALL treat manual review as the authority for final question-to-point bindings.

#### Scenario: Candidate binding is suggested automatically
- **WHEN** a candidate binding is suggested by keyword, embedding, or model output
- **THEN** it SHALL remain provisional until a reviewer records an accepted, rejected, or uncertain decision.

#### Scenario: Reviewer accepts a binding
- **WHEN** a reviewer accepts a question-to-point binding
- **THEN** the binding SHALL record the linked video point key, binding role, evidence chunk ids, reviewer note, and confidence.

### Requirement: Option-level point binding
The system SHALL support option-level point bindings for single-choice questions.

#### Scenario: Single-choice question is reviewed
- **WHEN** a single-choice question is reviewed
- **THEN** each option MAY reference an existing video point or misconception
- **AND** the correct option SHALL identify the evidence point when the option is point-specific.

#### Scenario: Wrong option has diagnostic value
- **WHEN** a distractor maps to a specific misconception or adjacent point
- **THEN** the option binding SHALL preserve that diagnostic relationship for later learning analytics.

### Requirement: Question quality review
The system SHALL record whether a reviewed question should be kept, rewritten, or rejected.

#### Scenario: Question is too trivial
- **WHEN** a question only asks for direct formula recitation, direct equation writing, pure terminology recall, or one-step obvious facts
- **THEN** it SHALL be marked for rewrite or rejection
- **AND** it SHALL NOT be promoted as a final diagnostic question without revision.

#### Scenario: Fill blank is not mobile-suitable
- **WHEN** a fill-blank question expects a long reagent combination, full equation, multi-clause explanation, or other phone-unfriendly answer
- **THEN** it SHALL be marked for rewrite
- **AND** the proposed replacement SHALL use single choice, true/false, or a short machine-gradable fill blank.

#### Scenario: Rewrite decision is recorded
- **WHEN** a reviewed question is marked `rewrite`
- **THEN** the review artifact SHALL include a concrete proposed rewritten question
- **AND** the proposed question SHALL include deterministic answer data without AI-based correctness grading.

#### Scenario: Question lacks source support
- **WHEN** the cited source chunks do not support the stem, answer, or explanation
- **THEN** the question SHALL be marked as under-evidenced
- **AND** it SHALL NOT be accepted into the point-aware demo bank.
