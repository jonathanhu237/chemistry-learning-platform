# experiment-centered-course-management Specification

## Purpose
Define the course experiment resource model, including theory chapter bindings, the seeded 11 official experiment units, teacher-created experiment units, experiment resource binding, and publication or archive behavior.
## Requirements
### Requirement: Theory chapter to experiment binding

The system SHALL keep theory chapters visible and bind experiments under related chapters without teacher-facing coverage-strength labels.

#### Scenario: Teacher views chapter structure
- **GIVEN** the textbook theory chapters are available
- **WHEN** a teacher opens course structure management
- **THEN** the teacher SHALL see chapters as grouping/navigation nodes
- **AND** each chapter SHALL show its bound experiment units as learning resources under that chapter.

#### Scenario: Experiment is bound to multiple chapters
- **GIVEN** an experiment is relevant to more than one theory chapter
- **WHEN** the experiment is bound to chapters
- **THEN** the system SHALL allow many-to-many chapter/experiment bindings
- **AND** the teacher-facing UI SHALL present the bindings as plain chapter selections without primary, partial, or supporting labels.

#### Scenario: Chapter has no direct experiment binding
- **GIVEN** a chapter such as lanthanides/actinides has no bound experiment
- **WHEN** the chapter is displayed
- **THEN** the system SHALL show that no experiment is currently bound
- **AND** it SHALL NOT fabricate an experiment to fill the gap.

### Requirement: Experiment-first admin management

The admin console SHALL let teachers manage experiment metadata, chapter bindings, resource bindings, and status from experiment-centered pages.

#### Scenario: Teacher views experiment list
- **GIVEN** a teacher opens experiment management
- **WHEN** the experiment list is displayed
- **THEN** the console SHALL show teacher-facing sequence number, experiment name, bound chapters, resource status, publication status, and edit action
- **AND** it SHALL NOT show database ids, editable source codes, published question counts, or draft question counts as primary list columns.

#### Scenario: Teacher edits experiment metadata
- **GIVEN** a teacher opens an experiment detail workspace
- **WHEN** they edit display name, chapter bindings, learning summary, resources, or publication status
- **THEN** the system SHALL save the metadata to the experiment unit
- **AND** stable internal identifiers SHALL remain server-controlled.

#### Scenario: Teacher filters experiments
- **GIVEN** a teacher opens the experiment list
- **WHEN** they filter by chapter, resource status, or publication status
- **THEN** the system SHALL return the matching experiment units.

#### Scenario: Teacher archives an experiment
- **GIVEN** an experiment is no longer part of the active teaching workflow
- **WHEN** a teacher archives it
- **THEN** the system SHALL hide it from active student-facing learning resources
- **AND** it SHALL preserve historical videos, question banks, learning attempts, and analytics data.

### Requirement: Seeded extensible experiment catalog

The system SHALL initialize the course with the 11 official experiment units while allowing teachers to create additional experiment units after deployment.

#### Scenario: Official experiments are initialized
- **GIVEN** the course structure is initialized
- **WHEN** the default experiment catalog is loaded
- **THEN** the system SHALL contain the 11 official experiment units as seeded records
- **AND** the system SHALL preserve their existing student learning records, question banks, media bindings, and analytics identifiers.

#### Scenario: Teacher creates an additional experiment
- **GIVEN** a teacher is managing experiments
- **WHEN** they create an experiment with a name, optional summary, status, and at least one bound chapter
- **THEN** the backend SHALL assign the experiment id, stable internal code, and teacher-facing display order automatically
- **AND** the teacher SHALL NOT need to enter or edit database identifiers.

#### Scenario: Legacy extracted fragments exist
- **GIVEN** existing data contains legacy experiment-like fragments from earlier extraction
- **WHEN** the admin course structure is displayed
- **THEN** the system SHALL NOT count those fragments as seeded official experiment units
- **AND** it MAY preserve them only as source/reference material until explicitly mapped or replaced.

### Requirement: Experiment resource binding

The system SHALL manage video resources as resources bound to experiments rather than as a separate teacher-facing workflow.

#### Scenario: Teacher uploads a video from experiment detail
- **GIVEN** an experiment exists without prepared video material
- **WHEN** a teacher uploads a video inside that experiment's detail workspace
- **THEN** the backend SHALL store the upload, processing status, media asset, and experiment binding
- **AND** the admin console SHALL show upload, processing, ready, failed, draft, and published states within the experiment context.

#### Scenario: Teacher binds an existing video from experiment detail
- **GIVEN** a video asset has already been uploaded
- **WHEN** a teacher selects it from an experiment's resource section
- **THEN** the system SHALL bind the asset to that experiment without requiring the teacher to visit a separate video page.

#### Scenario: Student opens experiment before video is ready
- **GIVEN** a video exists but is not ready or not published
- **WHEN** the student frontend requests the chapter or experiment content
- **THEN** the system SHALL not expose the unavailable video as playable material
- **AND** it SHALL expose the experiment metadata and other published learning materials.
