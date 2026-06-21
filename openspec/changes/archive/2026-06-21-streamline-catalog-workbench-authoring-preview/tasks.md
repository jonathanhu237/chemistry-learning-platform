## 1. Contract Audit

- [x] 1.1 Inventory every backend reference to `student_description`, `card_image_asset_id`, `card_icon_key`, `card_accent`, `card_layout`, `card_presentation`, and `point_card_presentation`.
- [x] 1.2 Inventory every teacher frontend reference to student-card form values, `CatalogStudentCardPanel`, and `student-card` tab keys.
- [x] 1.3 Inventory every student frontend reference to removed card fields and identify derived replacements.
- [x] 1.4 Inventory tests and fixtures that currently assert manual card fields or card override behavior.
- [x] 1.5 Confirm whether the current migration system supports irreversible column drops and document the rollback assumption as database backup restore.

## 2. Backend Data Model Removal

- [x] 2.1 Add an irreversible migration that drops obsolete manual student-card columns from catalog node storage.
- [x] 2.2 Remove removed card fields from catalog create/update Pydantic schemas.
- [x] 2.3 Remove removed card fields from catalog node response schemas and serialization helpers.
- [x] 2.4 Remove removed card fields from directory/node normalization helpers and payload builders.
- [x] 2.5 Remove removed card fields from catalog node create, update, copy, seed, and import SQL paths.
- [x] 2.6 Remove removed card fields from common catalog node select/read-model projections.
- [x] 2.7 Remove removed card fields from student catalog read models.
- [x] 2.8 Remove removed card fields from video-library search document builders.
- [x] 2.9 Remove removed card fields from ES/search indexing document builders.
- [x] 2.10 Ensure stale payload fields are rejected, ignored, or stripped consistently according to the existing API validation style.
- [x] 2.11 Update backend contract tests that currently assert card field normalization.
- [x] 2.12 Add migration/schema tests verifying removed fields are no longer present in live catalog node contracts.

## 3. Derived Student Catalog Cards

- [x] 3.1 Define derived directory card display rules using directory title, child availability, descendant count where available, and stable default visual treatment.
- [x] 3.2 Define derived point card display rules using point title, point learning summary where available, binary video presence, and bound video thumbnail where available.
- [x] 3.3 Update backend student catalog payloads so directory and point cards contain only remaining authoritative fields.
- [x] 3.4 Update `CatalogNodeCards` in `web-student` to render without removed fields.
- [x] 3.5 Replace point-card short description usage with a derived content summary or empty fallback.
- [x] 3.6 Replace card icon/accent/layout usage with stable defaults in the student frontend.
- [x] 3.7 Add student frontend tests for directory cards, point cards with summary/video thumbnail, and point cards with missing summary/video.
- [x] 3.8 Verify student catalog pages still render on phone widths without horizontal overflow after card derivation.

## 4. Teacher Preview Backend

- [x] 4.1 Add a teacher-authorized endpoint to create a short-lived preview token for a selected catalog point node.
- [x] 4.2 Scope preview tokens to teacher identity, node id, preview purpose, and expiry.
- [x] 4.3 Add a preview point-detail read endpoint that returns a `StudentPointDetailResponse`-compatible payload for the scoped point.
- [x] 4.4 Ensure preview detail can render valid draft, unpublished, missing-content, and missing-video points for teacher inspection.
- [x] 4.5 Add preview media stream/thumbnail access that accepts only a valid preview token for the scoped point.
- [x] 4.6 Ensure preview APIs do not expose teaching notes, node-status diagnostics, ES/RAG internals, evidence chunks, generated queries, or job state.
- [x] 4.7 Ensure preview APIs do not start assessments, record progress, create feedback, open AI sessions, or mutate student data.
- [x] 4.8 Add backend tests for token scope, expiry, wrong-node rejection, no-teacher-diagnostic leakage, and preview media authorization.

## 5. Student Preview Shell

- [x] 5.1 Add a preview route or shell in `web-student` that accepts a preview token without creating a normal student session.
- [x] 5.2 Add a preview API client path that uses preview token authorization instead of `chem_student_token`.
- [x] 5.3 Reuse `CatalogPointDetailPanel` or factor its rendering so preview and normal student routes share the same point-detail composition.
- [x] 5.4 Add preview-only props or context to disable finish-learning, assessment handoff, feedback, and real AI chat actions.
- [x] 5.5 Add preview media URL helper that uses preview token media endpoints.
- [x] 5.6 Add controlled unavailable states for invalid, expired, or wrong-scope preview tokens.
- [x] 5.7 Ensure the student preview route can be embedded by the teacher preview shell using the approved internal origin/frame policy.
- [x] 5.8 Add student frontend tests proving preview mode renders point detail but does not call student mutation APIs.
- [x] 5.9 Verify normal student routes still use student auth and preserve assessment, AI, feedback, and related-point behavior.

## 6. Teacher Workbench Authoring IA

- [x] 6.1 Remove `CatalogStudentCardPanel` from the teacher catalog feature.
- [x] 6.2 Remove `student-card` from directory and point editor tab key lists.
- [x] 6.3 Change directory primary tabs to only `内容`.
- [x] 6.4 Change point primary tabs to exactly `内容`, `视频`, and `相关实验`.
- [x] 6.5 Remove student-card form values from teacher frontend types, hydration, update payload builders, and tests.
- [x] 6.6 Remove visible student-card status summary cards from the selected-node header.
- [x] 6.7 Keep compact content, video, related, and node-status summary information in the header without making diagnostics a tab.
- [x] 6.8 Update directory content panel so it no longer exposes student-facing card description or card presentation fields.
- [x] 6.9 Update point content/video/related panels to remain feature-complete after student-card removal.
- [x] 6.10 Update editor-tab tests and contracts to assert the new tab sets.

## 7. Teacher Header Preview and Diagnostics

- [x] 7.1 Replace the disabled `预览学生端` header button with an enabled `预览学习卡片` action for point nodes.
- [x] 7.2 Wire `预览学习卡片` to the teacher preview-token endpoint and open a teacher preview window/shell for the selected point.
- [x] 7.3 Add `react-device-mockup` or an equivalent standard React device mockup dependency to the teacher frontend preview shell.
- [x] 7.4 Build a constrained phone preset selector outside the phone viewport, with default modern iPhone plus notched iPhone, legacy iPhone, and Android phone presets.
- [x] 7.5 Render the returned student preview URL inside the selected phone mockup screen, using explicit screen viewport dimensions for each preset.
- [x] 7.6 Ensure the teacher preview shell does not expose freeform resizing, network throttling, user-agent editing, DOM inspection, or other debugging controls.
- [x] 7.7 Disable or provide a controlled directory preview behavior when the selected node is a directory.
- [x] 7.8 Add a selected-node header `高级` or `更多` action exposing `节点状态`, `AI 上下文`, and `高级调试`.
- [x] 7.9 Add auxiliary teacher diagnostics route/window support for node status, AI context, and advanced debug panels.
- [x] 7.10 Preserve existing node-status, AI-context, and advanced panel functionality inside the secondary diagnostics surface.
- [x] 7.11 Add fallback behavior when popup/window opening is blocked.
- [x] 7.12 Add teacher frontend tests for preview action availability, phone preset switching, diagnostics menu options, and absence of diagnostics in primary tabs.

## 8. Cleanup and Regression Tests

- [x] 8.1 Remove obsolete imports, CSS, tests, fixtures, and snapshots for manual student-card editing.
- [x] 8.2 Update TypeScript API types in teacher and student apps to match backend field removal.
- [x] 8.3 Update backend tests for catalog create/update/read/search contracts after field removal.
- [x] 8.4 Run backend migration and service tests covering catalog tree, student catalog, preview auth, media preview, and search documents.
- [x] 8.5 Run teacher frontend tests and typecheck.
- [x] 8.6 Run student frontend tests and typecheck.
- [x] 8.7 Run OpenSpec strict validation for this change.
- [x] 8.8 Rebuild affected Docker services and verify backend, web-teacher, and web-student health.

## 9. Visual QA

- [x] 9.1 Capture teacher workbench desktop screenshots for selected directory and selected point after tab simplification.
- [x] 9.2 Capture teacher workbench narrow laptop screenshots to verify header actions, tabs, and tree metadata do not collide.
- [x] 9.3 Capture phone-sized preview screenshots for a complete point with video.
  - Captured `apps/web-teacher/artifacts/streamline-preview-complete-with-video-phone.png` after binding a ready video to `cat-outline-ch13-091965fc5964c79a`; the preview iframe rendered the target point with one video element.
- [x] 9.4 Capture phone-sized preview screenshots for missing-content and missing-video points.
- [x] 9.5 Capture phone mockup preview screenshots for the default modern iPhone preset and at least one alternate phone preset.
- [x] 9.6 Capture diagnostics window/surface screenshots for node status, AI context, and advanced debug panels.
- [x] 9.7 Verify preview does not expose teaching notes, raw RAG traces, validation internals, or backend job details.
- [x] 9.8 Verify preview does not trigger assessment, AI chat, feedback, or learning progress side effects.

## 10. Related Experiments Simplification

- [x] 10.1 Remove related-link short display names from teacher frontend form state, hydration, payload builders, API types, and contract tests.
- [x] 10.2 Remove related-link `label`/short-title fields in backend request schemas and replace-related-links persistence so new saves cannot create student-facing title overrides.
- [x] 10.3 Update related-link read models so teacher detail, student H5, teacher preview, search documents, video-library search, and AI context use the resolved target experiment title rather than stored labels.
- [x] 10.4 Add backend tests proving stale stored labels do not override related experiment titles in student, preview, search, and AI-context payloads.
- [x] 10.5 Replace the card-like `相关实验` editor with compact single-row related experiment items matching the catalog tree visual language.
- [x] 10.6 Make each related experiment row draggable as a whole row, with subdued source row, lightweight drag preview, and row-between drop indicator.
- [x] 10.7 Remove always-visible drag grips, `⋮⋮` handles, up/down reorder buttons, and permanent multi-button clusters from idle related experiment rows.
- [x] 10.8 Move destructive and precision/fallback reorder actions into a quiet hover action or `...` row menu without making them primary.
- [x] 10.9 Redesign related experiment search/add results as compact selectable rows with quiet `加入` / `已在列表` states.
- [x] 10.10 Update teacher frontend tests/contracts to assert absence of short-name inputs, absence of visible drag grips, absence of always-visible up/down buttons, and presence of compact row/source-tag behavior.
- [x] 10.11 Capture desktop and narrow laptop screenshots for the redesigned `相关实验` tab covering default rows, manual rows, long titles, hover/focus actions, drag/drop indicator, search results, and empty/default state.
- [x] 10.12 Run OpenSpec validation, teacher frontend tests/typecheck, relevant backend tests, and student H5 related-link regression tests after the simplification.
- [x] 10.13 Destructively drop obsolete related-link label columns from legacy and catalog database tables, and update fresh schema baselines so the columns are not recreated.
- [x] 10.14 Replace the inline related-experiment search/save workflow with a dashed add placeholder, catalog tree picker modal, and auto-save behavior for add/remove/reorder/reset.
