## Context

The current teacher video resource library is an ingestion and inspection surface for uploaded media assets. It lists processing state, thumbnails, duplicate hints, preview, and retry actions, but it does not expose a stored-asset delete/archive action. Catalog point authoring manages a separate `experiment_catalog_point_media_bindings` relationship where one canonical point has at most one active video reference. Removing a point video currently archives the binding, not the asset.

The current student video-library search index is a derived point-placement projection. It excludes raw unbound media-library uploads, but the document builders still pull bound video titles into `search_text`. The incremental builder also serializes `videos: [{media_id, title}]` into the ES document source. Product-wise, this is wrong: a video title or file name is a teacher-only operational label, while the point title, principle, phenomenon explanation, safety note, equations, related points, and path already contain the complete student-facing meaning.

The repository already has a Postgres-backed outbox/job pattern for catalog point ES/RAG work, and cleanup documentation already refuses DB-backed media file deletion until an explicit archive/tombstone state exists. This change should reuse those patterns rather than introducing an external broker or putting catalog binding logic inside upload/processing code.

## Goals / Non-Goals

**Goals:**

- Give media assets an explicit lifecycle state for active versus archived resources.
- Add an impact-aware teacher archive/delete workflow for video resources.
- Keep media upload and processing isolated from catalog binding business rules.
- Archive affected catalog point video bindings when a media asset is archived.
- Trigger existing point status, ES, and RAG freshness mechanisms after binding cleanup.
- Make student video-library Elasticsearch documents semantically pure: point content only, with video resource names and metadata excluded.
- Preserve `has_video` and `video_count` as point readiness signals where useful.
- Permit destructive database and ES rebuilds to remove old lifecycle/index assumptions.

**Non-Goals:**

- This change does not add a new teacher-facing publish/unpublish state for videos.
- This change does not add transcripts, ASR, semantic video analysis, playlists, chapters, or multiple videos per point.
- This change does not make physical file deletion part of the teacher confirmation path.
- This change does not make Elasticsearch the source of truth for point detail body or media playback.
- This change does not move upload into the catalog point editor.

## Decisions

### Decision 1: Separate processing status from lifecycle status

`media_assets.upload_status` should continue to describe ingestion/processing state: pending, processing, ready, failed, or replaced. Add a separate asset lifecycle field, such as `lifecycle_status`, with active and archived states. Optional later hard-delete/tombstone states may exist for maintenance, but teacher deletion should first archive the asset.

Rationale: processing status answers "can this file be read or played"; lifecycle status answers "should this resource remain available in the library and authoring picker." Mixing the two would make failed-vs-archived and ready-vs-deleted ambiguous.

Alternative considered: add `archived` to `upload_status`. Rejected because it reuses a media processing field for a product lifecycle concept and would ripple into worker logic.

### Decision 2: Archive assets first; physical file deletion is a later cleanup

Teacher delete/archive should mark the DB asset archived and make it unavailable to authoring and student playback. It should not immediately remove original, rendition, thumbnail, or fingerprint files. File cleanup remains a maintenance operation that can safely delete orphan files or archived asset files after policy checks.

Rationale: media files are large and operational, but deleting them synchronously from the UI risks partial failure, broken previews, and unrecoverable mistakes. An archived DB record gives the system a stable tombstone for audit and cleanup.

Alternative considered: immediately delete `media_assets` and rely on `ON DELETE CASCADE`. Rejected because cascade would silently remove bindings without queueing ES/RAG updates or recording impact.

### Decision 3: Use explicit lifecycle events as the boundary

Archiving a media asset should write an auditable lifecycle event such as `media_asset_archived`. The media domain may expose an event dispatcher/handler call, but the catalog binding cleanup should live in a catalog-owned handler. In one transaction, the API can archive the asset, append the event, invoke registered handlers, archive affected bindings, and enqueue point jobs.

Rationale: this follows the existing Postgres-backed outbox/job style without deploying Redis, RabbitMQ, Celery, or another broker. It also makes the media domain publish facts while catalog owns catalog consequences.

Alternative considered: import catalog services directly from the media asset archive function and update bindings inline. Rejected because it pollutes the upload/asset boundary and makes video-worker-safe media modules harder to reason about.

### Decision 4: Impact preview is required before archive

The archive endpoint should have a companion deletion/archival plan endpoint. The plan should return total active catalog bindings, affected placement ids, canonical point ids, point titles, catalog paths, publication/readiness state, and whether the student side currently has a playable video.

Rationale: teachers need to understand that deleting a resource removes point video bindings while leaving point content intact. This is a product confirmation, not a low-level database constraint.

Alternative considered: warn only when `association_count > 0`. Rejected because the current count only covers old generic `media_bindings` and does not explain affected catalog points.

### Decision 5: Catalog cleanup archives bindings, not point content

When `media_asset_archived` is handled, every non-archived `experiment_catalog_point_media_bindings` row for that asset should be archived with metadata recording the reason, asset id, lifecycle event id, actor, and previous binding state. Point content, equations, related links, publication status, and assessment/question bindings must remain unchanged.

Rationale: video resource deletion should make a point "missing video" when no other active ready video exists, but it should not delete the learning point itself.

Alternative considered: prevent deletion whenever a point references the asset. Rejected because the user explicitly wants deletion to be able to remove bindings after confirmation.

### Decision 6: ES index must contain point semantics only

Both incremental and rebuild document builders must stop adding video titles, media asset titles, original file names, media ids, thumbnails, streams, upload status, or binding titles to `search_text` or ES `_source`. The index may keep `has_video` and `video_count` because they are point readiness signals, not video semantic labels.

Rationale: in this product, the video resource label is known only to the teacher and has no student/product meaning. Indexing it can cause false hits that do not correspond to point learning content.

Alternative considered: keep video title in `_source` but not in mapped fields. Rejected because ES `_source` is still an indexed payload and can leak into diagnostics, hashing, rebuild diffs, and future consumers.

### Decision 7: Destructive rebuild is allowed and preferred

The implementation may add destructive migrations and rebuild commands that reset media lifecycle/index state and recreate the student video-library ES index. Existing ES documents should not be migrated in place; they should be rebuilt from PostgreSQL point content after the pure mapping and builders are in place.

Rationale: the current index contains historical document shapes and may contain video titles in `search_text` or `_source`. Clean deletion and recreation is safer than attempting a field-by-field scrub.

Alternative considered: update mapping and let future upserts overwrite old documents lazily. Rejected because stale documents could preserve video metadata for an unknown time.

## Risks / Trade-offs

- [Risk] A teacher archives a video used by many published points. -> Mitigation: require impact preview and confirmation copy listing affected points and student visibility impact.
- [Risk] Archive succeeds but binding cleanup or ES job queueing fails. -> Mitigation: perform DB updates in one transaction where practical; otherwise keep lifecycle events retryable and diagnostics visible.
- [Risk] ES rebuild temporarily removes search results. -> Mitigation: document maintenance sequencing, recreate the index from PostgreSQL, and expose failed/pending sync state.
- [Risk] Existing tests or docs assume video titles are searchable. -> Mitigation: update specs and tests to assert video titles do not appear in `search_text` or ES `_source`.
- [Risk] Archived media records accumulate files. -> Mitigation: keep physical cleanup in the media lifecycle maintenance path and require policy checks before deleting DB-backed asset files.
- [Risk] Removing `videos` from ES `_source` surprises UI code. -> Mitigation: student search result cards should use point title/snippet/path and route to detail; point detail fetches current videos from PostgreSQL.

## Migration Plan

1. Add media asset lifecycle columns and lifecycle event/outbox storage. Existing rows default to active.
2. Add or update destructive migration/rebuild support to remove old video-resource semantic fields from index mappings and documents.
3. Add archive impact query logic that counts both catalog point media bindings and any retained legacy generic media bindings.
4. Add asset archive command that marks the asset archived, writes a lifecycle event, and invokes or queues catalog cleanup.
5. Add catalog event handler that archives non-archived point video bindings, records reason metadata, updates point readiness, marks evidence stale, and queues ES delete/upsert jobs according to point visibility.
6. Update media list and picker read models to hide archived assets by default while optionally allowing an archived filter for audit.
7. Update student and preview media file access to reject archived media assets.
8. Update ES document builders and mapping to remove video-resource semantic fields while preserving `has_video` and `video_count`.
9. Recreate the student video-library ES index and run validators that scan output documents for forbidden video fields and forbidden video-title leakage.
10. Update documentation and production readiness validation.

Rollback:

- Before applying destructive migration/rebuild, back up PostgreSQL and `data/media`.
- Code rollback can stop using archive endpoints, but archived lifecycle rows should remain auditable.
- ES rollback is rebuild-based: recreate the index from the previous code if needed.
- Physical media files are not deleted by the archive workflow, so restoring an archived resource can be implemented by changing lifecycle status back to active and rebinding if product policy permits.

## Open Questions

- Should archived assets be restorable from the teacher UI or only by operator tooling?
- Should archive confirmation require typing the video title when the asset is bound to many published points?
- Should archived assets remain visible in the duplicate-candidate review surface, or should duplicate review ignore them by default?
- Should ES `has_video` remain in the mapping if there is no current UI filter for it, or only in diagnostics?
