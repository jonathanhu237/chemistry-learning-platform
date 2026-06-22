## ADDED Requirements

### Requirement: Intelligent monitoring feature boundary
The admin frontend SHALL implement the intelligent monitoring page as route-local modules, hooks, mappers, and styles rather than a single large behavior-owning page component.

#### Scenario: Developer changes OpenAI monitoring UI
- **WHEN** a developer changes provider health, recent request summary, connectivity labels, or OpenAI usage metrics on the monitoring page
- **THEN** the change MUST be localized to an OpenAI monitoring module, route-local mapper, or route-local data hook
- **AND** it MUST NOT require editing ES retrieval, dictionary/outbox, guardrail, or trend modules.

#### Scenario: Developer changes RAG monitoring UI
- **WHEN** a developer changes BGE runtime, warmup, model load, memory, latency, or retrieval/rerank count display
- **THEN** the change MUST be localized to a RAG monitoring module, route-local mapper, or route-local data hook
- **AND** it MUST NOT require editing OpenAI provider health or ES query workbench UI.

#### Scenario: Developer changes ES retrieval diagnostics UI
- **WHEN** a developer changes query input, normalized term display, recall route display, ranked result display, or raw diagnostic disclosure
- **THEN** the change MUST be localized to an ES retrieval workbench module and shared search-diagnostic mappers
- **AND** it MUST NOT require editing safety guardrail, usage trend, or provider credential code.

#### Scenario: Developer changes dictionary or outbox diagnostics UI
- **WHEN** a developer changes dictionary category counts, analyzer asset display, mapping version state, document counts, sync status counts, or retry/readiness presentation
- **THEN** the change MUST be localized to dictionary/outbox monitoring modules and mappers
- **AND** it MUST NOT require editing the query workbench result renderer.

#### Scenario: Route-level page code is reviewed
- **WHEN** reviewers inspect the intelligent monitoring route page
- **THEN** the route page MUST primarily compose data hooks and module components
- **AND** it MUST NOT contain all module markup, status mapping, chart mapping, query diagnostic rendering, and CSS class orchestration in one monolithic component.

### Requirement: Intelligent monitoring validation is focused
The admin frontend SHALL verify the monitoring UX with type, build, behavior, and visual checks appropriate to a dense operational page.

#### Scenario: Automated frontend validation runs
- **WHEN** implementation of this UX refactor is complete
- **THEN** teacher frontend typecheck and production build MUST pass
- **AND** any new or changed production chunk warning MUST be documented as accepted or targeted for follow-up.

#### Scenario: Component or mapper tests run
- **WHEN** monitoring modules or mappers are extracted
- **THEN** focused tests MUST cover health tone mapping, attention item generation, query diagnostic term rendering, route/result mapping, and empty/error state behavior where feasible.

#### Scenario: Browser or screenshot QA runs
- **WHEN** visual QA validates the intelligent monitoring page
- **THEN** it MUST capture or inspect the overview and at least the ES retrieval, dictionary/outbox, and RAG modules at normal desktop width
- **AND** it MUST capture or inspect the overview and ES retrieval module at narrow laptop width to verify no text overlap or unusable horizontal clipping.

#### Scenario: Existing route lazy loading is checked
- **WHEN** the production build is inspected after the refactor
- **THEN** the monitoring route and chart dependencies MUST remain behind the existing lazy route boundary
- **AND** unrelated teacher routes MUST NOT newly import monitoring-only modules eagerly.
