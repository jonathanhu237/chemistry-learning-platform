# student-h5-learning-flow Specification

## Purpose
TBD - created by archiving change integrate-student-h5-platform. Update Purpose after archive.
## Requirements
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

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning entry that hands off to one current family or chapter learning page.

#### Scenario: Student chooses a family from the periodic table
- **WHEN** a student selects a family, group, or chapter from the periodic-table learning entry
- **THEN** the H5 app MUST open the corresponding current family or chapter learning page
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the student MUST be able to return to the periodic-table entry or switch chapter through a secondary navigation affordance.

#### Scenario: Existing recommendation is used as fallback
- **WHEN** a student reaches learning without choosing a family or chapter explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as a current chapter page, not as a sibling-family selector.

### Requirement: Chapter learning to assessment handoff
The student H5 learning flow SHALL preserve the existing completion-to-assessment path from the current family or chapter page and from experiment point detail.

#### Scenario: Student completes chapter learning
- **WHEN** a student completes learning from the current family or chapter page
- **THEN** the H5 app MUST start the existing post-learning assessment flow
- **AND** the assessment context MUST remain compatible with the current experiment-point and question-bank behavior.

#### Scenario: Student completes point detail learning
- **WHEN** a student opens a point detail from the current family or chapter page and then completes learning
- **THEN** the H5 app MUST preserve the point, experiment, and chapter context needed for learning events, AI context, feedback context, and the existing assessment handoff.

### Requirement: Chapter-local facts and experiments flow
The student H5 learning flow SHALL keep facts/common-property viewing and experiment-point video learning within the same selected family/chapter context.

#### Scenario: Student enters chapter from periodic table
- **WHEN** a student selects a family/chapter from the periodic-table learning entry
- **THEN** the H5 app MUST open that family/chapter as the current learning context
- **AND** it MUST provide local switching between facts/common properties and experiment-point videos without returning to the periodic-table entry

#### Scenario: Student switches views before opening a point
- **WHEN** a student changes between facts and experiments on the chapter page
- **THEN** the selected chapter MUST remain unchanged
- **AND** the selected element SHOULD remain unchanged when the profile contains that element

#### Scenario: Student opens a point from experiments view
- **WHEN** a student selects a point card from the experiment-point video view
- **THEN** the app MUST open the existing point detail route with profile, chapter, experiment, point, active view, and selected element context where available
- **AND** returning from point detail MUST restore the chapter page in a sensible experiments-view context

#### Scenario: Student completes learning
- **WHEN** a student completes learning from the chapter page or point detail
- **THEN** the app MUST continue into the existing post-learning assessment flow
- **AND** the A/B view split MUST NOT bypass learning event recording or assessment eligibility behavior

### Requirement: Local chapter view state
The student H5 app SHALL preserve local chapter view state across A/B switches where feasible.

#### Scenario: Active view is preserved during local interaction
- **WHEN** a student switches to the experiments view and opens or closes local overlays
- **THEN** the app MUST keep the experiments view active unless the student explicitly switches views or leaves the chapter

#### Scenario: Scroll position is restored where feasible
- **WHEN** a student scrolls within the facts view or experiments view and then switches away and back
- **THEN** the app SHOULD restore the prior scroll position for that view where feasible
- **AND** if independent scroll restoration is not reliable, the app MUST at least preserve the active view and selected chapter context
