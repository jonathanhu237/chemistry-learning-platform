## MODIFIED Requirements

### Requirement: RAG-assisted course answering
The student learning assistant SHALL treat RAG and platform evidence as helpful support for ordinary chemistry questions, not as a hard requirement, and SHALL use the retrieval decision layer to determine whether dynamic RAG is needed for each turn.

#### Scenario: Student asks a course-factual question
- **WHEN** the student asks an ordinary inorganic chemistry factual question
- **THEN** the assistant SHALL answer using available chemistry knowledge
- **AND** it SHALL use RAG evidence as supporting context only when the retrieval decision selects dynamic RAG and usable evidence is found.

#### Scenario: Student asks an ordinary explanation question
- **WHEN** the student asks for a concept explanation, mechanism explanation, equation derivation, safe reasoning path, or short follow-up without requesting platform evidence
- **THEN** the assistant SHALL allow the retrieval decision to skip dynamic RAG
- **AND** it SHALL still answer from reliable model chemistry knowledge when a model is configured.

#### Scenario: RAG is disabled or has no match
- **WHEN** RAG lookup is disabled or no suitable evidence is found for an ordinary course-factual question
- **THEN** the assistant SHALL still answer from reliable model chemistry knowledge when a model is configured
- **AND** it SHALL NOT claim that the answer came from platform evidence.

#### Scenario: Explicit evidence request is received
- **WHEN** the student asks for a citation, source, textbook wording, source figure, evidence image, course material reference, or answer according to platform material
- **THEN** the assistant SHALL require evidence through fixed point evidence, dynamic RAG, or strict evidence handling
- **AND** it SHALL NOT provide an unsupported platform-evidence claim when no usable evidence is found.

### Requirement: Policy gate fail-closed fallback
The student learning assistant SHALL fall back to deterministic local policy and deterministic retrieval routing when the optional model policy gate is unavailable or invalid.

#### Scenario: Policy gate is unavailable
- **WHEN** the optional model policy gate raises an error or is not configured
- **THEN** the assistant SHALL continue with the local student policy classification
- **AND** risky requests SHALL still be refused or converted to hints according to local policy
- **AND** retrieval routing SHALL use deterministic local fallback rather than defaulting to dynamic RAG for every turn.

#### Scenario: Policy gate returns invalid structured output
- **WHEN** the optional model policy gate returns malformed JSON, an unknown mode, an unknown retrieval mode, or another invalid policy decision
- **THEN** the assistant SHALL record an invalid policy decision guardrail or diagnostic
- **AND** it SHALL continue with the local student policy classification and deterministic retrieval routing instead of treating the request as a normal always-RAG answer.

## ADDED Requirements

### Requirement: Retrieval routing remains separate from safety guardrails
The student learning assistant SHALL keep safety, assessment, and course-scope guardrails separate from retrieval routing while allowing retrieval decisions to be recorded for diagnostics.

#### Scenario: Safety refusal is selected
- **WHEN** the student asks for unsafe experiment operation details
- **THEN** the safety guardrail SHALL decide the refusal behavior
- **AND** retrieval routing SHALL NOT run dynamic RAG to produce unsafe operation steps.

#### Scenario: Assessment hint is selected
- **WHEN** the student asks for a direct quiz, test, exam, or assignment answer
- **THEN** the assessment guardrail SHALL convert the turn to learning guidance or hints
- **AND** retrieval routing SHALL NOT override that policy into a direct grounded answer.

#### Scenario: Retrieval decision is diagnostic
- **WHEN** the backend records a retrieval decision for a student assistant turn
- **THEN** diagnostics SHALL include that decision for teacher/operator inspection where assistant turn diagnostics are exposed
- **AND** student-facing chat surfaces MUST NOT display raw retrieval mode names, policy codes, confidence values, or tool internals.
