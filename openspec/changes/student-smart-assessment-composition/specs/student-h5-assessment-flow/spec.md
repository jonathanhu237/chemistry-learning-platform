## ADDED Requirements

### Requirement: Student smart assessment session lifecycle
The student H5 SHALL let authenticated students start, continue, submit, and review smart assessment sessions directly from the assessment destination.

#### Scenario: Student starts smart assessment
- **WHEN** an authenticated student starts a smart assessment from the `测评` page
- **THEN** the backend MUST create or return that student's current open smart assessment session
- **AND** it MUST return public questions without exposing hidden answer keys
- **AND** it MUST include a concise composition summary suitable for student display.

#### Scenario: Student resumes open smart assessment
- **WHEN** a student with an in-progress smart assessment starts smart assessment again
- **THEN** the backend MUST return the same open session rather than composing a new paper
- **AND** the question list MUST remain stable.

#### Scenario: Student submits smart assessment
- **WHEN** a student submits answers for an open smart assessment session
- **THEN** the backend MUST validate that submitted question ids exactly match the session questions
- **AND** it MUST grade the answers
- **AND** it MUST persist item attempts with a smart-assessment evidence kind
- **AND** it MUST complete the session with a report.

### Requirement: Student custom assessment selection
The student H5 SHALL provide a separate custom assessment mode where students select experiments and question count before starting a paper.

#### Scenario: Student opens custom assessment options
- **WHEN** an authenticated student opens the custom assessment selection page
- **THEN** the backend MUST return the effective custom assessment settings
- **AND** it MUST return only selectable published root or first-level experiments that have at least one eligible published point-backed question under their descendants
- **AND** it MUST NOT return hidden answer keys or question bodies in the options payload.

#### Scenario: Student searches and selects experiments
- **WHEN** custom assessment options are displayed
- **THEN** the UI MUST let the student search experiments by visible experiment text
- **AND** the UI MUST let the student select one or more experiments
- **AND** it MUST NOT require the student to choose by knowledge point, wrong-answer set, weak threshold, or measured/untested status.

#### Scenario: Student chooses custom assessment question count
- **WHEN** the student configures a custom assessment
- **THEN** the UI MUST offer fixed question-count options from `5`, `10`, `15`, and `20`
- **AND** it MUST hide options greater than the effective maximum question count
- **AND** it MUST preselect the effective default question count.

#### Scenario: Student starts custom assessment
- **WHEN** a student starts custom assessment with selected experiments and a valid question count
- **THEN** the backend MUST create or return that student's current open assessment session
- **AND** if no open session exists, it MUST compose questions only from descendant point-backed questions under the selected experiments
- **AND** it MUST mark the session as custom assessment.

#### Scenario: Custom assessment rejects invalid selection
- **WHEN** a student starts custom assessment without selected experiments, with an unsupported question count, or with experiments outside the selectable options
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT create a new assessment session.

#### Scenario: Existing open assessment is reused across modes
- **GIVEN** a student has any in-progress assessment session
- **WHEN** the student starts smart assessment or custom assessment
- **THEN** the backend MUST return the existing open session rather than creating a second session.

### Requirement: Smart assessment composes by point mastery
Smart assessment composition SHALL select point-backed questions from the full eligible question bank, using point mastery evidence and teacher-configured strategy.

#### Scenario: Composition separates untested points
- **WHEN** the system composes a smart assessment
- **THEN** points with no mastery row or zero evidence count MUST be treated as untested
- **AND** untested points MUST NOT be assigned a fake mastery score for the mastery curve.

#### Scenario: Untested ratio reserves question quota
- **WHEN** the effective strategy has a non-zero untested point ratio
- **THEN** the composer MUST reserve the configured proportion of question slots for untested points where eligible untested questions exist
- **AND** if untested questions are insufficient, it MUST backfill from eligible measured points and record a warning.

#### Scenario: Measured points use mastery tickets
- **WHEN** the system selects from measured points
- **THEN** lower mastery scores MUST produce higher relative draw tickets according to the effective weak-tendency strategy
- **AND** high mastery points MUST retain non-zero draw opportunity unless no eligible questions exist.

#### Scenario: Only point-backed questions are eligible
- **WHEN** the backend builds smart assessment candidates
- **THEN** it MUST include only published questions bound to at least one valid point node
- **AND** questions without valid point binding MUST NOT be selected for smart assessment.

#### Scenario: Experiment question cap is enforced
- **WHEN** questions are selected for a smart assessment
- **THEN** the system MUST respect the effective maximum questions per root or first-level experiment where enough candidate points and questions exist
- **AND** it SHOULD select at most one question per point before using any point-level backfill
- **AND** if a selected experiment lacks enough point-backed questions, the composer MUST backfill from remaining eligible points before returning an underfilled paper.

### Requirement: Smart assessment updates point mastery
Smart assessment submissions SHALL update point-level mastery using BKT updates and derive experiment summaries from affected points.

#### Scenario: Completed smart assessment records mastery changes
- **WHEN** a student submits a smart assessment with graded attempts linked to point nodes
- **THEN** the backend MUST update `student_point_mastery` for those points using the configured BKT update model
- **AND** if a question is linked to multiple valid point nodes, every linked point MUST receive evidence from the graded result
- **AND** the report MUST include point mastery before/after changes grouped under affected experiments where available.

#### Scenario: Smart assessment report explains composition
- **WHEN** a completed smart assessment report is returned
- **THEN** it MUST include score, correct rate, experiment summary cards, point mastery changes, composition summary, and wrong-answer details where available
- **AND** experiment mastery shown in the report MUST be derived from descendant point mastery rather than stored as an independent fact
- **AND** it MUST explain untested and low-mastery point coverage in student-facing language without requiring the student to understand the internal ticket formula.

### Requirement: Custom assessment composes balanced papers from selected experiments
Custom assessment composition SHALL sample questions only from student-selected experiments and SHOULD cover selected experiments and their descendant points as evenly as question availability allows.

#### Scenario: Custom assessment samples selected experiments evenly
- **WHEN** the backend composes a custom assessment from multiple selected experiments
- **THEN** it MUST allocate requested question slots approximately evenly across selected experiments
- **AND** it MUST expand selected experiments to descendant point nodes
- **AND** it MUST prefer at most one question per point before selecting additional questions from an already covered point
- **AND** it MUST stable-shuffle eligible questions within each point or experiment bucket until the requested question count is reached or eligible questions are exhausted.

#### Scenario: Custom assessment handles insufficient questions
- **WHEN** selected experiments cannot fill the requested question count
- **THEN** the backend MUST return the underfilled assessment if at least one question was selected
- **AND** it MUST include warning metadata with requested and actual question counts
- **AND** the UI MUST tell the student that the selected experiment question bank was insufficient.

#### Scenario: Custom assessment has zero eligible questions
- **WHEN** selected experiments produce zero eligible questions
- **THEN** the backend MUST reject the start request
- **AND** it MUST explain that no eligible questions are available.

#### Scenario: Custom assessment report is simple
- **WHEN** a custom assessment is completed
- **THEN** the report MUST include at least correct rate, selected experiment summaries, and wrong-answer details where available
- **AND** it MUST NOT require a finalized custom report design beyond the shared assessment report shell.
