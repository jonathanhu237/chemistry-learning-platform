## ADDED Requirements

### Requirement: Student H5 published experiment exposure
Student H5 learning APIs SHALL expose only active and published experiment resources.

#### Scenario: Published experiment is requested
- **WHEN** a student requests a published experiment available to their class
- **THEN** the backend SHALL return student-facing experiment metadata and learning resources.

#### Scenario: Draft or archived experiment is requested
- **WHEN** a student requests a draft, archived, or otherwise unavailable experiment
- **THEN** the backend SHALL hide unavailable playable resources
- **AND** it SHALL avoid exposing teacher-only draft data.
