## ADDED Requirements

### Requirement: H5 student assistant endpoint guardrails
Student H5 assistant APIs SHALL use the existing student chat guardrail policy and feature-switch behavior.

#### Scenario: Student asks from learning page
- **WHEN** an authenticated student sends a learning-page assistant request from the H5 app
- **THEN** the backend SHALL process it as a student learning assistant request
- **AND** it SHALL apply the existing student policy classification, assessment-answer protection, resource grounding, and feature switches.

#### Scenario: Student AI feature is disabled
- **WHEN** the student AI assistant switch is disabled
- **THEN** H5 assistant endpoints SHALL reject assistant generation
- **AND** they SHALL NOT invoke the agent model.

### Requirement: Submitted posttest review scope
The student assistant SHALL only explain posttest mistakes from the authenticated student's submitted completed posttest data.

#### Scenario: Student requests posttest mistake help
- **WHEN** a student requests posttest mistake explanations
- **THEN** the backend SHALL scope explanations to that student's completed submitted answers
- **AND** it SHALL avoid revealing direct answers for unrelated assessment items.
