# Implementation Result

## Runtime Import

- Imported `data/seed/experiment_catalog/point_content_seed.json` into the local Docker Postgres database on 2026-06-21 UTC.
- The retired previous point-content seed attempt was removed by the reset path.
- Persisted counts:
  - point content records: 76
  - equation-mode records: 71
  - text-mode records: 5
  - reaction equation rows: 122
  - queued search documents: 76

## ES Rebuild

- Recreated `student-video-library` with mapping version `chemistry-point-placement-v4`.
- Indexed documents: 76.
- Sync state: `synced=76`, no retryable rows.
- Cluster health in the single-node local stack is `yellow`, expected because replica shards are unassigned.

## Key Query Checks

- `H2O2 KMnO4` ranks `H₂O₂ + KMnO₄ | 酸性体系` first.
- `双氧水 高锰酸钾` ranks `H₂O₂ + KMnO₄ | 酸性体系` first.
- `SO2 刺激性气体` uses strict alias/formula routes plus phenomenon/reaction-feature routes.
- `黄色沉淀` uses phenomenon tags, not strict chemistry synonyms.
- `氧化性` uses property tags and supporting text routes.

## Verification

- `python -m pytest server/tests/test_chemistry_search.py server/tests/test_chemistry_retrieval_vocabulary.py server/tests/test_student_video_library.py server/tests/test_catalog_outline_seed.py server/tests/test_catalog_point_ai_context.py server/tests/test_catalog_point_jobs.py server/tests/test_catalog_point_equations.py`
- `python scripts/validate_experiment_catalog_seed.py`
- `npm run typecheck` in `apps/web-teacher`
- `npm run build` in `apps/web-teacher`
- `openspec status --change add-chemistry-point-retrieval-monitoring --json`
- `openspec validate add-chemistry-point-retrieval-monitoring --strict`
