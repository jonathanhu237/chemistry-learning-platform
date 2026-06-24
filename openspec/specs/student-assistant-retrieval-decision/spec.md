# student-assistant-retrieval-decision Specification

## Purpose
TBD - created by archiving change adaptive-retrieval-gate. Update Purpose after archive.
## Requirements
### Requirement: Student assistant retrieval decision contract
The student learning assistant SHALL compute a structured retrieval decision for each student assistant turn after safety/policy classification and before answer-generation payload construction.

#### Scenario: Retrieval decision is computed for a normal turn
- **WHEN** a student assistant turn passes initial safety, assessment, and course-scope policy checks
- **THEN** the backend MUST compute a retrieval decision before invoking answer generation
- **AND** the decision MUST include a retrieval mode, decision source, reason, strict-evidence flag, allowed tool names, and booleans indicating whether dynamic RAG or platform resource lookup will run.

#### Scenario: Retrieval decision is not a safety refusal
- **WHEN** a turn is refused for course scope, unsafe experiment detail, or direct assessment-answer leakage
- **THEN** the refusal or hint behavior MUST remain governed by student chat guardrails
- **AND** retrieval routing MUST NOT convert the turn back into a normal answer.

#### Scenario: Retrieval permission differs from retrieval obligation
- **WHEN** student RAG access is enabled for a turn
- **THEN** the retrieval decision MUST treat that setting as permission to use dynamic RAG
- **AND** it MUST NOT treat permission as an obligation to call RAG for every ordinary learning question.

### Requirement: LLM semantic retrieval routing
The student learning assistant SHALL use the configured LLM policy gate as the primary semantic router for retrieval decisions when the policy gate is available and returns valid structured output.

#### Scenario: Ordinary concept explanation skips dynamic RAG
- **WHEN** the student asks an ordinary inorganic chemistry explanation, mechanism, equation derivation, or short follow-up that does not request platform evidence
- **THEN** the retrieval decision MUST use mode `skip` or `fixed_evidence` when fixed point evidence is available and no explicit evidence/source request requires supplemental retrieval
- **AND** answer generation MUST NOT call dynamic RAG solely because the question is factual.

#### Scenario: Evidence request requires retrieval
- **WHEN** the student explicitly asks for citation, source, textbook/material wording, page, figure, evidence image, source image, or "according to course material" support
- **THEN** the retrieval decision MUST require evidence using mode `dynamic_rag`, `fixed_evidence`, or `strict_evidence`
- **AND** answer generation MUST NOT claim platform evidence unless usable evidence is present.

#### Scenario: Platform resource request uses resource lookup
- **WHEN** the student asks whether a video, file, link, download, uploaded resource, or platform material is available
- **THEN** the retrieval decision MUST use mode `resource_lookup` or `strict_evidence`
- **AND** the answer MUST be based only on ready and published platform resources found by lookup.

#### Scenario: Router output is malformed
- **WHEN** the configured LLM policy gate omits retrieval fields, returns an unknown retrieval mode, or returns malformed structured output
- **THEN** the backend MUST fall back to deterministic local retrieval routing
- **AND** the turn MUST continue unless another guardrail requires refusal or hinting.

### Requirement: Deterministic retrieval overrides
The student learning assistant SHALL apply deterministic retrieval overrides only for high-confidence boundaries that must not depend on free-form model judgment.

#### Scenario: Hard evidence wording overrides skip
- **WHEN** deterministic checks identify explicit evidence, citation, source image, textbook figure, or platform material wording
- **THEN** the backend MUST override an LLM `skip` decision with an evidence-seeking mode
- **AND** it MUST record the override in teacher/operator diagnostics.

#### Scenario: Resource boundary overrides model ambiguity
- **WHEN** deterministic checks identify a true platform resource availability request
- **THEN** the backend MUST use platform resource lookup even if the LLM labels the turn as a normal explanation
- **AND** it MUST prevent fabricated resource availability claims.

#### Scenario: RAG feature switch disables dynamic RAG
- **WHEN** student RAG access is disabled by feature switch or request policy
- **THEN** the retrieval decision MUST NOT call dynamic RAG
- **AND** ordinary learning answers SHALL continue from model chemistry knowledge or local fallback without claiming platform evidence when an answer path is otherwise available.

#### Scenario: Learning explanation is not reclassified as resource availability
- **WHEN** the student asks to explain a video point, experiment observation, or course concept without asking whether a platform resource exists
- **THEN** deterministic resource checks MUST NOT force platform resource lookup solely because the text contains words such as video, material, resource, or point.

### Requirement: Retrieval mode execution
The student learning assistant SHALL execute only the tool path selected by the retrieval decision.

#### Scenario: Skip mode executes no dynamic retrieval
- **WHEN** the retrieval decision mode is `skip`
- **THEN** answer generation MUST NOT call `rag_search_tool`
- **AND** the answer prompt MUST receive empty supplemental RAG evidence and instructions not to claim platform evidence.

#### Scenario: Fixed evidence mode uses reviewed point context
- **WHEN** the retrieval decision mode is `fixed_evidence`
- **THEN** answer generation MUST include trusted point evidence that was already hydrated for the selected context
- **AND** it MUST NOT call supplemental dynamic RAG unless the decision also requires strict evidence not satisfied by fixed evidence.

#### Scenario: Dynamic RAG mode executes RAG
- **WHEN** the retrieval decision mode is `dynamic_rag`
- **THEN** answer generation MUST call the existing RAG search path
- **AND** it MUST pass only usable selected evidence into the answer payload.

#### Scenario: Resource lookup mode executes platform resource lookup
- **WHEN** the retrieval decision mode is `resource_lookup`
- **THEN** answer generation MUST use platform resource lookup for availability claims
- **AND** it MUST NOT replace a resource lookup miss with an unsupported model claim that the resource exists.

#### Scenario: Strict evidence mode fails closed for evidence claims
- **WHEN** the retrieval decision mode is `strict_evidence`
- **AND** no usable fixed evidence, RAG evidence, or resource lookup result is available
- **THEN** the final answer MUST state that no reliable course/platform evidence was found for the requested evidence claim
- **AND** it MUST NOT answer as though the platform evidence exists.

### Requirement: Retrieval quality handling
The student learning assistant SHALL distinguish usable retrieval evidence from empty or non-supporting retrieval results before grounding an answer.

#### Scenario: Dynamic RAG returns usable evidence
- **WHEN** dynamic RAG returns selected evidence with supporting text, figure assets, or source metadata suitable for the student question
- **THEN** the answer SHALL be allowed to use that evidence as grounding
- **AND** the final response SHALL include sanitized student-facing source metadata when existing source-summary contracts require source disclosure.

#### Scenario: Dynamic RAG returns no usable evidence for ordinary question
- **WHEN** dynamic RAG returns no usable evidence for an ordinary learning explanation
- **THEN** the assistant SHALL answer from reliable model chemistry knowledge when a model answer path is configured and no stricter guardrail applies
- **AND** it MUST NOT claim the answer was found in platform material.

#### Scenario: Dynamic RAG returns no usable evidence for strict evidence request
- **WHEN** dynamic RAG returns no usable evidence for a strict evidence request
- **THEN** output guardrails MUST prevent unsupported platform-evidence claims
- **AND** the turn MUST be reported as no reliable evidence found rather than a safety refusal.

### Requirement: Retrieval decision diagnostics privacy
The student assistant SHALL expose retrieval decision details only through teacher/operator diagnostics and student-safe trace messages.

#### Scenario: Teacher inspects a completed turn
- **WHEN** a teacher or operator diagnostic view inspects a completed assistant turn
- **THEN** diagnostics MUST include retrieval mode, decision source, strict-evidence state, confidence when available, reason, override state when applicable, and whether dynamic RAG or resource lookup ran.

#### Scenario: Student receives visible thinking
- **WHEN** a student assistant stream emits retrieval-decision progress
- **THEN** the student-visible message MUST be a sanitized high-level learning status
- **AND** it MUST NOT expose retrieval mode names, policy labels, tool names, confidence scores, source ids, rerank scores, or internal reasons.

