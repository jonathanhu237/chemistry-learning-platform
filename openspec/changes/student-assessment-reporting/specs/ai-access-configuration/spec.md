## ADDED Requirements

### Requirement: Report prompt settings live in controlled settings surfaces
The admin console SHALL expose assessment report prompt settings in settings-oriented surfaces rather than runtime monitoring.

#### Scenario: Admin edits global report prompts
- **WHEN** an administrator opens system settings
- **THEN** the console SHALL provide editable global defaults for report summary prompt and wrong-answer explanation prompt
- **AND** it SHALL provide a way to restore system-provided default prompt text.

#### Scenario: Teacher edits class report prompts
- **WHEN** a teacher with class edit access opens class settings
- **THEN** the console SHALL provide optional class-level overrides for report summary prompt and wrong-answer explanation prompt
- **AND** it SHALL indicate whether the class is inheriting global defaults or using class overrides.

#### Scenario: Monitoring page remains diagnostic
- **WHEN** a teacher opens the AI/RAG/ES monitoring page
- **THEN** the page SHALL remain focused on runtime status and diagnostics
- **AND** it SHALL not be the authoritative surface for editing report generation prompts.

### Requirement: Prompt editing exposes fixed variables
Report prompt editing SHALL expose fixed supported variables for assessment report generation.

#### Scenario: Teacher reviews available variables
- **WHEN** a teacher edits a report prompt
- **THEN** the UI SHALL show the supported variables for student, assessment, score, wrong answers, involved experiments or points, and mastery-change context
- **AND** the backend SHALL render prompts only from supported report context values.

#### Scenario: Unsupported variable is submitted
- **WHEN** a prompt includes an unsupported variable
- **THEN** the system SHALL reject the prompt with a teacher-readable validation error or ignore the unsupported variable safely
- **AND** it SHALL NOT allow arbitrary field lookup or teacher-only internal data access through prompt templates.

### Requirement: Prompt changes do not mutate historical reports
Changing report prompts SHALL affect only future report generation.

#### Scenario: Prompt changes after a report exists
- **WHEN** an administrator or teacher changes report prompts after a report has been generated
- **THEN** existing reports SHALL keep their persisted summary and wrong-answer explanation text
- **AND** opening those reports SHALL not regenerate text with the new prompt.
