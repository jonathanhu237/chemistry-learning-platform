## FastAPI Lifespan Migration Result: 2026-06-17

Changed files:

- `server/app/admin_main.py`
- `server/app/bge_service.py`

Implementation notes:

- Replaced the admin service startup `@app.on_event("startup")` handler with an async lifespan context.
- Preserved the admin startup database check gated by `settings.run_db_check_on_startup`.
- Preserved media-root creation through `settings.media_root.mkdir(parents=True, exist_ok=True)`.
- Replaced the BGE service startup warmup `@app.on_event("startup")` handler with an async lifespan context.
- Preserved the existing background-thread warmup flow and health/metrics warmup state.

Validation:

```powershell
python -c "import server.app.admin_main as m; print(m.app.title); import server.app.bge_service as b; print(b.app.title)"
python -m pytest server\tests -q
rg "on_event" server/app -n
docker compose --profile rag up -d --build backend bge-rag
```

Results:

- PASS: admin and BGE app import smoke.
- PASS: backend tests, `44 passed`.
- PASS: no remaining `on_event` references under `server/app`.
- PASS: Docker backend health returned `{"status":"ok"}`.
- PASS: Docker BGE health returned `ok=true`, `warmup.status=succeeded`, `models_ready=true`, `duration_ms=37450.33`.

Behavior guardrails:

- Existing route registration, health response shape, static admin serving, database startup check, and BGE warmup semantics were preserved.
- No API path, permission, migration, core resource, or question/evidence data changed.
