## ADDED Requirements

### Requirement: Same-point duplicate risk detection
The system SHALL detect possible duplicate question intent for objective questions within the same catalog point.

#### Scenario: Draft is checked against same-point questions
- **WHEN** an AI-generated or teacher-edited draft question is evaluated for duplicate risk
- **THEN** the system SHALL compare it only with published questions and active draft questions linked to the same source placement point
- **AND** it SHALL ignore questions linked only to other points.

#### Scenario: Same batch questions are compared
- **WHEN** multiple questions are generated in one request for the same point
- **THEN** the system SHALL compare later generated questions with earlier questions in the same batch
- **AND** it SHALL include same-batch matches in the duplicate-risk result.

#### Scenario: Rejected drafts are excluded
- **WHEN** duplicate risk is evaluated
- **THEN** the system SHALL exclude rejected draft questions from the comparison set.

### Requirement: Duplicate risk metadata
The system SHALL store duplicate-risk results as concise metadata on question drafts and preserve the metadata when published.

#### Scenario: Duplicate risk is found
- **WHEN** a draft question has possible duplicate risk
- **THEN** the system SHALL store metadata indicating that risk exists
- **AND** it SHALL include a teacher-readable message and a bounded list of similar same-point questions.

#### Scenario: No duplicate risk is found
- **WHEN** a draft question has no detected duplicate risk
- **THEN** the system SHALL store metadata indicating that no duplicate risk is currently detected.

#### Scenario: Risky draft is published
- **WHEN** a teacher publishes a draft that has duplicate-risk metadata
- **THEN** the published question SHALL preserve the duplicate-risk metadata for audit.

### Requirement: Semantic fingerprint caching
The system SHALL cache semantic fingerprints used for duplicate-risk comparison.

#### Scenario: Fingerprint already exists
- **WHEN** duplicate-risk detection needs a semantic fingerprint for unchanged question text and the same embedding model
- **THEN** the system SHALL reuse the cached fingerprint rather than requesting a new embedding.

#### Scenario: Fingerprint text changes
- **WHEN** a question or draft changes its stem, options, answer, or explanation
- **THEN** the system SHALL compute and cache a new fingerprint before semantic comparison when embeddings are configured.
