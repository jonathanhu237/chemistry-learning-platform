## ADDED Requirements

### Requirement: Existing video point binding
The system SHALL bind regenerated experiment questions to existing formal experiment video points.

#### Scenario: Question is accepted into the regenerated bank
- **WHEN** a regenerated question is accepted
- **THEN** it SHALL reference one formal experiment id
- **AND** it SHALL reference one or more existing video point keys for that formal experiment
- **AND** each referenced point key SHALL resolve to a current formal experiment video point title.

#### Scenario: Question covers multiple experimental points
- **WHEN** a question requires evidence from more than one video point
- **THEN** the question SHALL store all primary point keys needed to justify the stem, answer, and explanation
- **AND** it SHALL preserve a reviewer note explaining why multiple points are needed.

#### Scenario: Coverage concept is recorded
- **WHEN** a question also covers a cross-point concept such as observation method, oxidation order, or reagent role
- **THEN** the question MAY store coverage tags
- **AND** coverage tags SHALL NOT replace the required video point key bindings.

### Requirement: Source audit for point-aware questions
The system SHALL preserve source audit metadata for every accepted regenerated question.

#### Scenario: Canonical evidence supports a question
- **WHEN** a question is accepted
- **THEN** it SHALL include canonical experiment chunk ids
- **AND** it SHALL include a source audit decision, evidence sufficiency flag, and reviewer note.

#### Scenario: Theory evidence is used as support
- **WHEN** a question uses theory material beyond the canonical experiment chunk
- **THEN** it SHALL include supporting theory chunk ids
- **AND** it SHALL distinguish supporting evidence from canonical experiment evidence.

#### Scenario: Evidence is insufficient
- **WHEN** cited evidence does not support the stem, answer, or explanation
- **THEN** the question SHALL be rejected or rewritten
- **AND** it SHALL NOT be imported as an accepted default-bank item.

### Requirement: Option-level diagnostic links
The system SHALL support option-level diagnostic links for single-choice questions.

#### Scenario: Single-choice question has a correct option
- **WHEN** a single-choice question is accepted
- **THEN** its correct option SHOULD reference the video point key or coverage tag that supports the correct answer
- **AND** it SHALL include deterministic answer data.

#### Scenario: Wrong option has diagnostic meaning
- **WHEN** a distractor represents a misconception, reversed relation, adjacent experiment, adjacent point, or unrelated distractor
- **THEN** the option link SHALL record the option label, role, optional point key, and diagnostic note.

#### Scenario: Wrong option has no meaningful diagnostic target
- **WHEN** a distractor is only a weak or unrelated distractor
- **THEN** the option link SHALL mark it as `weak_distractor` or `unrelated_distractor`
- **AND** the review SHALL flag the question for rewrite if the weak options make the item non-diagnostic.

### Requirement: Review decision lineage
The system SHALL store the review decision and lineage for every generated candidate question.

#### Scenario: Candidate question is reviewed
- **WHEN** a candidate question is reviewed
- **THEN** it SHALL be marked `keep`, `rewrite`, or `reject`
- **AND** it SHALL include quality flags and reviewer notes.

#### Scenario: Candidate question is rewritten
- **WHEN** a candidate question is marked `rewrite`
- **THEN** the review artifact SHALL include a concrete proposed rewritten question
- **AND** the proposed question SHALL include type, stem, answer, explanation, point keys, and source audit metadata.

#### Scenario: Candidate question is rejected
- **WHEN** a candidate question is marked `reject`
- **THEN** the review artifact SHALL preserve rejection reasons
- **AND** the candidate SHALL NOT be imported into the active default bank.
