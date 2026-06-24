## MODIFIED Requirements

### Requirement: Turn-level diagnostics inspector
The system SHALL expose guardrail, classification, retrieval-decision, tool-call, RAG, source, and raw response diagnostics for each assistant turn.

#### Scenario: Admin selects a completed turn
- **WHEN** the admin selects a completed assistant turn
- **THEN** the inspector SHALL show the answer status, classification, retrieval decision, guardrail decisions, tool calls, selected sources, and raw structured response for that turn.

#### Scenario: Retrieval decision diagnostics are available
- **WHEN** a completed turn includes a retrieval decision
- **THEN** the inspector SHALL show the retrieval mode, decision source, strict-evidence state, confidence when available, decision reason, override state when applicable, and whether dynamic RAG or platform resource lookup executed
- **AND** it SHALL distinguish skipped dynamic RAG from RAG disabled, no usable match, fixed evidence only, and strict evidence failure.

#### Scenario: Retrieval diagnostics are available
- **WHEN** a turn uses RAG
- **THEN** the inspector SHALL show the generated retrieval queries, recall sources, rerank scores when available, and final evidence selected for the answer.

#### Scenario: Retrieval is skipped by decision
- **WHEN** a turn skips dynamic RAG because the retrieval decision selected ordinary model-knowledge answering or fixed evidence only
- **THEN** the inspector SHALL show the retrieval decision empty state for RAG diagnostics
- **AND** it SHALL NOT show stale retrieval diagnostics from a previous turn.

#### Scenario: Runtime performance is available
- **WHEN** hybrid BGE RAG is enabled
- **THEN** the debug console SHALL show whether the optional BGE service is reachable
- **AND** it SHALL show useful runtime metrics such as model loaded state, container memory, process/container CPU time, request counts, and service probe latency when available.

#### Scenario: BGE warmup status is available
- **WHEN** the optional BGE service is configured to warm up on startup
- **THEN** the debug console SHALL show whether warmup is disabled, not started, running, succeeded, or failed
- **AND** it SHALL show warmup duration or error details when available.

#### Scenario: Retrieval diagnostics are unavailable
- **WHEN** a turn does not use RAG or diagnostics are not returned
- **THEN** the inspector SHALL show an explicit empty state rather than stale diagnostics from a previous turn.
