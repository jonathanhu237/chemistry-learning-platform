## ADDED Requirements

### Requirement: Student learning home
The system SHALL provide a student learning home that lists the student's available experiment learning groups and progress context.

#### Scenario: Student opens learning home
- **WHEN** an authenticated student without a password-change requirement requests the learning home
- **THEN** the backend SHALL return student class context and available experiment groups
- **AND** it SHALL avoid exposing teacher-only identifiers or draft-only data.

### Requirement: Experiment group and detail access
The system SHALL provide student-facing experiment group and experiment detail APIs scoped to active/published learning resources.

#### Scenario: Student opens an experiment group
- **WHEN** an authenticated student requests an experiment group
- **THEN** the backend SHALL return the experiments available in that group
- **AND** unavailable or archived experiment resources SHALL NOT be exposed as playable student materials.

#### Scenario: Student opens an experiment detail
- **WHEN** an authenticated student requests an available experiment detail
- **THEN** the backend SHALL return experiment metadata, learning points, and published resource references for that experiment.

### Requirement: Protected media delivery
The system SHALL protect student media stream and thumbnail access using authenticated student context or equivalent short-lived authorization.

#### Scenario: Student requests protected media
- **WHEN** an authenticated student requests media that is bound to an available experiment
- **THEN** the backend SHALL authorize access before serving the stream or thumbnail
- **AND** unpublished or unready media SHALL remain unavailable.

#### Scenario: Unauthenticated media request
- **WHEN** a request lacks a valid student authorization token
- **THEN** the backend SHALL reject protected media access.
