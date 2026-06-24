## ADDED Requirements

### Requirement: Follow-up prompt guardrails
The student learning assistant SHALL apply student-facing safety, assessment, and course-scope guardrails to generated follow-up prompt suggestions.

#### Scenario: Suggestions are generated from in-scope context
- **WHEN** the backend generates follow-up prompt suggestions for a successful student assistant answer
- **THEN** the suggestion-generation context MUST include the active student assistant context, the latest student question, the completed assistant answer, and recent conversation history
- **AND** it MUST NOT include teacher/admin diagnostics, raw retrieval traces, policy internals, or hidden answer keys.

#### Scenario: Suggestions stay within course scope
- **WHEN** follow-up prompt suggestions are attached to the student assistant final response
- **THEN** each suggestion MUST be a student-facing inorganic chemistry experiment learning follow-up or a safe learning-strategy follow-up for the active context
- **AND** suggestions MUST NOT direct the student toward unrelated entertainment, finance, personal advice, or other out-of-course topics.

#### Scenario: Suggestions avoid unsafe experiment operations
- **WHEN** follow-up prompt suggestions relate to experiment practice or safety
- **THEN** they MUST avoid soliciting hazardous unsupervised operation steps
- **AND** they MAY ask about safety principles, observation cues, or teacher-supervised lab precautions.

#### Scenario: Suggestions avoid direct assessment answers
- **WHEN** the active context or recent conversation relates to a quiz, pretest, posttest, exam, or mistake review
- **THEN** generated suggestions MUST NOT ask Atom to directly reveal an answer choice or final answer
- **AND** they SHOULD ask for hints, reasoning steps, misconception analysis, or review priorities.

#### Scenario: Invalid suggestions are removed
- **WHEN** a generated suggestion violates student guardrails, exposes diagnostics, asks for direct answers, or is not student-readable
- **THEN** the backend MUST remove that suggestion before returning `suggested_prompts`
- **AND** the backend MUST NOT replace it with a static frontend fallback prompt.
