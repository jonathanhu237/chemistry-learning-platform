## Baseline

- Branch at start: `main`.
- Worktree at start: code was clean except the untracked OpenSpec change directory `openspec/changes/experiment-catalog-tree-point-architecture/`.
- Docker Compose services were already running and healthy for `postgres`, `elasticsearch`, `backend`, `student-web`, `admin-web`, `tusd`, and `video-worker`; `bge-rag` was also running under its profile.
- Initial readiness without compose smoke failed because local validation used the old default local Postgres port while Compose exposes Postgres on `127.0.0.1:15432`.
- Baseline readiness passed with compose host env via:

```bash
python scripts/validate_production_readiness.py --change experiment-catalog-tree-point-architecture --run-compose-smoke
```

Passed stages: compose smoke, protected resource manifest, video-library ES/IK readiness, legacy experiment point identity validation, OpenSpec strict validation, backend import smoke, backend architecture validation, backend tests, admin import boundaries/typecheck/tests/build/build report, and student typecheck/tests/build.

## Legacy Identity Inventory

Authoritative legacy point identity appears as `(experiment_id, point_key)` in these areas:

- Database tables: `formal_experiments`, `experiment_video_points`, `experiment_point_learning_content`, `experiment_point_related_links`, `experiment_video_point_search_index_state`, `experiment_video_point_evidence`, `experiment_questions`, `experiment_question_drafts`, assessment attempt/session metadata, student learning events, analytics read queries, feedback context, and media binding metadata.
- Backend admin routes: `/api/admin/experiments/{experiment_id}/video-points`, `/resources`, `/content`, `/publication`, and `/related-links`.
- Backend student routes: `/api/student/experiment-groups/{parent_code}` and `/api/student/experiments/{experiment_id}?point_key=...`.
- Backend domains: `server/app/domains/experiment_points/*`, `server/app/domains/video_library/search.py`, question workbench/generation/point-aware flows, assessment flows, analytics read models, feedback capture, and assistant context helpers.
- Admin frontend: `apps/admin-web/src/api/experiments.ts`, `features/experiments/*`, point content mapper/forms, video binding panels, question-bank displays, analytics types, and learning-assistant/feedback request payloads.
- Student frontend: `apps/student-web/src/api.ts`, `features/experiments/*`, learning chapter views, assistant point starter, assessment handoff, feedback context, and route helpers around experiment detail pages.

## Old-to-New Identity Mapping Assumptions

- Every former `formal_experiments.id` migrates to one chapter-scoped catalog directory node.
- Every former `experiment_video_points.(experiment_id, point_key)` migrates to a stable point catalog node under the migrated formal-experiment node.
- Deterministic generated ids use stable, namespaced hashes so rerunning migrations does not create divergent identities:
  - formal experiment directory node: `cat-exp-<sha1(formal_experiment_id)>`
  - point node: `cat-point-<sha1(experiment_id + "::" + point_key)>`
- The legacy identity map records both formal experiment rows and point rows for audit and repair. New write paths use catalog node ids only.
- Existing point content is migrated into point-node content; `teacher_note` starts empty because current trusted content is student-facing.
- Existing related links are migrated from `(target_experiment_id, target_point_key)` to `target_node_id` through the identity map.
- Existing media bindings are migrated when `media_bindings.metadata` resolves to legacy point metadata.
- Question, assistant, assessment, analytics, and feedback metadata gain point-node ids where a legacy identity can be resolved. Existing evidence chunks/source refs are preserved.

## Removed Compatibility Surface

These old write/read contracts are not kept as authoritative compatibility paths:

- Admin experiment video-point write APIs:
  - `POST /api/admin/experiments/{experiment_id}/video-points/{point_key}/resources`
  - `PUT /api/admin/experiments/{experiment_id}/video-points/{point_key}/content`
  - `POST /api/admin/experiments/{experiment_id}/video-points/{point_key}/publication`
  - `PUT /api/admin/experiments/{experiment_id}/video-points/{point_key}/related-links`
- Student learning APIs:
  - `GET /api/student/experiment-groups/{parent_code}`
  - `GET /api/student/experiments/{experiment_id}?point_key=...`
- Frontend route dependencies using experiment id plus point key for point detail navigation.

## ES/IK Requirement Confirmation

- `docker-compose.yml` builds `elasticsearch` from `server/Dockerfile.elasticsearch-ik`.
- Backend Compose env requires `VIDEO_LIBRARY_SEARCH_BACKEND=elasticsearch`, `VIDEO_LIBRARY_SEARCH_ANALYZER=ik_max_word`, and `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=false`.
- `scripts/validate_compose_stack.py` already smoke-tests `ik_max_word`; this change must extend the same readiness path to verify dictionary assets, analyzer behavior, and point-node search indexing.
