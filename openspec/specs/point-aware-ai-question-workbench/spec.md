# point-aware-ai-question-workbench Specification

## Purpose
TBD - created by archiving change redesign-point-aware-ai-question-workbench. Update Purpose after archive.
## Requirements
### Requirement: AI question workbench sessions
The system SHALL represent AI-assisted question repair and creation as persistent workbench sessions.

#### Scenario: Teacher starts a repair session
- **WHEN** a teacher starts AI repair from an existing point-aware question
- **THEN** the system SHALL create or reopen a repair workbench session for that question
- **AND** the session SHALL reference the original question id, formal experiment id, selected point context when available, operator, creation time, and session status.

#### Scenario: Teacher starts a create session
- **WHEN** a teacher starts AI creation from a selected formal experiment or experiment point
- **THEN** the system SHALL create or reopen a create workbench session
- **AND** the session SHALL reference the formal experiment id, selected point key when available, operator, creation time, and session status.

#### Scenario: Session is reopened
- **WHEN** a teacher reopens an unfinished workbench session
- **THEN** the system SHALL restore prior chat turns, generated candidates, candidate statuses, selected context, and validation results.

### Requirement: Original-question context during repair
The repair workbench SHALL keep the original question and its point-aware metadata visible while the teacher prompts AI.

#### Scenario: Repair workbench opens
- **WHEN** the repair workbench is opened for an existing question
- **THEN** the workbench SHALL show the original stem, options when present, deterministic answer, explanation, status, linked experiment, primary point keys, point titles, source audit, source references, and review lineage
- **AND** the original context SHALL remain visible while the teacher reads chat history, writes prompts, reviews candidates, or publishes a candidate.

#### Scenario: Single-choice repair uses option diagnostics
- **WHEN** the original single-choice question has option-level diagnostic links
- **THEN** the workbench SHALL show each option's diagnostic role and linked point or note beside the original question context
- **AND** generated single-choice candidates SHALL expose comparable option diagnostics before publication.

#### Scenario: Fill-blank repair uses accepted answers
- **WHEN** the original fill-blank question has accepted answer aliases or matching rules
- **THEN** the workbench SHALL show the deterministic accepted-answer set
- **AND** generated fill-blank candidates SHALL show their deterministic accepted-answer set before publication.

### Requirement: Multi-turn AI repair conversation
The workbench SHALL support multi-turn teacher prompts within a single AI assistance session.

#### Scenario: Teacher sends a follow-up prompt
- **WHEN** a teacher sends a follow-up prompt in an existing workbench session
- **THEN** the system SHALL append the teacher message as a new chat turn
- **AND** the AI request SHALL include the server-built session context, relevant prior turns or session memory, and the teacher's latest instruction.

#### Scenario: AI returns a response
- **WHEN** the AI provider or local fallback returns a response
- **THEN** the system SHALL append an assistant turn to the session
- **AND** any generated question candidates SHALL be linked to that assistant turn.

#### Scenario: Generation fails
- **WHEN** an AI request fails
- **THEN** the workbench SHALL preserve the teacher prompt in the session
- **AND** it SHALL show an actionable failure state without discarding previous turns or candidates.

### Requirement: Candidate comparison and validation
The workbench SHALL present generated candidates as comparable, validation-gated versions.

#### Scenario: Candidate is generated for repair
- **WHEN** a repair candidate is generated
- **THEN** the workbench SHALL show the candidate next to or near the original question with changed stem, options, answer, explanation, point bindings, source audit, and option diagnostics highlighted in teacher-readable form.

#### Scenario: Candidate is generated for creation
- **WHEN** a create candidate is generated
- **THEN** the workbench SHALL show the candidate with formal experiment context, selected point context when available, source references, point bindings, answer, explanation, and validation readiness.

#### Scenario: Candidate validation runs
- **WHEN** a candidate is stored or refreshed
- **THEN** the system SHALL validate objective type, deterministic answer shape, primary point keys, source audit, option diagnostic links where applicable, and generation lineage
- **AND** the workbench SHALL show whether the candidate is publishable, needs revision, or failed validation.

#### Scenario: Candidate is not publishable
- **WHEN** validation fails for a generated candidate
- **THEN** the workbench SHALL prevent publication of that candidate
- **AND** it SHALL show the validation errors so the teacher can prompt another revision.

### Requirement: Non-mutating candidate adoption
The workbench SHALL keep AI candidates non-student-facing until a teacher explicitly publishes a valid candidate.

#### Scenario: Teacher rejects a candidate
- **WHEN** a teacher rejects a generated candidate
- **THEN** the system SHALL mark the candidate rejected
- **AND** the live question bank SHALL remain unchanged.

#### Scenario: Teacher requests another revision
- **WHEN** a teacher asks for another revision after reviewing a candidate
- **THEN** the system SHALL keep the prior candidate and its status
- **AND** it SHALL add any newly generated candidate as a separate candidate version.

#### Scenario: Teacher publishes a candidate
- **WHEN** a teacher publishes a valid generated candidate
- **THEN** the system SHALL create or update the appropriate published question-bank record only after explicit confirmation
- **AND** it SHALL record session id, generating turn id, candidate id, original question id when repairing, operator, publish time, source audit, and validation result.

#### Scenario: Repair candidate is published
- **WHEN** a teacher publishes a repair candidate for an existing question
- **THEN** the system SHALL record lineage to the original question
- **AND** it SHALL follow an explicit replace, disable-original, or add-as-new policy rather than silently mutating the original question.

### Requirement: Workbench access and continuity
The workbench SHALL be reachable from normal question-bank browsing without hiding the teacher's current context.

#### Scenario: Teacher opens workbench from question detail
- **WHEN** a teacher chooses AI repair from a question detail surface
- **THEN** the system SHALL open the workbench with the selected question loaded as original context
- **AND** the teacher SHALL NOT have to close or mentally reconstruct the question detail to prompt AI.

#### Scenario: Teacher closes the workbench
- **WHEN** a teacher closes the workbench without publishing a candidate
- **THEN** the session SHALL remain available for later continuation unless the teacher explicitly discards it.

#### Scenario: Teacher returns to the question list
- **WHEN** a teacher exits the workbench
- **THEN** the question-bank page SHALL preserve the selected experiment, point filter, keyword filter, and list position when feasible.

### Requirement: Python Playwright Chrome takeover verification
The workbench SHALL be verified with Python Playwright against the teacher-visible Chrome page whenever a Chrome DevTools Protocol endpoint is available.

#### Scenario: Chrome exposes a DevTools endpoint
- **WHEN** Chrome is running with a reachable DevTools endpoint such as `http://127.0.0.1:9222`
- **THEN** the verification script SHALL connect with Python Playwright over CDP
- **AND** it SHALL reuse or open the `localhost` question-bank tab
- **AND** it SHALL verify that AI repair opens the workbench with original-question context, chat composer, and candidate area visible.

#### Scenario: Chrome does not expose a DevTools endpoint
- **WHEN** no reachable Chrome DevTools endpoint is available
- **THEN** verification SHALL report the missing endpoint as a browser-verification blocker
- **AND** it SHALL NOT claim that the teacher-visible Chrome page was inspected.

#### Scenario: Workbench screenshot is captured
- **WHEN** Python Playwright successfully attaches to Chrome and opens the workbench
- **THEN** it SHALL capture a screenshot artifact for desktop review
- **AND** it SHALL assert that original context, multi-turn chat, and candidate controls do not visibly collapse into a detached one-shot generation drawer.

