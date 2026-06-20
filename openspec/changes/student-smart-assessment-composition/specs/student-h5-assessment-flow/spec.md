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

### Requirement: Smart assessment composes by experiment mastery
Smart assessment composition SHALL select experiments before selecting questions, using experiment mastery evidence and teacher-configured strategy.

#### Scenario: Composition separates untested experiments
- **WHEN** the system composes a smart assessment
- **THEN** experiments with no mastery row or zero evidence count MUST be treated as untested
- **AND** untested experiments MUST NOT be assigned a fake mastery score for the mastery curve.

#### Scenario: Untested ratio reserves question quota
- **WHEN** the effective strategy has a non-zero untested experiment ratio
- **THEN** the composer MUST reserve the configured proportion of question slots for untested experiments where eligible untested questions exist
- **AND** if untested questions are insufficient, it MUST backfill from eligible measured experiments and record a warning.

#### Scenario: Measured experiments use mastery tickets
- **WHEN** the system selects from measured experiments
- **THEN** lower mastery scores MUST produce higher relative draw tickets according to the effective weak-tendency strategy
- **AND** high mastery experiments MUST retain non-zero draw opportunity unless no eligible questions exist.

#### Scenario: Experiment question cap is enforced
- **WHEN** questions are selected for a smart assessment
- **THEN** the system MUST respect the effective maximum questions per experiment where enough candidate experiments and questions exist
- **AND** if a selected experiment lacks enough questions, the composer MUST backfill from remaining eligible experiments before returning an underfilled paper.

### Requirement: Smart assessment updates experiment mastery
Smart assessment submissions SHALL update experiment-level mastery using the same experiment mastery evidence model as other graded assessment flows.

#### Scenario: Completed smart assessment records mastery changes
- **WHEN** a student submits a smart assessment with graded attempts linked to formal experiments
- **THEN** the backend MUST update experiment-level mastery for those experiments
- **AND** the report MUST include mastery before/after changes for affected experiments where available.

#### Scenario: Smart assessment report explains composition
- **WHEN** a completed smart assessment report is returned
- **THEN** it MUST include score, correct rate, selected experiment summaries, composition summary, mastery changes, and wrong-answer details where available
- **AND** it MUST explain untested and low-mastery coverage in student-facing language without requiring the student to understand the internal ticket formula.
