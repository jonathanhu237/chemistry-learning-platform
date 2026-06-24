# production-engineering-quality Specification

## Purpose
TBD - created by archiving change production-quality-iteration-three. Update Purpose after archive.
## Requirements
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
The system SHALL provide committed smoke commands that can log in with local-only accounts and visit representative paths for the teacher console and the platform console.

#### Scenario: Teacher E2E smoke succeeds against a running local stack
- **WHEN** the backend and `web-teacher` frontend are running and a local smoke teacher account can be prepared
- **THEN** the teacher smoke command MUST verify that representative teacher paths including overview, videos, learning assistant, question banks, and analytics load without login redirect or error overlay.

#### Scenario: Platform E2E smoke succeeds against a running local stack
- **WHEN** the backend and `web-admin` frontend are running and a local smoke web-admin token is configured
- **THEN** the platform smoke command MUST verify that the teacher-account workbench loads without login redirect or teacher-module leakage.

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

### Requirement: Compose service names are canonical
The production-like Compose topology SHALL use `web-admin`, `web-teacher`, and `web-student` as the canonical frontend service names.

#### Scenario: Compose stack is inspected
- **WHEN** `docker-compose.yml` or compose validation output is inspected
- **THEN** the frontend services MUST be named `web-admin`, `web-teacher`, and `web-student`
- **AND** services named `admin-web` or `student-web` MUST NOT be required by the default application stack.

#### Scenario: Frontend ports are inspected
- **WHEN** Compose frontend port mappings are inspected
- **THEN** `web-admin` MUST default to host port `5175`
- **AND** `web-teacher` MUST default to host port `5174`
- **AND** `web-student` MUST default to host address `222.200.189.249`
- **AND** `web-student` MUST default to host port `5173`.

### Requirement: Retired root backend demo modules stay removed
The backend SHALL remove obsolete root-level demo JSON, standalone RAG, recommendation, and report modules that are no longer used by production runtime, APIs, scripts, or tests.

#### Scenario: Backend architecture validation rejects retired modules
- **WHEN** backend architecture validation is run
- **THEN** `server/app/db.py`, `server/app/rag.py`, `server/app/recommendation.py`, and `server/app/report.py` MUST be absent
- **AND** validation MUST fail if any of those files are reintroduced as root-level compatibility or demo modules

#### Scenario: Live non-import process entrypoints are preserved
- **WHEN** the cleanup is complete
- **THEN** backend modules used through Docker, uvicorn, worker command strings, or current API wiring MUST remain available unless a separate specification retires them

### Requirement: Backend tool metadata uses the canonical runtime entrypoint
Backend tool metadata SHALL point to the documented FastAPI runtime entrypoint instead of deleted compatibility entrypoints.

#### Scenario: FastAPI tool entrypoint is inspected
- **WHEN** `pyproject.toml` is inspected
- **THEN** `[tool.fastapi].entrypoint` MUST be `server.app.app_runtime.main:app`
- **AND** it MUST NOT reference deleted modules such as `server.app.admin_main` or `server.app.main`

### Requirement: Production quality validates split frontend services
Production engineering quality SHALL validate frontend services independently from backend API readiness.

#### Scenario: Full production readiness runs
- **WHEN** full production readiness runs after the frontend deployment split
- **THEN** it MUST validate backend API readiness
- **AND** it MUST validate student frontend readiness
- **AND** it MUST validate admin frontend readiness.

#### Scenario: Compose service list is checked
- **WHEN** production quality checks required Compose services
- **THEN** `web-student`, `web-teacher`, and `web-admin` MUST be included in the required service list for full application validation
- **AND** missing frontend services MUST fail the check.

### Requirement: Admin e2e smoke targets the admin frontend origin
Admin e2e smoke SHALL target the teacher/admin frontend service root after the deployment split.

#### Scenario: Admin e2e smoke opens pages
- **WHEN** admin e2e smoke runs
- **THEN** it MUST open canonical root routes such as `/overview`, `/videos`, `/question-banks`, `/analytics`, and `/learning-assistant` on the admin frontend origin
- **AND** it MUST NOT require `/admin` path prefixes.

### Requirement: Backend slim architecture validation is a production quality gate
The production engineering quality workflow SHALL include backend architecture validation for slim dependency boundaries.

#### Scenario: Production quality validation includes architecture rules
- **WHEN** the backend slim refactor is complete
- **THEN** the documented backend verification sequence MUST run architecture validation
- **AND** it MUST fail on disallowed imports between runtime, API, domain, infrastructure, worker, and script-support owners.

#### Scenario: Compose smoke remains required after backend slimming
- **WHEN** backend slim refactor changes are validated in a production-like stack
- **THEN** the Compose smoke validation MUST verify PostgreSQL, backend, Elasticsearch/IK, tusd, and video-worker services
- **AND** it MUST verify migrations and video-library search readiness using the canonical backend entrypoints.

#### Scenario: Route inventory is verified
- **WHEN** backend API ownership changes during the slim refactor
- **THEN** route inventory tests MUST prove canonical routes are registered exactly once
- **AND** removed aliases are absent unless explicitly retained as canonical.

### Requirement: Destructive backend refactors use validation instead of compatibility layers
Production engineering quality SHALL rely on git, tests, route inventory, Compose smoke, and e2e validation rather than preserving old backend compatibility wrappers.

#### Scenario: Old import compatibility wrapper is proposed
- **WHEN** implementation introduces a wrapper module solely to preserve a previous backend import path
- **THEN** production quality validation MUST treat that wrapper as a failure unless the spec explicitly lists it as a canonical owner.

#### Scenario: Runtime rollback is needed
- **WHEN** a destructive backend slim refactor fails after deployment validation
- **THEN** rollback MUST use git or deployment version rollback
- **AND** the codebase MUST NOT add new compatibility layers as the rollback mechanism.
