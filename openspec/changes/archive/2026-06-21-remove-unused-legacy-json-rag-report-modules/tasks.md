## 1. Retire Unused Backend Modules

- [x] 1.1 Delete `server/app/db.py`, `server/app/rag.py`, `server/app/report.py`, and `server/app/recommendation.py`.
- [x] 1.2 Confirm no repository source imports the retired modules after deletion.

## 2. Align Configuration And Validation

- [x] 2.1 Update `[tool.fastapi].entrypoint` in `pyproject.toml` to `server.app.app_runtime.main:app`.
- [x] 2.2 Extend backend architecture validation so the retired modules fail validation if reintroduced.
- [x] 2.3 Update backend structure documentation to list the retired modules.

## 3. Verify

- [x] 3.1 Run OpenSpec strict validation for `remove-unused-legacy-json-rag-report-modules`.
- [x] 3.2 Run backend architecture validation.
- [x] 3.3 Run focused backend architecture tests.
