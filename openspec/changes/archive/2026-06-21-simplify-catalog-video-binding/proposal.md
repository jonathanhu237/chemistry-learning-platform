## Why

The catalog point video tab still uses an old multi-binding workflow: teachers choose videos from a text-only dropdown, bind them as draft records, then separately publish the binding. This conflicts with the product rule that one catalog point has at most one experiment video and makes routine authoring feel like managing another publication object.

The video relationship should be a simple content reference: if the point is published and the selected video asset is ready, students can see it. Teachers should not have to understand or maintain a second video-binding publish state.

## What Changes

- Replace the text-only multi-select video binder with a single-video asset picker workflow.
- Show video candidates in a media-library style selection surface with thumbnail, title, file name, upload/processing state, and preview affordance.
- Render the selected point's current video as one focused media slot/card with preview, replace, and remove actions.
- Remove primary teacher controls for binding-level `draft` / `published` status.
- Treat a video binding as active immediately after selection, subject only to the video asset being ready and the point/node publication state.
- Enforce the one-video-per-catalog-point product model in backend write behavior and contract tests.
- **BREAKING** Stop requiring `binding_status = published` for student visibility of catalog point videos; archived/deleted bindings remain hidden, but normal bound ready videos become student-visible through point publication.
- **BREAKING** Remove or de-emphasize binding publication APIs and frontend paths for catalog point videos; stale clients should not be able to create a hidden draft binding by default.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `experiment-catalog-tree`: Catalog point media bindings become a single active video reference per canonical point, without teacher-facing binding publication semantics.
- `teacher-experiment-catalog-editor`: The video tab becomes a single-video media picker and selected-video slot instead of a multi-select binding list with publish/unpublish controls.
- `student-h5-learning-experience`: Student and preview video visibility uses point publication plus ready media asset plus active binding, not a separate binding publish state.

## Impact

- Backend schemas and domain services for catalog point media binding.
- Database migrations and fresh schema baselines for enforcing or normalizing a single active binding.
- Student/preview media read models and media authorization filters.
- Teacher frontend API types, catalog video panel UI, mutation hooks, and contract tests.
- Search, AI context, video library, and validation/status counts that currently distinguish binding `draft` and `published`.
- Dockerized teacher frontend rebuild and targeted backend/frontend regression tests.
