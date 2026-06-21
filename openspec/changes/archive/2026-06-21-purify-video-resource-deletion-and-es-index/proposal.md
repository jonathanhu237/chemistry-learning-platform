## Why

The teacher video resource library currently has no safe delete/archive workflow for stored video assets, while catalog point bindings can already reference those assets as the single active point video. At the same time, student video-library Elasticsearch documents still allow bound video titles to enter search text even though product meaning belongs entirely to the published catalog point content, not to teacher-only video file names.

This change creates a clean asset lifecycle boundary: deleting a video resource archives the asset, emits an auditable lifecycle event, lets the catalog domain remove affected bindings, and keeps Elasticsearch as a pure published-point projection.

## What Changes

- Add an explicit media asset lifecycle state for active versus archived resources without reintroducing teacher-facing video publication state.
- Add a teacher video resource deletion/archive flow with an impact preview that lists affected point bindings before confirmation.
- Route asset archival through an event/outbox-style handoff so the media domain does not directly own catalog point binding rules.
- Archive affected catalog point video bindings when their media asset is archived, then refresh point readiness and derived ES/RAG state through existing catalog job mechanisms.
- Preserve `has_video` and `video_count` as non-semantic point readiness signals where useful.
- **BREAKING** Remove video title, original file name, media asset title, `media_id`, thumbnail paths, stream paths, and video metadata from student video-library Elasticsearch searchable text and index source.
- **BREAKING** Allow destructive database reset/rebuild of existing media lifecycle/index structures and full recreation of the student video-library Elasticsearch index to guarantee clean state.

## Capabilities

### New Capabilities

- `media-asset-lifecycle`: Defines active/archive/tombstone behavior for video resources, deletion impact analysis, event emission, and safe cleanup boundaries.
- `teacher-video-resource-library`: Defines the teacher-facing video resource library deletion/archive workflow and confirmation UX.

### Modified Capabilities

- `experiment-catalog-tree`: Catalog point video bindings react to archived media assets by archiving affected bindings without deleting point content.
- `student-h5-video-library-search`: Student video-library ES documents become point-content-only for searchable semantics and must not index video resource names or metadata.
- `catalog-point-index-evidence-jobs`: ES/RAG jobs must be triggered when media asset archival changes point video readiness, and ES may be destructively rebuilt.
- `backend-slim-domain-architecture`: Media lifecycle, catalog binding cleanup, and search projection updates must stay in separate owners connected by explicit lifecycle events/jobs.
- `production-readiness-governance`: Production validation must verify the rebuilt ES mapping and documents do not contain video-resource semantic fields.

## Impact

- Backend media asset schema and migrations for lifecycle status, archive metadata, and optional lifecycle event/outbox records.
- Admin media APIs for deletion impact preview and archive confirmation.
- Catalog point media binding service for asset-archived event handling and binding archival.
- Student video-library ES document builders, ES mapping, rebuild scripts, diagnostics, and validation scripts.
- Teacher frontend `/videos` page for impact-aware archive/delete confirmation.
- Tests for media lifecycle, catalog binding cleanup, ES document purity, destructive rebuild behavior, and route/API contracts.
