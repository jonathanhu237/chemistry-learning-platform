## 1. Contract and Current-State Audit

- [x] 1.1 Inventory teacher frontend video binding references to multi-select state, `bindMedia`, `changeMediaStatus`, and binding status labels.
- [x] 1.2 Inventory backend catalog video binding reads/writes that depend on `binding_status = 'published'` or allow multiple active rows.
- [x] 1.3 Inventory student, preview, search, AI context, and validation/status paths that derive visible video state from binding publication.
- [x] 1.4 Decide and document which legacy binding columns remain for compatibility in this implementation.

## 2. Backend Binding Semantics

- [x] 2.1 Add a migration that normalizes existing point media bindings to one active non-archived binding per canonical point or node fallback.
- [x] 2.2 Add a partial unique index or equivalent database guard for one active video binding per canonical point where schema permits.
- [x] 2.3 Update fresh schema baselines so new databases inherit the one-active-binding invariant.
- [x] 2.4 Remove teacher-controlled binding status from `CatalogPointMediaBindRequest` or make stale status input harmless.
- [x] 2.5 Update `bind_existing_media` to archive prior active bindings and make the selected asset active immediately.
- [x] 2.6 Update remove/delete behavior to archive the current active binding and refresh point detail.
- [x] 2.7 Keep stale publish/unpublish binding endpoint behavior compatible or explicitly unsupported without breaking current frontend routes during deployment.

## 3. Student and Read-Model Visibility

- [x] 3.1 Update catalog tree summary counts and validation to count active ready media instead of published bindings.
- [x] 3.2 Update `student_videos` and student point detail media reads to use active non-archived binding plus ready media asset.
- [x] 3.3 Update teacher preview media/detail reads to use the same active ready binding rule.
- [x] 3.4 Update catalog search documents, AI context, and video-library search paths that currently filter by binding publication.
- [x] 3.5 Update backend schemas/tests so response fields no longer expose binding publication as teacher-facing authoring state.

## 4. Teacher Frontend Data Flow

- [x] 4.1 Change video tab state from multiple selected asset ids to a single picker/open state and selected media asset identity.
- [x] 4.2 Update catalog mutations so binding one asset persists immediately and does not pass `status: "draft"`.
- [x] 4.3 Replace publish/unpublish mutation usage in the video panel with replace/remove behavior.
- [x] 4.4 Ensure video binding mutation refreshes point detail without resetting the active `视频` tab.

## 5. Teacher Frontend Video UI

- [x] 5.1 Replace the inline Ant Design multi-select with a single empty video slot when no video is bound.
- [x] 5.2 Render the current bound video as one focused row/card with thumbnail, title, file name, readiness, preview, replace, and remove.
- [x] 5.3 Add a media picker modal that lists video assets with thumbnail or placeholder, title, file name, upload/processing state, and updated metadata.
- [x] 5.4 Add search/filter behavior in the picker without hiding thumbnail and metadata context.
- [x] 5.5 Disable or clearly mark unready/failed videos as not selectable for student playback.
- [x] 5.6 Keep the video resource page shortcut visible as the upload/processing entry point.
- [x] 5.7 Remove visible `draft`, `published`, `发布`, and `取消发布` binding controls from the video tab.
- [x] 5.8 Polish responsive layout so the video slot and picker do not overflow on narrow admin viewports.

## 6. Tests and Contracts

- [x] 6.1 Add or update backend migration tests for the one-active-binding invariant and active-binding normalization.
- [x] 6.2 Add backend service tests for bind, replace, remove, stale status input, and student-visible ready media behavior.
- [x] 6.3 Update student/preview regression tests for video visibility without binding publication.
- [x] 6.4 Update teacher frontend contract tests for absence of multi-select and publish/unpublish controls, and presence of picker/slot UI.
- [x] 6.5 Add frontend mapper or component tests for picker disabled states where practical.
- [x] 6.6 Run OpenSpec validation for `simplify-catalog-video-binding`.

## 7. Verification and Deployment

- [x] 7.1 Run relevant backend tests for catalog tree migrations, service contracts, student point detail, preview media, and video-library search.
- [x] 7.2 Run teacher frontend tests, typecheck, and production build.
- [x] 7.3 Rebuild affected Docker services and verify backend, web-teacher, and dependent services health.
- [x] 7.4 Smoke-test the teacher video tab with an existing ready video: choose, preview, replace/remove, and confirm the tab stays on `视频`.
- [x] 7.5 Record any remaining follow-up such as destructive removal of legacy `binding_status`/publish metadata columns.
