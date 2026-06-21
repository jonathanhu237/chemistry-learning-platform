## 1. Data Model And Migration

- [x] 1.1 Add media asset lifecycle columns such as `lifecycle_status`, `archived_at`, `archived_by`, and `archive_reason` with existing rows defaulting to active.
- [x] 1.2 Add media asset lifecycle event/outbox storage for `media_asset_archived` events with actor, reason, previous state, and affected binding summary.
- [x] 1.3 Update fresh schema baselines and migration tests so upload/processing status remains separate from asset lifecycle status.
- [x] 1.4 Define the destructive upgrade/rebuild path for derived media lifecycle and ES index state, including backup and rollback notes.

## 2. Media Asset Lifecycle Backend

- [x] 2.1 Implement media asset archive impact planning that reports active catalog point bindings, legacy generic bindings, processing jobs, renditions, fingerprints, duplicate candidates, and file-state summary.
- [x] 2.2 Implement the media asset archive command that validates permissions, writes lifecycle state, records the lifecycle event, and returns affected-binding summary.
- [x] 2.3 Ensure archived assets are hidden by default from media asset lists and catalog video pickers while remaining available to explicit audit/maintenance filters.
- [x] 2.4 Reject student and preview playback or thumbnail access for archived media assets.
- [x] 2.5 Keep teacher archive separate from physical file deletion and update media cleanup tooling to require archived/tombstoned state before deleting DB-backed files.

## 3. Catalog Binding Cleanup

- [x] 3.1 Add a catalog-owned handler for media asset archived events that archives all non-archived point video bindings for the asset.
- [x] 3.2 Record binding archive metadata including reason, media asset id, lifecycle event id, actor, and previous binding state.
- [x] 3.3 Recompute affected point video readiness and preserve point content, equations, related links, publication state, questions, and assessments.
- [x] 3.4 Queue ES sync and RAG evidence freshness jobs for every affected active point placement using the existing Postgres-backed job model.
- [x] 3.5 Make archive handling idempotent for repeated events and partial retries.

## 4. Elasticsearch Purity

- [x] 4.1 Remove video titles, binding titles, media asset titles, original file names, media ids, thumbnail paths, stream paths, upload status, processing status, and media metadata from incremental ES document source and `search_text`.
- [x] 4.2 Remove the same video-resource semantic fields from full rebuild document construction and local fallback searchable text.
- [x] 4.3 Preserve only allowed non-semantic readiness signals such as `has_video` and `video_count` where needed.
- [x] 4.4 Update ES mapping version and mapping properties so forbidden video-resource fields are not mapped or serialized.
- [x] 4.5 Update search diagnostics and route-match explanations so they cannot report matches from video resource labels.

## 5. Teacher Frontend

- [x] 5.1 Add an archive/delete action for stored assets in the `/videos` resource library that is distinct from pending upload queue removal.
- [x] 5.2 Fetch and render the archive impact plan before confirmation, including affected point count and representative catalog paths.
- [x] 5.3 Use confirmation copy that says point video bindings will be removed while point content remains.
- [x] 5.4 Call only media lifecycle archive APIs from the resource library and never call catalog binding APIs directly.
- [x] 5.5 Refresh asset metrics, lists, duplicate review state, and affected success feedback after archive.

## 6. Rebuild And Operations

- [x] 6.1 Update `scripts/rebuild_video_library_index.py` or equivalent rebuild workflow to recreate the ES index with the pure mapping.
- [x] 6.2 Add validation that scans generated/indexed documents for forbidden video-resource fields and forbidden video-title leakage.
- [x] 6.3 Update production operations docs for destructive ES rebuild, media archive state, and safe physical cleanup.
- [x] 6.4 Ensure production readiness validation fails when stale ES documents still contain video resource labels or metadata.

## 7. Tests And Verification

- [x] 7.1 Add backend tests for media archive impact plans with active catalog point bindings and no-binding assets.
- [x] 7.2 Add backend tests for media archive event handling, idempotent catalog binding archival, and point readiness recalculation.
- [x] 7.3 Add backend tests proving student/preview media endpoints reject archived assets.
- [x] 7.4 Add ES document tests proving video resource titles and original file names do not appear in `search_text`, ES source, local fallback search text, snippets, or diagnostics.
- [x] 7.5 Add frontend tests for archive confirmation copy, bound-point impact rendering, no-binding archive flow, and stored-asset delete action separation from upload queue removal.
- [x] 7.6 Run targeted backend tests for media lifecycle, catalog tree services, video-library search documents, route inventory, and architecture boundaries.
- [x] 7.7 Run teacher frontend typecheck/build and any available tests covering `/videos`.
- [x] 7.8 Run OpenSpec strict validation and the production/video-library ES validator after destructive rebuild.
- [x] 7.9 Add and run teacher E2E coverage for archiving a bound video resource, confirming binding-impact copy, point-content preservation, active-library hiding, and ES purity before/after archive.
