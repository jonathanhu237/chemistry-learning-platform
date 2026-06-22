## ADDED Requirements

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
