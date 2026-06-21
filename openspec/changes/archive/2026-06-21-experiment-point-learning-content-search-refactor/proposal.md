## Why

The current experiment point experience is still built from a mix of `formal_experiments.metadata.video_candidates`, media binding metadata, and search-time metadata assembly. That is no longer enough: the student experiment point detail page needs stable, teacher-authored learning content, and the video library search must be driven by the same published point content rather than by loose video filenames or AI/RAG evidence.

This change formalizes experiment video points as editable learning-content records, keeps AI-generated point chunk/evidence bindings as a separate assistant/RAG consumer path, and makes Elasticsearch with IK analysis a required application service for student video-library search.

## What Changes

- Add a first-class experiment point model keyed by stable `(experiment_id, point_key)` instead of treating point identity as a temporary derivation from candidate text or media metadata.
- Add teacher/admin editing for point learning content inside the experiment management workflow, not inside the generic video asset page.
- Store point learning content as human-authored data:
  - video bindings remain media resources attached to the point
  - experiment principle with exactly one primary mode: chemical equation or text description
  - phenomenon explanation
  - safety note
  - manually editable related experiment point links
  - draft/published/archive visibility states and audit fields
- Keep related links editable while defaulting to nearby points from the same parent experiment when no manual override exists.
- Keep the "go test" action as a fixed student frontend entry into the existing post-learning/assessment flow for the experiment's chapter or knowledge context; it is not an admin-editable content field.
- Refactor the student H5 experiment point/detail page so the video remains primary and the content below follows:
  - experiment principle
  - phenomenon explanation
  - safety note
  - related experiment links
  - go test
- Build a published point search projection for the student video library from teacher-authored point content and student-visible video bindings.
- Add Elasticsearch as a required application service/container for production-like operation, with IK Chinese analyzer support plus chemistry-specific normalization, synonyms, stopwords, equation parsing, and reaction feature extraction.
- Ensure admin edits and publishing changes update the student frontend payload and the ES search index.
- Preserve the existing AI-generated/manual-reviewed point chunk evidence path for assistant/RAG and diagnostics only; it must not become student page body copy or the source of published point content.

## Capabilities

### New Capabilities

- `experiment-point-learning-content`: First-class experiment point identity, teacher-authored point learning content, admin editing, publishing, related links, student point detail display, and the strict boundary from AI/RAG evidence.
- `experiment-video-search-indexing`: Elasticsearch/IK-backed video-library search projection generated from published point learning content and student-visible video resources, including chemistry normalization and update synchronization.

### Modified Capabilities

- `experiment-centered-course-management`: Experiment management must include point-level editing and publishing rather than only experiment metadata and video resource binding.
- `student-h5-learning-experience`: The experiment point/detail page must render the new structured learning content and fixed test entry.
- `student-h5-learning-flow`: The point detail "go test" action must continue using the existing assessment handoff for the point's experiment/chapter context.
- `point-context-learning-assistant`: The existing AI point evidence package remains a separate consumer path for assistant/RAG and must be explicitly distinguished from teacher-authored point content.
- `production-readiness-governance`: Elasticsearch with IK analyzer support becomes part of the required application deployment/validation surface for video-library search.

## Impact

- Backend database migrations for stable experiment video points, point learning content, related links, publication metadata, and search indexing state.
- Backend admin APIs for listing points, editing point content, publishing/unpublishing content, editing related links, and triggering/indexing published point search documents.
- Backend student APIs for point detail content and video-library search results.
- Backend search infrastructure for ES/IK mapping, chemical dictionary or synonym configuration, stopword configuration, equation parsing, index upsert/delete, and health checks.
- Admin frontend experiment detail workspace gains a point editor surface with validation and publish controls.
- Student H5 experiment point/detail page gains the new structured content layout and related-link navigation.
- Student H5 video library search becomes dependent on published point-content search documents, while local fallback remains only a development/test safety net where explicitly allowed.
- Docker/deployment, environment documentation, readiness checks, and tests must cover ES container availability and index behavior.
- Existing AI-generated/manual-reviewed point evidence files, `experiment_video_point_evidence`, `source_chunks`, and assistant diagnostics remain protected and continue serving AI/RAG consumers without being overwritten by this content model.
