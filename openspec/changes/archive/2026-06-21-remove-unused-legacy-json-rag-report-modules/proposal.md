## Why

The backend still contains several root-level modules from the earlier JSON-backed demo/RAG/report era even though production runtime, APIs, and tests no longer import them. Keeping these modules makes the current backend ownership map harder to trust and leaves a path for obsolete code to be accidentally revived.

## What Changes

- Remove unused root-level backend modules for the old JSON/RAG/report/recommendation flow.
- Update backend architecture validation so those retired modules cannot be reintroduced silently.
- Correct the FastAPI tool entrypoint in `pyproject.toml` to the canonical runtime module.
- Preserve current API routes, domain behavior, seed resources, Docker service entrypoints, BGE RAG service, and video similarity helper behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `production-engineering-quality`: add backend cleanup requirements for retired root-level demo modules and canonical runtime entrypoint validation.

## Impact

- Affected backend files: `server/app/db.py`, `server/app/rag.py`, `server/app/report.py`, `server/app/recommendation.py`, `scripts/validate_backend_architecture.py`, backend architecture tests, and backend structure documentation.
- Affected configuration: `pyproject.toml` FastAPI entrypoint.
- No API contract, database schema, protected seed resource, Docker Compose service, or frontend runtime behavior is intended to change.
