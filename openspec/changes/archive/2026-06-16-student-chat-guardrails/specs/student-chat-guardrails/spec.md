## ADDED Requirements

### Requirement: Student chat policy scope
The student learning assistant SHALL apply guardrails only to student learning-page chat requests and SHALL NOT change teacher AI workflows.

#### Scenario: Student chat request is processed
- **WHEN** a learning assistant request is executed as `user_role="student"`
- **THEN** the system SHALL classify the request against the student AI policy
- **AND** the response SHALL include policy version, classification, guardrail decisions, tool calls, sources, and final mode.

#### Scenario: Teacher AI workflow is used
- **WHEN** a teacher uses question-bank assistant, teacher analytics, or another teacher AI workflow
- **THEN** the student chat guardrails SHALL NOT be required for that workflow
- **AND** the workflow SHALL continue to use its existing teacher-facing AI behavior.

### Requirement: Course-scope refusal
The student learning assistant SHALL refuse requests that are outside inorganic chemistry experiment learning scope.

#### Scenario: Student asks an unrelated question
- **WHEN** the student asks for advice unrelated to the course, such as financial, entertainment, or general life advice
- **THEN** the assistant SHALL refuse with a course-scope explanation
- **AND** it SHALL NOT call learning tools or produce the requested unrelated answer.

### Requirement: Unsafe experiment-detail refusal
The student learning assistant SHALL refuse unsafe experiment-operation detail requests while allowing safe conceptual or teacher-supervised safety guidance.

#### Scenario: Student asks for hazardous home experiment steps
- **WHEN** the student asks for detailed steps to perform hazardous chemistry outside supervised teaching conditions
- **THEN** the assistant SHALL refuse to provide actionable operation steps
- **AND** it SHALL redirect to safety principles or supervised-lab guidance.

### Requirement: Assessment answer protection
The student learning assistant SHALL avoid giving direct answers to assessments and SHALL provide learning hints instead.

#### Scenario: Student asks for a direct test answer
- **WHEN** the student asks the assistant to directly answer a quiz, pretest, posttest, exam, or assignment item
- **THEN** the assistant SHALL avoid revealing the direct answer
- **AND** it SHALL provide a hint, reasoning path, or relevant knowledge-point guidance.

### Requirement: RAG-assisted course answering
The student learning assistant SHALL treat RAG and platform evidence as helpful support for ordinary chemistry questions, not as a hard requirement.

#### Scenario: Student asks a course-factual question
- **WHEN** the student asks an ordinary inorganic chemistry factual question
- **THEN** the assistant SHALL answer using available chemistry knowledge
- **AND** it SHALL use RAG evidence as supporting context when evidence is enabled and found.

#### Scenario: RAG is disabled or has no match
- **WHEN** RAG lookup is disabled or no suitable evidence is found for an ordinary course-factual question
- **THEN** the assistant SHALL still answer from reliable model chemistry knowledge when a model is configured
- **AND** it SHALL NOT claim that the answer came from platform evidence.

### Requirement: Platform resource grounding
The student learning assistant SHALL require platform lookup for claims about published platform resources or material availability.

#### Scenario: Student asks for a published resource
- **WHEN** the student asks whether a video or resource exists on the platform
- **THEN** the assistant SHALL only report ready and published resources found by platform lookup
- **AND** it SHALL state unavailable when no matching published resource exists.

### Requirement: Feature-switch enforcement
The student learning assistant SHALL respect student AI feature switches.

#### Scenario: Student AI assistant is disabled
- **WHEN** the student AI assistant entry switch is disabled
- **THEN** the admin test endpoint SHALL reject learning assistant test requests
- **AND** it SHALL NOT invoke the agent.

#### Scenario: Student RAG access is disabled
- **WHEN** student RAG access is disabled
- **THEN** learning assistant requests SHALL execute without RAG lookup permission
- **AND** the guardrail diagnostics SHALL record that RAG lookup was disabled when relevant.

### Requirement: Policy gate fail-closed fallback
The student learning assistant SHALL fall back to deterministic local policy when the optional model policy gate is unavailable or invalid.

#### Scenario: Policy gate is unavailable
- **WHEN** the optional model policy gate raises an error or is not configured
- **THEN** the assistant SHALL continue with the local student policy classification
- **AND** risky requests SHALL still be refused or converted to hints according to local policy.

#### Scenario: Policy gate returns invalid structured output
- **WHEN** the optional model policy gate returns malformed JSON, an unknown mode, or another invalid policy decision
- **THEN** the assistant SHALL record an invalid policy decision guardrail
- **AND** it SHALL continue with the local student policy classification instead of treating the request as a normal answer.
