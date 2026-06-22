## ADDED Requirements

### Requirement: First-screen health overview
The teacher intelligent monitoring console SHALL render a first-screen overview that summarizes AI, RAG, ES, dictionary, outbox, and guardrail health before detailed diagnostics.

#### Scenario: Teacher opens intelligent monitoring
- **WHEN** an authenticated teacher-console user opens the `智能监控` route
- **THEN** the page SHALL show a compact health overview for OpenAI, RAG/BGE, Elasticsearch, dictionary assets, outbox/index sync, and student AI guardrails without requiring vertical scrolling on a normal desktop viewport
- **AND** each health item SHALL expose a status label, status tone, and the most important supporting value such as model, backend, mapping version, synced count, or recent error count.

#### Scenario: A subsystem has a warning or error
- **WHEN** any monitored subsystem reports warning, error, stale, failed, unavailable, missing, or degraded state
- **THEN** the overview SHALL surface the condition in a `需要关注` or equivalent attention area
- **AND** the attention item SHALL identify the affected subsystem and provide a direct path to the corresponding detail module.

#### Scenario: All subsystems are healthy
- **WHEN** all monitored subsystems report healthy or acceptable local-development states
- **THEN** the overview SHALL communicate that no immediate action is required
- **AND** it SHALL still show last refresh time and manual refresh affordance.

### Requirement: Module-based monitoring navigation
The intelligent monitoring console SHALL organize detailed diagnostics into stable modules rather than one long page.

#### Scenario: Detail modules are rendered
- **WHEN** the teacher views the monitoring page
- **THEN** the page SHALL provide module navigation for `总览`, `OpenAI`, `RAG`, `ES 检索`, `词典与同步`, `安全护栏`, and `调用趋势`
- **AND** selecting one module SHALL reveal its detailed content without duplicating all other modules above or below it.

#### Scenario: User returns to overview
- **WHEN** the teacher selects `总览`
- **THEN** the page SHALL return to the compact triage surface
- **AND** it SHALL not require scrolling past previously opened module content.

#### Scenario: Module data is loading or failed
- **WHEN** a module's backing API request is loading, empty, or failed
- **THEN** that module SHALL show a localized loading, empty, or error state with retry support
- **AND** other modules with available data SHALL remain usable.

### Requirement: OpenAI monitoring module
The OpenAI module SHALL monitor provider connectivity and usage while keeping credential editing outside the monitoring page.

#### Scenario: OpenAI module opens
- **WHEN** the teacher opens the `OpenAI` module
- **THEN** the module SHALL show connectivity status, effective model, API key configured state, AI channel, recent requests, recent errors, last check time, next check time, and last request summary
- **AND** it SHALL not render API key, base URL, provider, or model editing forms.

#### Scenario: Provider remediation is needed
- **WHEN** OpenAI connectivity is failed, stale, untested, or not configured
- **THEN** the module SHALL explain the state in operational wording
- **AND** it MAY provide a link to the existing settings or credential-management surface instead of performing configuration inline.

### Requirement: RAG runtime monitoring module
The RAG module SHALL monitor RAG/BGE runtime health separately from OpenAI provider health.

#### Scenario: RAG module opens
- **WHEN** the teacher opens the `RAG` module
- **THEN** the module SHALL show student RAG enabled state, BGE service status, query generation state, retrieval/rerank/final counts, service URL, request latency, model load state, memory, uptime, warmup state, model paths, and recent check time
- **AND** it SHALL distinguish legacy keyword RAG, Hybrid BGE RAG, disabled RAG, and unreachable BGE states.

#### Scenario: BGE sidecar is unavailable
- **WHEN** BGE metrics or warmup checks return an error
- **THEN** the RAG module SHALL show the error locally inside the RAG module
- **AND** the overview SHALL show only the summarized attention item with a path back to the RAG module.

### Requirement: ES retrieval diagnostics workbench
The ES retrieval module SHALL provide a focused workbench for explaining point-search query behavior.

#### Scenario: Teacher diagnoses a chemistry query
- **WHEN** the teacher enters a query such as `H2O2 KMnO4 酸性` and runs diagnostics
- **THEN** the workbench SHALL show normalized query terms, extracted formulae, strict aliases, reagent aliases, condition tags, phenomenon tags, property tags, and reaction features when present
- **AND** it SHALL show ranked point-placement results with score and matched route chips.

#### Scenario: Recall routes are available
- **WHEN** search diagnostics return route metadata
- **THEN** the workbench SHALL list recall routes with route name, human-readable label, relevant fields, and boost or weight
- **AND** the route list SHALL be visually comparable with the matched routes shown on each result.

#### Scenario: Raw diagnostics are present
- **WHEN** raw ES payload, analyzer tokens, or other low-level diagnostic details are available
- **THEN** the workbench SHALL keep them behind an explicit secondary disclosure, drawer, or detail action
- **AND** raw details SHALL not appear in the default module view.

#### Scenario: Query returns no results
- **WHEN** the diagnostic query produces no ranked results
- **THEN** the workbench SHALL show a controlled empty state
- **AND** it SHALL still show parsed query terms and enabled recall routes when those are available.

### Requirement: Dictionary and outbox governance module
The dictionary and sync module SHALL explain search readiness by combining dictionary assets, ES mapping/index state, and outbox sync state.

#### Scenario: Dictionary and sync module opens
- **WHEN** the teacher opens `词典与同步`
- **THEN** the module SHALL show dictionary category counts, analyzer asset state, mapping version, expected mapping version, ES document count, published point-content count, and outbox status counts
- **AND** it SHALL distinguish healthy, warning, failed, stale, missing, and local-development acceptable states.

#### Scenario: Dictionary assets are missing or stale
- **WHEN** analyzer or application dictionary diagnostics report missing files, mismatched hashes, or unknown category counts
- **THEN** the module SHALL show which asset category is affected
- **AND** it SHALL avoid implying that chemistry synonym semantics can be edited directly from the monitoring page unless a dedicated editing workflow exists.

#### Scenario: Outbox has pending or failed rows
- **WHEN** outbox sync status includes pending, running, failed, retryable, disabled, or unavailable rows
- **THEN** the module SHALL show the counts by status
- **AND** it SHALL provide either read-only explanation or a controlled link/action to the existing retry or rebuild workflow if available.

### Requirement: Guardrail and trend modules
The monitoring console SHALL keep safety guardrail state and usage trends available without crowding the operational overview.

#### Scenario: Safety module opens
- **WHEN** the teacher opens `安全护栏`
- **THEN** the module SHALL show student AI policy version, active state, recent decision count, invalid decision count, handled risk count, and recent outcome distribution
- **AND** it SHALL keep policy explanation compact and operational rather than instructional.

#### Scenario: Trend module opens
- **WHEN** the teacher opens `调用趋势`
- **THEN** the module SHALL show selectable ranges for recent AI calls and errors
- **AND** the chart or fallback table SHALL remain readable at normal and narrow teacher-console widths.

### Requirement: Responsive operational layout
The intelligent monitoring console SHALL remain readable and non-overlapping across common teacher desktop and laptop viewports.

#### Scenario: Normal desktop viewport renders
- **WHEN** the monitoring page is viewed at a wide desktop viewport
- **THEN** the overview SHALL use compact multi-column status layout
- **AND** module details MAY use side-by-side panels where comparison is useful.

#### Scenario: Narrow laptop viewport renders
- **WHEN** the monitoring page is viewed at a narrow laptop-width teacher-console viewport
- **THEN** status tiles, tabs, query terms, route chips, result rows, and action buttons SHALL wrap or stack without text overlap
- **AND** no nested card structure SHALL create horizontal clipping of primary status or search input.

#### Scenario: Long tokens or formulas are displayed
- **WHEN** module content includes long model paths, service URLs, formula signatures, route names, dictionary hashes, or result titles
- **THEN** the layout SHALL truncate, wrap, or disclose the value in a controlled way
- **AND** hover/focus/action states SHALL not resize surrounding content unexpectedly.

### Requirement: Teacher-only diagnostic surface
The intelligent monitoring console SHALL keep operational diagnostics restricted to teacher-console users.

#### Scenario: Student API consumer requests diagnostics
- **WHEN** a student-facing API or student frontend requests search diagnostics, raw ES DSL, analyzer tokens, dictionary metadata, job payloads, or guardrail internals
- **THEN** the system SHALL not expose those details through student responses.

#### Scenario: Teacher console renders diagnostics
- **WHEN** an authenticated teacher-console user opens diagnostic modules
- **THEN** the console MAY show teacher/operator diagnostic metadata
- **AND** sensitive raw details SHALL still be hidden behind explicit secondary actions rather than default visible page content.
