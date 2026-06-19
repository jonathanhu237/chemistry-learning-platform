# Productionization Final Notes

This note closes the `productionize-admin-platform` change. The intent of this phase was to make the current internal-beta education platform recoverable, cleaner, and safer to maintain without changing feature behavior, API contracts, question content, RAG evidence semantics, or current data counts.

## Protected Current Resources

The current system of record is protected under `data/seed` and declared by `data/seed/manifests/core_resources.json`.

Protected resources include:

- `data/seed/formal_experiments.json`: 77 formal experiments.
- `data/seed/knowledge_framework/`: 11 chapters, 133 units, 385 knowledge points, plus reviewed curriculum source.
- `data/seed/experiment_points/formal_experiment_point_inventory.json`: 300 current experiment points across 77 experiments.
- `data/seed/question_bank/rebuilt_question_bank_merged_v1.json`: 2310 current point-aware questions across 77 banks.
- `data/seed/question_bank/point_aware_question_bank_schema.json`: current question-bank validation schema.
- `data/seed/canonical_rag/chunks/`: 3637 canonical chunks mirrored from the external RAG package.
- `data/seed/canonical_rag/embeddings/canonical_base_v1/`: 3637 canonical embeddings.
- `data/seed/point_evidence/manual_reviewed_point_evidence.jsonl`: 300 manually reviewed point-to-canonical-chunk bindings.
- `data/seed/import_reports/`: current import reports retained as production manifests.

Any cleanup or refactor that touches data must pass:

```powershell
python scripts/validate_production_resources.py
```

## Removed Or Classified As Disposable

Historical review material and generated local outputs are no longer part of the active production baseline:

- Point-aware question-bank review packets, rebuilt work packages, semantic work packets, pilot reviews, and old release intermediates are disposable because the current inventory, schema, and merged bank are protected in `data/seed`.
- Video-point raw candidates, rerank scratch outputs, smoke packages, and review packets are disposable because the final reviewed point evidence is protected in `data/seed/point_evidence`.
- Playwright screenshots, root UI screenshots, `.tmp`, logs, pytest caches, frontend `dist`, frontend `node_modules`, and Vite logs are generated outputs and should not be committed as source resources.
- `data/media` is deliberately not removed by the guarded cleanup. It is local uploaded/transcoded media and can be discarded only with the database/UI consistency plan in `docs/production-media-cleanup.md`.

The cleanup boundary is encoded in `scripts/cleanup_legacy_artifacts.py` and `data/seed/manifests/legacy_cleanup_plan.json`. Destructive cleanup must remain guarded by the core resource manifest.

## Restore Path

With an empty database and the declared resources available, restore the current system with:

```powershell
python scripts/apply_migrations.py
python scripts/publish_reviewed_curriculum.py
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/point_aware_question_bank.py import --bank-kind default --bank-status published --question-status published --skip-migrations
python scripts/import_manual_reviewed_point_evidence.py --skip-migrations
python scripts/validate_production_resources.py
```

Expected restored counts:

- 77 active formal experiments.
- 11 chapters, 133 units, 385 knowledge points.
- 300 experiment points.
- 77 question banks and 2310 questions.
- 3637 source chunks and 3637 embeddings.
- 300 point evidence bindings.

## Codebase State After Refactor

Frontend:

- `apps/admin-web/src/app/AdminApp.tsx` is the admin app entrypoint; providers, login, auth guard, route registry, navigation, and shell layout live under `apps/admin-web/src/app/*`.
- The old root `apps/admin-web/src/App.tsx` has been removed. Admin routes are deployed at the admin frontend service root, not below `/admin`.
- Admin routes are lazy-loaded from `src/features/*`.
- Heavy optional modules are behind feature boundaries: charts in AI config, Uppy/tus upload code in media, assistant markdown/KaTeX rendering in the learning assistant.
- `apps/admin-web/src/styles.css` now holds global tokens, shell layout, shared helpers, Ant Design baseline overrides, and shared responsive rules.
- Feature styles live beside their owning pages, including `features/question-bank/question-bank.css`, `features/learning-assistant/learning-assistant.css`, `features/media/media.css`, `features/resources/resources.css`, and related page CSS files.

Backend:

- `server/app/admin.py` and the old empty `server/app/experiment_admin.py` compatibility stub have been removed; admin endpoints are owned by feature routers.
- Admin endpoint groups moved into focused routers under `server/app/routers/`.
- Domain logic moved into services under `server/app/services/`, including question bank, point-aware questions, workbench sessions, learning resources, analytics, media/experiments, feedback management, class/roster management, student submissions, and agent RAG/output helpers.
- Endpoint paths, request/response shapes, permissions, and current database effects are intended to remain equivalent.

Operations:

- `.env.example`, Docker expectations, health checks, backup/restore notes, migration discipline, and validation commands are documented in `docs/production-operations.md`.
- The default Compose application graph now includes separate `student-web` and `admin-web` services; the backend serves API and health routes only.
- Future migrations must continue from `014_...`; historical duplicate `010_...` migrations are append-only history and should not be renamed.

## Validation Chain

Use the full local release gate:

```powershell
python scripts/validate_production_readiness.py --install-frontend
openspec validate productionize-admin-platform --strict
git status --short
```

The validation script covers protected resources, OpenSpec strict validation, backend import smoke, backend tests, frontend typecheck, frontend tests, frontend build, and core data counts. Generated frontend build output remains reproducible and should not be treated as source.
