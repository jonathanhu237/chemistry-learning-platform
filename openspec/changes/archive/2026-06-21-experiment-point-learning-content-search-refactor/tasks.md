## 1. Data Model And Migration

- [x] 1.1 Add a migration for `experiment_video_points` keyed by `(experiment_id, point_key)` with title, display order, source, status, metadata, and timestamps.
- [x] 1.2 Add a migration for `experiment_point_learning_content` with principle mode, principle equation/text fields, phenomenon explanation, safety note, content status, publisher audit, editor audit, metadata, and timestamps.
- [x] 1.3 Add a migration for manual related point link overrides keyed by source experiment/point and target experiment/point.
- [x] 1.4 Add search index state or outbox tables needed to track point document upsert/delete status and retryable failures.
- [x] 1.5 Backfill `experiment_video_points` from existing `formal_experiments.metadata.video_candidates` using the current candidate key algorithm.
- [x] 1.6 Backfill additional point rows from existing experiment media bindings that already contain `metadata.point_key` or `metadata.point_title`.
- [x] 1.7 Preserve existing media binding point metadata for compatibility while making `experiment_video_points` the canonical point identity source.
- [x] 1.8 Add database constraints or service-level validation so published point content references an active point and a published parent experiment.
- [x] 1.9 Add validation that all current question-bank point references resolve to canonical point rows after migration.
- [x] 1.10 Add validation that all `experiment_video_point_evidence` rows resolve to canonical point rows without changing the evidence table's consumer role.
- [x] 1.11 Add migration tests or data-validation scripts for backfilled point counts, key stability, and unresolved point references.
- [x] 1.12 Update production resource validation expectations for stable experiment video points and optional published point content resources.

## 2. Backend Point Services And Admin APIs

- [x] 2.1 Create backend repository/service helpers for listing canonical points by experiment.
- [x] 2.2 Create backend repository/service helpers for reading and saving draft point learning content.
- [x] 2.3 Create backend validation for principle mode so equation and text modes are mutually exclusive as the primary principle.
- [x] 2.4 Create backend publication logic that requires principle, phenomenon explanation, and safety note before publishing.
- [x] 2.5 Create backend unpublish/archive logic that hides point content from student APIs and search while preserving audit data.
- [x] 2.6 Create backend related-link helpers that derive nearby same-parent defaults.
- [x] 2.7 Create backend related-link helpers for manual add, hide, reorder, and delete behavior.
- [x] 2.8 Add admin endpoint for fetching an experiment's point workspace data including point content, videos, related links, validation state, and index state.
- [x] 2.9 Add admin endpoint for saving point title and point learning content drafts.
- [x] 2.10 Add admin endpoint for publishing, unpublishing, and archiving point learning content.
- [x] 2.11 Add admin endpoint for editing manual related point links.
- [x] 2.12 Ensure admin point APIs enforce admin/teacher authorization and never expose student tokens or teacher-only fields to student endpoints.

## 3. Student Point Detail Backend

- [x] 3.1 Extend student point detail schemas with point identity, published principle, phenomenon explanation, safety note, related point links, video availability, and assessment context.
- [x] 3.2 Update student point detail service to resolve the requested `experiment_id` and `point_key` against canonical point rows.
- [x] 3.3 Keep PostgreSQL point learning content as the display source and avoid reading ES hit sources for point detail body content.
- [x] 3.4 Return published video resources for the selected point while preserving graceful no-video state behavior.
- [x] 3.5 Return default related links when no manual related link override exists.
- [x] 3.6 Return manually edited related links and hidden default overrides when configured.
- [x] 3.7 Return controlled unavailable or partial-content states when point content is missing, draft, archived, or not student-visible.
- [x] 3.8 Preserve existing student learning event recording for point detail opens and learning completion.
- [x] 3.9 Add backend tests for published content, missing content, hidden experiment, no-video state, and related link behavior.

## 4. Elasticsearch And IK Search Projection

- [x] 4.1 Add Elasticsearch/IK service configuration to the application stack and document required image/plugin expectations.
- [x] 4.2 Add environment settings for ES URL, index name, analyzer bootstrap mode, timeout, and production fallback policy.
- [x] 4.3 Add a search index bootstrap module that creates the video-library index with IK text analyzers and chemistry-aware normalized fields.
- [x] 4.4 Add chemistry normalization utilities for Unicode subscripts/superscripts, formula casing, charges, and common equation symbols.
- [x] 4.5 Add equation parsing utilities that extract formula chemicals while stripping coefficients, state markers, and gas/precipitate symbols.
- [x] 4.6 Add reaction feature extraction for gas generation, precipitation, heating, color/phase keywords, and other deterministic tags.
- [x] 4.7 Add a maintainable chemical alias dictionary path for important formulas and common names such as HCl/盐酸, H2O2/双氧水, and Na2S2O3/硫代硫酸钠.
- [x] 4.8 Add domain stopword configuration so high-frequency workflow words have reduced search impact.
- [x] 4.9 Build point-centered search documents from published point learning content, canonical point identity, student-visible videos, experiment metadata, chapter/profile context, and derived chemistry fields.
- [x] 4.10 Ensure search documents do not use `experiment_video_point_evidence` or `source_chunks` as student-facing body content.
- [x] 4.11 Implement point document upsert and delete operations for ES.
- [x] 4.12 Implement outbox or retryable index-status handling for failed ES updates after admin publish/edit/unpublish.
- [x] 4.13 Implement a full rebuild command that recreates the video-library index from PostgreSQL point content.
- [x] 4.14 Update video-library search service to query ES point documents and preserve typed actionable route targets.
- [x] 4.15 Keep deterministic local fallback available only for explicit local/test configuration and document that production requires ES/IK.

## 5. Admin Frontend Point Editor

- [x] 5.1 Extend admin API types for canonical points, point content, related links, validation state, publication state, and index state.
- [x] 5.2 Update experiment detail workspace to fetch the new point workspace endpoint.
- [x] 5.3 Replace or extend the current point video reference card with a point workspace card.
- [x] 5.4 Add point title editing while preserving server-controlled point keys.
- [x] 5.5 Add principle mode control with equation and text editor states.
- [x] 5.6 Add phenomenon explanation editor with validation and clear saved/draft state.
- [x] 5.7 Add safety note editor with validation and clear saved/draft state.
- [x] 5.8 Keep video binding controls inside the point workspace and preserve existing publish/unpublish/delete binding behavior.
- [x] 5.9 Add related-link editor with default nearby links, manual add, hide, reorder, and remove behavior.
- [x] 5.10 Add publish/unpublish actions with validation feedback before publishing.
- [x] 5.11 Show point completeness, content status, and search index sync status in the point list/card.
- [x] 5.12 Add filters for missing content, draft content, published content, no video, unpublished video, and search sync errors.
- [x] 5.13 Ensure the generic video resources page remains asset-focused and does not become the point content authoring surface.
- [x] 5.14 Add admin frontend tests for editing, validation, publication, related links, and video binding preservation.
- [x] 5.15 Verify admin point editor layout remains usable in the existing Ant Design drawer/workspace without nested card clutter.

## 6. Student Frontend Point Detail And Video Library UX

- [x] 6.1 Extend student API types for the new point detail content payload.
- [x] 6.2 Update point detail route/search params so point keys from video-library results and chapter point cards resolve deterministically.
- [x] 6.3 Refactor `ExperimentDetailPanel` or its route owner to render video, point context, experiment principle, phenomenon explanation, safety note, related links, go-test action, and completion action.
- [x] 6.4 Render equation-mode principles in a chemistry-friendly visual treatment without requiring the student to parse raw JSON or metadata.
- [x] 6.5 Render text-mode principles with the same section hierarchy as equation-mode principles.
- [x] 6.6 Render no-video, missing-content, draft-hidden, and error states without overlapping mobile content.
- [x] 6.7 Make related links navigate to target point detail routes while preserving source-aware route-stack return behavior.
- [x] 6.8 Wire the fixed go-test action to the existing assessment handoff for the point's experiment chapter or knowledge context.
- [x] 6.9 Ensure point detail does not display AI evidence chunks or ES snippets as body copy.
- [x] 6.10 Update video-library result rendering to reflect ES-backed point documents and route targets.
- [x] 6.11 Preserve video-library search state when returning from a point detail route where browser history allows.
- [x] 6.12 Add mobile viewport QA coverage for 360px, 390px, and 430px point detail states and video-library result navigation.

## 7. AI Evidence Boundary And Assessment Behavior

- [x] 7.1 Keep assistant point evidence loading through `experiment_video_point_evidence` and `source_chunks`.
- [x] 7.2 Ensure student point detail APIs do not join AI evidence rows into display body content.
- [x] 7.3 Ensure ES document builders do not use AI evidence chunks as principle, phenomenon explanation, or safety note body text.
- [x] 7.4 Update assistant diagnostics to distinguish teacher-authored page context, fixed manual-reviewed point evidence, and supplemental RAG evidence.
- [x] 7.5 Add tests proving published point content can exist without manual-reviewed evidence.
- [x] 7.6 Add tests proving manual-reviewed evidence can exist without published point content and still remain assistant-only.
- [x] 7.7 Verify point-aware question bank point bindings continue to resolve after point migration.
- [x] 7.8 Verify the point detail go-test action uses existing assessment/session behavior and does not introduce editable per-point test destinations.

## 8. Deployment, Documentation, And Operations

- [x] 8.1 Add ES/IK service and health check to Docker or deployment configuration used by production-like runs.
- [x] 8.2 Document search service environment variables, index bootstrap, IK analyzer expectations, stopword/synonym configuration, and rebuild commands.
- [x] 8.3 Update production operations docs to state that ES/IK is required for production video-library search.
- [x] 8.4 Update production readiness validation to fail when production search backend is missing, unhealthy, or missing required index/analyzer configuration.
- [x] 8.5 Update protected resource manifest logic for stable point records and point content resources when present.
- [x] 8.6 Keep manually reviewed point evidence listed as a separate protected resource.
- [x] 8.7 Add backup/restore notes for point content tables and search index rebuild-from-Postgres behavior.
- [x] 8.8 Add admin or CLI diagnostics for search index document counts, failed point sync rows, and last rebuild time.
- [x] 8.9 Add rollback notes for disabling the point editor or rebuilding/clearing the ES index without deleting point evidence data.
- [x] 8.10 Update developer onboarding notes for local ES startup versus explicit local fallback testing.

## 9. Verification

- [x] 9.1 Run `openspec validate experiment-point-learning-content-search-refactor --strict`.
- [x] 9.2 Add backend migration tests or validation scripts for canonical point backfill.
- [x] 9.3 Add backend service tests for point content save, validation, publish, unpublish, archive, and audit behavior.
- [x] 9.4 Add backend API tests for admin point workspace authorization and payload shape.
- [x] 9.5 Add backend API tests for student point detail visibility and missing-content states.
- [x] 9.6 Add backend tests for related link defaults and manual overrides.
- [x] 9.7 Add backend tests for chemistry formula normalization, equation extraction, alias expansion, and reaction feature extraction.
- [x] 9.8 Add backend tests for ES document builder visibility rules and no AI evidence leakage.
- [x] 9.9 Add backend tests for ES adapter query behavior and local fallback policy.
- [x] 9.10 Add admin frontend tests for point content editor workflows.
- [x] 9.11 Add student frontend tests for point detail structured sections, related links, go-test action, and no-video state.
- [x] 9.12 Add student video-library tests for ES-backed typed result routing to point detail.
- [x] 9.13 Run backend tests relevant to experiments, media bindings, student learning, student video library, assistant point context, and production resources.
- [x] 9.14 Run admin and student frontend typecheck and unit tests.
- [x] 9.15 Run student H5 build and mobile QA for point detail and video-library flows.
- [x] 9.16 Run production readiness/resource validation with ES/IK configuration documented or mocked as appropriate for the validation mode.

## 10. Production-Like Compose Stack Contract

- [x] 10.1 Update Docker Compose so the default production-like stack starts required `postgres`, `elasticsearch`, `backend`, `tusd`, and `video-worker` services as one application unit.
- [x] 10.2 Ensure the Elasticsearch service image is buildable or pullable and includes IK analyzer support for `ik_max_word`.
- [x] 10.3 Make host port bindings configurable so local host-port conflicts do not prevent required container-to-container service discovery.
- [x] 10.4 Ensure production-like backend search config disables deterministic local fallback and fails readiness when ES/IK is unhealthy or missing.
- [x] 10.5 Add a Compose stack smoke validation that starts or verifies required services, checks backend/Postgres/ES health, verifies IK analyzer behavior, applies migrations, and validates or rebuilds the video-library index.
- [x] 10.6 Document the standard deployment flow and clarify that Vite ports `5173` and `5174` are development-only, not substitutes for production-like Compose validation.
- [x] 10.7 Run the Compose stack smoke validation and record the result before marking the change complete again.
