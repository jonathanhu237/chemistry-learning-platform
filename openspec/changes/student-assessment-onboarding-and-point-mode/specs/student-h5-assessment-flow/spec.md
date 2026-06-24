## ADDED Requirements

### Requirement: Student point assessment session lifecycle
The student H5 SHALL let authenticated students start a point-scoped assessment from a catalog point detail page after learning that point.

#### Scenario: Student starts point assessment
- **WHEN** an authenticated student starts point assessment for a valid catalog `point_node_id` and has no open assessment session
- **THEN** the backend MUST create an assessment session with `assessment_mode = "point"`
- **AND** it MUST compose questions only from published student-visible questions bound to that `point_node_id`
- **AND** it MUST return public questions without exposing hidden answer keys.

#### Scenario: Point assessment reuses open session
- **WHEN** a student starts point assessment while any assessment session is already in progress
- **THEN** the backend MUST return the existing open session rather than creating a point session
- **AND** the student H5 MUST tell the student that an unfinished assessment is being continued.

#### Scenario: Point assessment handles insufficient questions
- **WHEN** a point assessment is started for a point with one or more eligible questions but fewer than the target question count
- **THEN** the backend MUST create an underfilled point assessment
- **AND** the response composition metadata MUST indicate that the point question bank was underfilled.

#### Scenario: Point assessment rejects zero eligible questions
- **WHEN** a point assessment is started for a point with zero eligible published point-backed questions
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT create a new assessment session.

### Requirement: Student assessment status and baseline prompt
The student H5 SHALL use server assessment status to guide students toward completing an initial smart assessment baseline and continuing unfinished assessments.

#### Scenario: Student assessment status is loaded
- **WHEN** an authenticated student enters the H5 shell
- **THEN** the frontend MUST request the student's assessment status
- **AND** the backend MUST report whether a completed `smart` assessment exists
- **AND** it MUST report any open assessment session id and mode
- **AND** it MUST report whether the smart-baseline prompt was permanently dismissed.

#### Scenario: Open assessment prompt has priority
- **WHEN** the assessment status reports an open assessment session
- **THEN** the student H5 MUST show a continuation prompt before any smart-baseline prompt
- **AND** continuing the prompt MUST navigate to the open assessment session.

#### Scenario: Smart baseline prompt is shown
- **WHEN** the assessment status reports no completed `smart` assessment, no open assessment, and no baseline prompt dismissal
- **THEN** the student H5 MUST show a dialog recommending a first smart assessment
- **AND** accepting the dialog MUST start or navigate to smart assessment.

#### Scenario: Smart baseline prompt is permanently dismissed
- **WHEN** the student chooses not to be reminded about the smart baseline prompt again
- **THEN** the frontend MUST call the dismissal endpoint
- **AND** future assessment status responses for that student MUST mark the prompt as dismissed.

#### Scenario: Point and custom assessments do not satisfy smart baseline
- **WHEN** a student has completed only `point` or `custom` assessments
- **THEN** the assessment status MUST still report that no completed smart baseline exists.
