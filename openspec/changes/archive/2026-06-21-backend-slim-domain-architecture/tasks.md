## 1. Baseline And Inventory

- [x] 1.1 Capture the current backend route table for auth, admin, student, static frontend, health, and legacy endpoints.
- [x] 1.2 Classify every registered route as canonical, legacy alias, static/runtime, or candidate for deletion.
- [x] 1.3 Capture current worker entrypoints, CLI scripts, and maintenance commands that import backend application code.
- [x] 1.4 Capture current large backend modules and service files with line counts, primary responsibilities, and suspected mixed concerns.
- [x] 1.5 Capture current backend imports from FastAPI inside reusable service/domain-like modules.
- [x] 1.6 Capture current cross-service private-helper imports such as search/read-model code importing student learning internals.
- [x] 1.7 Document current media responsibilities in `server/app/media.py` and `server/app/video_worker.py`.
- [x] 1.8 Document current experiment point, student point detail, video-library search, ES index, and AI evidence ownership paths.
- [x] 1.9 Produce the initial backend owner map that identifies target owners for every currently mixed backend area.
- [x] 1.10 Produce the first canonical route inventory and list route aliases that will be deleted rather than preserved.

## 2. Architecture Guardrails

- [x] 2.1 Add an architecture validation command or script that scans Python imports using a structured parser or equivalent reliable approach.
- [x] 2.2 Configure validation rules so reusable domain modules cannot import FastAPI, Starlette responses, routers, or runtime app wiring.
- [x] 2.3 Configure validation rules so worker modules cannot import FastAPI, routers, app runtime, or broad web-only service modules.
- [x] 2.4 Configure validation rules so API/router modules cannot import worker entrypoints.
- [x] 2.5 Configure validation rules so deleted legacy modules cannot remain as compatibility wrappers.
- [x] 2.6 Configure validation rules so canonical route inventory can be compared against the app route table.
- [x] 2.7 Add failing characterization output for current violations before major refactor work begins.
- [x] 2.8 Add architecture validation documentation to backend operations or engineering quality docs.
- [x] 2.9 Add backend tests for route inventory exactness and duplicate route registration.
- [x] 2.10 Add tests proving removed legacy aliases are absent after the canonical route inventory is accepted.

## 3. Runtime And API Shell Slimming

- [x] 3.1 Create the target backend runtime owner for app construction, lifespan, middleware, static frontend mounts, and health routes.
- [x] 3.2 Move auth route registration into an explicit auth API owner.
- [x] 3.3 Move admin route modules into an explicit admin API owner while preserving canonical route paths.
- [x] 3.4 Move student route modules into an explicit student API owner while preserving canonical route paths.
- [x] 3.5 Retire or relocate `server/app/admin_main.py` according to the final runtime owner decision.
- [x] 3.6 Retire or relocate `server/app/main.py` compatibility entrypoint rather than keeping it as a wrapper, unless it becomes the canonical runtime owner.
- [x] 3.7 Remove obsolete route aliases identified in the canonical inventory.
- [x] 3.8 Update Docker, scripts, tests, and docs to import the canonical FastAPI runtime entrypoint.
- [x] 3.9 Update route inventory tests to match the new canonical runtime route table.
- [x] 3.10 Verify backend app import does not initialize worker-only or CLI-only modules.

## 4. Infrastructure Layer Extraction

- [x] 4.1 Move database session, connection checks, and migration-facing helpers into infrastructure ownership without compatibility wrappers.
- [x] 4.2 Move settings/config loading and startup validation into infrastructure ownership.
- [x] 4.3 Move filesystem/media-root path helpers that are not domain-specific into infrastructure ownership.
- [x] 4.4 Move Elasticsearch client primitives that are not video-library-specific into infrastructure ownership where appropriate.
- [x] 4.5 Update all canonical imports to the new infrastructure owners.
- [x] 4.6 Delete old infrastructure module paths that are no longer canonical.
- [x] 4.7 Verify scripts and workers can import infrastructure modules without importing FastAPI runtime.
- [x] 4.8 Run backend tests covering settings, database connectivity, and migration scripts after infrastructure moves.

## 5. Media Domain Split

- [x] 5.1 Create media asset domain owner for asset creation, upload completion, duplicate precheck, listing, and file summary behavior.
- [x] 5.2 Create media binding domain owner for binding creation, publication, unpublication, deletion, and binding metadata behavior.
- [x] 5.3 Create media processing queue domain owner for enqueue, retry, active processing status, and processing job records.
- [x] 5.4 Create media lifecycle domain owner for cleanup dry-run, referenced path discovery, orphan file reporting, and dependency counts.
- [x] 5.5 Create media visibility domain owner for student-visible media predicates and shared status ordering.
- [x] 5.6 Create media file helper owner for checksum, validation, safe path generation, and relative path resolution.
- [x] 5.7 Move admin media API routes to import only the media domain owners they need.
- [x] 5.8 Move experiment catalog media-binding calls to canonical media binding and asset owners.
- [x] 5.9 Move student media playback helpers to canonical media visibility and asset read owners.
- [x] 5.10 Move media cleanup scripts to canonical lifecycle owners.
- [x] 5.11 Delete `server/app/media.py` after all canonical imports are migrated.
- [x] 5.12 Verify `video_worker` imports only processing-safe media and infrastructure owners.
- [x] 5.13 Add tests proving media binding changes enqueue point search projection events without involving `video_worker`.
- [x] 5.14 Add tests proving uploaded unbound media assets do not become student video-library search documents.

## 6. Video Worker Slimming

- [x] 6.1 Move `video_worker` into the canonical worker owner.
- [x] 6.2 Update Docker Compose, Dockerfiles, commands, and process documentation to use the canonical worker module path.
- [x] 6.3 Split worker job claiming, phase updates, failure handling, completion handling, and asset persistence into worker-safe domain helpers where useful.
- [x] 6.4 Keep ffmpeg/ffprobe process execution and media derivative generation inside worker-owned code or worker-safe helpers.
- [x] 6.5 Verify worker import validation fails if FastAPI or API routers are imported.
- [x] 6.6 Rebuild backend and video-worker images after worker path changes.
- [x] 6.7 Run Compose stack smoke to verify `video-worker` starts and remains up with the canonical imports.
- [x] 6.8 Add or update worker-focused tests for processing queue behavior and worker-safe import boundaries.

## 7. Experiment Point Domain Split

- [x] 7.1 Create canonical experiment point owner for stable point identity, point key generation, backfill support, and reference validation.
- [x] 7.2 Create point learning content owner for draft save, validation, publish, unpublish, archive, and audit behavior.
- [x] 7.3 Create related point links owner for default nearby links and manual overrides.
- [x] 7.4 Create point search event owner for search-index state enqueue/upsert/delete markers.
- [x] 7.5 Move admin point workspace assembly out of broad experiment services into an explicit point workspace/read model owner.
- [x] 7.6 Move student point detail payload assembly out of admin point services into a student read-model owner.
- [x] 7.7 Ensure point content services do not import FastAPI and use domain exceptions or result objects.
- [x] 7.8 Update admin experiment API routes to translate point-domain errors into HTTP responses.
- [x] 7.9 Update student learning API routes to translate point-detail errors into HTTP responses.
- [x] 7.10 Delete old experiment point compatibility import paths after canonical imports are migrated.
- [x] 7.11 Run point content, related link, student detail, and canonical point reference tests after the split.

## 8. Student Video-Library And ES Projection Split

- [x] 8.1 Create video-library document builder owner that builds point-centered documents from published point content and student-visible resource state.
- [x] 8.2 Create video-library search service owner that handles query execution and typed actionable result grouping.
- [x] 8.3 Create video-library ES index client owner for mapping, index creation, health, upsert, and delete operations.
- [x] 8.4 Create video-library sync owner for index status updates, rebuild command support, and retryable failure state.
- [x] 8.5 Remove video-library service imports of private helpers from student learning services.
- [x] 8.6 Ensure video-library search continues to index published point content even when the point has no published video.
- [x] 8.7 Ensure generic teacher media assets are never indexed directly as student video-library search documents.
- [x] 8.8 Ensure AI evidence and source chunks are not used as student-facing video-library body copy.
- [x] 8.9 Update `rebuild_video_library_index.py` and validation scripts to use canonical video-library owners.
- [x] 8.10 Run chemistry search, ES adapter, video-library, and Compose search validation tests after the split.

## 9. AI, RAG, Question, And Assessment Domain Cleanup

- [x] 9.1 Audit assistant/RAG modules for web-runtime imports and mixed assistant, evidence, and question-workbench concerns.
- [x] 9.2 Move assistant runtime, policy, retrieval, output normalization, evidence shaping, and guardrails into canonical assistant domain owners.
- [x] 9.3 Ensure assistant and question diagnostics keep `experiment_video_point_evidence` and `source_chunks` separate from student point display content.
- [x] 9.4 Move question bank validation helpers out of broad services or make their canonical owner explicit.
- [x] 9.5 Move point-aware question suggestion ownership to canonical question/point domains without private helper leakage.
- [x] 9.6 Move pretest, posttest, grading, and mastery update behavior into canonical assessment owners.
- [x] 9.7 Ensure assessment domain modules do not import FastAPI directly.
- [x] 9.8 Update admin and student assessment/question routers to translate domain errors into HTTP responses.
- [x] 9.9 Run assistant, question bank, question workbench, point-aware question, pretest, posttest, and mastery tests after cleanup.

## 10. Roster, Analytics, Feedback, Platform, And Catalog Cleanup

- [x] 10.1 Move roster and class management logic into canonical roster/class domain owners without FastAPI imports.
- [x] 10.2 Move analytics read models into canonical analytics owners without router or HTTP dependencies.
- [x] 10.3 Move feedback listing, status update, attachment handling, and reporting into canonical feedback owners.
- [x] 10.4 Move platform settings and AI access configuration into canonical platform/configuration owners.
- [x] 10.5 Move formal experiment catalog and learning resource read models into explicit catalog/resource owners.
- [x] 10.6 Update admin routers for roster, analytics, feedback, platform, experiments, and resources to use canonical owners.
- [x] 10.7 Delete old service compatibility paths after all canonical imports are migrated.
- [x] 10.8 Run domain-relevant backend tests for roster, analytics, feedback, platform settings, catalog, and learning resources.

## 11. HTTP Boundary And Error Translation

- [x] 11.1 Define shared domain exception/result types or per-domain equivalents for not found, validation, conflict, forbidden, and unavailable states.
- [x] 11.2 Add API translation helpers that convert domain errors into HTTP status codes and response payloads.
- [x] 11.3 Remove direct FastAPI imports from reusable domain modules.
- [x] 11.4 Update router tests to assert HTTP behavior remains correct after domain error translation.
- [x] 11.5 Update service/domain tests to assert domain outcomes without HTTP framework dependency.
- [x] 11.6 Run architecture validation and confirm no reusable domain owner imports FastAPI.

## 12. Scripts, Migrations, And Maintenance Commands

- [x] 12.1 Update migration runner scripts to import canonical infrastructure modules.
- [x] 12.2 Update production resource validation scripts to import canonical domain/read-model owners.
- [x] 12.3 Update experiment point validation scripts to import canonical point owners.
- [x] 12.4 Update video-library search validation and rebuild scripts to import canonical video-library owners.
- [x] 12.5 Update media lifecycle cleanup scripts to import canonical media lifecycle owners.
- [x] 12.6 Update question and evidence import/generation scripts to import canonical question, catalog, and evidence owners.
- [x] 12.7 Verify scripts do not initialize FastAPI runtime as an import side effect.
- [x] 12.8 Run script-level smoke checks for migrations, production readiness, resource validation, experiment point validation, video-library index rebuild, and media cleanup dry-run.

## 13. Frontend Audit Only

- [x] 13.1 Audit admin frontend oversized pages, including experiments, media resources, learning assistant, question banks, learning resources, analytics, and classes.
- [x] 13.2 Audit admin frontend monolithic API file ownership and backend endpoint assumptions.
- [x] 13.3 Audit admin route shell eager imports and route-owned feature boundaries.
- [x] 13.4 Produce admin frontend follow-up recommendations grouped by feature owner, risk, and verification gate.
- [x] 13.5 Audit student frontend oversized modules, including API, app root, atom viewer, assistant chat, experiment point detail, video library, and e2e test surface.
- [x] 13.6 Audit student frontend route shell, route-stack navigation, and backend endpoint assumptions.
- [x] 13.7 Produce student frontend follow-up recommendations grouped by feature owner, risk, and verification gate.
- [x] 13.8 Limit frontend code edits in this backend slim change to canonical endpoint updates, test updates, and minimal required fixes.

## 14. Documentation And Operations

- [x] 14.1 Document the final backend package structure and dependency direction rules.
- [x] 14.2 Document the final backend domain owner map.
- [x] 14.3 Document the final route inventory and removed legacy aliases.
- [x] 14.4 Document canonical runtime, worker, and CLI entrypoints.
- [x] 14.5 Document how to run architecture validation locally.
- [x] 14.6 Update production operations docs for canonical Compose service commands after entrypoint moves.
- [x] 14.7 Update developer onboarding docs with backend slim architecture conventions.
- [x] 14.8 Add implementation notes explaining why compatibility wrappers were intentionally not kept.

## 15. Verification

- [x] 15.1 Run `openspec validate backend-slim-domain-architecture --strict`.
- [x] 15.2 Run backend architecture validation and confirm it passes.
- [x] 15.3 Run route inventory tests and confirm canonical routes are registered exactly once.
- [x] 15.4 Run backend unit tests covering media, worker-safe imports, experiment points, student learning, video library, ES projection, assistant/RAG, questions, assessments, roster, analytics, feedback, platform settings, catalog, and production resources.
- [x] 15.5 Run migration and production resource validation scripts.
- [x] 15.6 Run video-library ES rebuild and validation against the Compose Elasticsearch/IK service.
- [x] 15.7 Run `python scripts/validate_compose_stack.py` or its canonical replacement against the full required Compose stack.
- [x] 15.8 Rebuild and start backend plus video-worker containers using canonical entrypoints.
- [x] 15.9 Run admin frontend typecheck/build/e2e only as needed for endpoint canonicalization changes and document the result.
- [x] 15.10 Run student frontend typecheck/build/e2e/mobile QA only as needed for endpoint canonicalization changes and document the result.
- [x] 15.11 Run `git diff --check`.
- [x] 15.12 Produce final implementation notes with removed compatibility layers, frontend audit summaries, validation commands, and residual risks.
