## ADDED Requirements

### Requirement: Representative admin pages are free of known deprecation noise
The system SHALL remove known Ant Design deprecation warnings from representative admin pages covered by browser smoke, including warnings for `Space.direction`, `Tooltip.overlayClassName`, `Alert.message`, `Spin.tip`, and `Drawer.width`.

#### Scenario: Browser smoke reports no known Ant Design deprecation warnings
- **WHEN** the e2e smoke visits representative authenticated admin pages
- **THEN** the smoke output MUST NOT contain the known Ant Design deprecation warning messages listed in this requirement

### Requirement: Browser-smoke 404 diagnostics are actionable
The system SHALL either fix the generic 404 observed during browser smoke or report the requested URL, method, status, and owning page so maintainers can distinguish harmless local static misses from real missing resources.

#### Scenario: A 404 occurs during smoke
- **WHEN** a browser-smoke run observes an HTTP 404 response
- **THEN** the smoke output MUST include enough request information to identify the missing resource and page context

### Requirement: E2E smoke is repeatable
The system SHALL provide a committed e2e smoke command that logs in with a local-only admin account and visits the representative admin paths for overview, videos, learning assistant, question banks, and analytics.

#### Scenario: E2E smoke succeeds against a running local stack
- **WHEN** the backend and frontend are running and a local smoke admin can be prepared
- **THEN** the e2e smoke command MUST verify that all representative paths load without login redirect or error overlay

### Requirement: E2E validation is opt-in
The production-readiness validation script SHALL expose e2e smoke as an explicit opt-in stage rather than running it by default.

#### Scenario: Default validation avoids browser/runtime coupling
- **WHEN** `python scripts/validate_production_readiness.py` is run without e2e flags
- **THEN** the script MUST NOT require a running frontend dev server, browser executable, or local smoke admin

#### Scenario: Opt-in validation runs browser smoke
- **WHEN** `python scripts/validate_production_readiness.py` is run with the e2e opt-in flag
- **THEN** the script MUST run the committed e2e smoke command and fail if representative paths do not load

### Requirement: Assistant modularization preserves behavior
The system SHALL continue splitting learning-assistant implementation details out of `server/app/agent.py` while preserving public endpoint imports, response schemas, guardrails, retrieval behavior, evidence shaping, and formula normalization.

#### Scenario: Assistant-focused tests pass after extraction
- **WHEN** assistant runtime helpers are moved into service modules
- **THEN** assistant-focused characterization tests and backend tests MUST pass without changing protected data or endpoint contracts

### Requirement: Media lifecycle schema changes are justified
The system SHALL not add a media archive/tombstone migration unless the implementation requires durable database state beyond the existing cleanup dry-run and missing-file status behavior.

#### Scenario: No schema change is required
- **WHEN** media lifecycle improvements can be completed with existing columns and scripts
- **THEN** no `014_...` migration MUST be added

#### Scenario: Schema change is required
- **WHEN** media lifecycle improvements require durable archive or tombstone state
- **THEN** the next migration MUST use the `014_...` prefix or later and MUST NOT rename, remove, reorder, or rewrite existing migrations

### Requirement: Production readiness workflow remains manual
The GitHub production readiness workflow SHALL remain manually triggered unless the project owner explicitly requests automatic push or pull-request execution.

#### Scenario: Pushes do not trigger production readiness workflow
- **WHEN** changes are pushed to `main` or `codex/**`
- **THEN** the production readiness workflow MUST NOT run solely because of that push
