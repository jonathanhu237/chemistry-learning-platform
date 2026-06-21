## ADDED Requirements

### Requirement: Student point videos use active ready bindings
The student H5 learning experience SHALL render catalog point videos from the point's single active ready media binding rather than a separate binding publication state.

#### Scenario: Published point has active ready video
- **WHEN** a student opens a visible catalog point that has an active non-archived binding to a ready video asset
- **THEN** the H5 point detail page MUST render that video as the point video
- **AND** it MUST NOT require the binding row to carry a separate `published` status.

#### Scenario: Point has no active ready video
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the H5 point detail page MUST show the existing graceful no-video state
- **AND** it MUST not fail or expose teacher-only binding diagnostics.

#### Scenario: Point has archived or unready bindings
- **WHEN** a point has only archived bindings or bindings to unready video assets
- **THEN** the H5 point detail page MUST treat the point as having no playable video
- **AND** it MUST not expose archived or processing-only media URLs to students.

### Requirement: Teacher preview follows the same video visibility rule
Teacher preview SHALL render the same student-facing video behavior as normal H5 point detail while remaining read-only.

#### Scenario: Teacher previews a point with active ready video
- **WHEN** a teacher opens the learning-card preview for a point with an active ready video binding
- **THEN** the preview MUST render that video through preview-scoped media access
- **AND** it MUST match the normal student rule that binding publication state is not required.

#### Scenario: Teacher previews a point without active ready video
- **WHEN** a teacher previews a point with no active ready video
- **THEN** the preview MUST show the same no-video state as normal H5
- **AND** it MUST not expose binding status internals or teacher-only diagnostics.
