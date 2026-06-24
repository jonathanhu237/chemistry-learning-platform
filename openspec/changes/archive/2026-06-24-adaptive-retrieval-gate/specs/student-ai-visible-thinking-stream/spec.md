## MODIFIED Requirements

### Requirement: Agent trace fallback reflects real execution
When model reasoning summaries are unavailable, the student assistant SHALL expose truthful high-level agent progress rather than preset fake thinking, including the retrieval decision actually made for the current turn.

#### Scenario: Policy gate starts
- **WHEN** the agent actually begins student policy, safety, scope, or question-type evaluation for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="policy"` when agent trace fallback is active
- **AND** it MUST NOT include policy codes, policy prompts, guardrail arrays, or internal classification labels.

#### Scenario: Retrieval decision starts
- **WHEN** the agent actually begins deciding whether the turn needs course material, fixed evidence, dynamic RAG, or platform resource lookup
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval_decision"` when agent trace fallback is active
- **AND** the message MUST be a fixed student-safe status that does not expose retrieval mode names, confidence values, policy labels, or tool names.

#### Scenario: Course context is prepared
- **WHEN** the agent actually prepares fixed point evidence, curriculum context, conversation context, or other course context for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="context"` when agent trace fallback is active
- **AND** it MUST NOT expose source ids, chunk ids, catalog internals, or teacher-only metadata.

#### Scenario: Fixed point evidence is used
- **WHEN** the retrieval decision uses hydrated fixed point evidence for the selected point or experiment context
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="fixed_evidence"` when agent trace fallback is active
- **AND** it MUST describe only that the assistant is reading current course context in student-facing language.

#### Scenario: Retrieval is skipped
- **WHEN** the retrieval decision skips dynamic RAG because the turn can be answered as an ordinary learning explanation
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval_skip"` when agent trace fallback is active
- **AND** it MUST NOT claim that course material search, source lookup, or platform resource lookup ran.

#### Scenario: Retrieval runs
- **WHEN** the agent actually performs RAG, curriculum, source, or platform evidence lookup for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval"` when agent trace fallback is active
- **AND** it MUST NOT claim retrieval ran when the retrieval decision or feature switch skipped retrieval.

#### Scenario: Evidence quality is evaluated
- **WHEN** dynamic RAG or platform lookup returns and the agent evaluates whether results are usable for the requested evidence claim
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="evidence_quality"` when agent trace fallback is active
- **AND** it MUST NOT expose raw no-match diagnostics, disabled feature flags, RAG implementation names, source ids, or rerank scores to the student.

#### Scenario: Retrieval has no usable match
- **WHEN** retrieval is disabled, skipped by policy, or produces no usable evidence and the turn continues from model chemistry knowledge or local fallback
- **THEN** the backend SHALL emit a high-level student-safe trace message that the assistant is organizing the answer from available course knowledge when agent trace fallback is active
- **AND** it MUST NOT expose raw no-match diagnostics, disabled feature flags, or RAG implementation names to the student.

#### Scenario: Answer generation starts
- **WHEN** the agent actually starts model or local answer generation for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="generation"` when agent trace fallback is active
- **AND** it MUST NOT describe that message as model reasoning unless it came from a reasoning summary event.

#### Scenario: Local fallback is used
- **WHEN** model streaming fails or no model is configured and the agent continues through a local fallback answer path
- **THEN** the backend SHALL emit a `thinking` event with `source="agent_trace"` and `phase="fallback"` when agent trace fallback is active
- **AND** it MUST NOT expose provider error details or stack traces to the student.
