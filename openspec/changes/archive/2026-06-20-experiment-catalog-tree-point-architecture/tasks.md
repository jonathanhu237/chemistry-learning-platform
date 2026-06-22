## 1. Baseline and Safety Checks

- [x] 1.1 Confirm `main` is clean and the current Docker multi-service deployment is healthy before starting implementation.
- [x] 1.2 Run the current production readiness validation once to capture the pre-refactor baseline.
- [x] 1.3 Review existing experiment, point, media, question, assistant, assessment, analytics, feedback, and video-library tables for all `(experiment_id, point_key)` usages.
- [x] 1.4 Document old-to-new identity mapping assumptions in implementation notes before writing migrations.
- [x] 1.5 Identify current admin and student routes that must be removed rather than kept as compatibility paths.
- [x] 1.6 Confirm ES/IK service remains required by compose and production readiness validation.

## 2. Database Catalog Tree Model

- [x] 2.1 Add a migration for `experiment_catalog_nodes` with stable id, chapter id, parent id, node kind, title, summary, status, display order, shortcut target, metadata, and timestamps.
- [x] 2.2 Add database constraints that prevent invalid node kinds and require valid titles.
- [x] 2.3 Add indexes for chapter roots, parent children, status, display order, shortcut target, and updated time.
- [x] 2.4 Add a migration for point learning content keyed by point-capable catalog node id, including explicit student-facing knowledge fields and a separate teacher-only note field.
- [x] 2.5 Add a migration for point-node media bindings keyed by catalog node id and media asset id.
- [x] 2.6 Add a migration for point-node related links keyed by source and target point node ids.
- [x] 2.7 Add a migration for point-node search index state keyed by catalog node id.
- [x] 2.8 Add a migration for legacy identity mapping from `(experiment_id, point_key)` and formal experiment ids to catalog node ids.
- [x] 2.9 Add acyclic parent validation at the database or service layer for move operations.
- [x] 2.10 Add shortcut validation so shortcut nodes cannot create shortcut loops.

## 3. Data Migration and Seed Backfill

- [x] 3.1 Backfill former formal experiments into chapter catalog directory or hybrid nodes.
- [x] 3.2 Backfill former experiment video points into point nodes under migrated parent nodes.
- [x] 3.3 Backfill existing point learning content into point-node learning content records and leave teacher-only notes empty unless existing trusted metadata can be safely mapped.
- [x] 3.4 Backfill existing experiment point related links into point-node related links.
- [x] 3.5 Backfill existing media bindings into point-node media bindings where legacy point metadata resolves.
- [x] 3.6 Backfill legacy video candidates into point nodes or draft child nodes according to migration rules.
- [x] 3.7 Backfill question metadata primary point keys into point node ids using the legacy identity map.
- [x] 3.8 Backfill assistant reviewed evidence references into point node ids while preserving source chunk ids.
- [x] 3.9 Backfill assessment attempt/session metadata to include point node ids where legacy point context exists.
- [x] 3.10 Backfill analytics and feedback metadata to include point node ids where legacy point context exists.
- [x] 3.11 Add migration tests for deterministic old-to-new identity mapping.
- [x] 3.12 Add migration tests for migrated point content, media, related links, and questions.

## 4. Backend Catalog Domain

- [x] 4.1 Create a backend catalog-tree domain module for node read/write operations.
- [x] 4.2 Implement list chapter roots and list node children services.
- [x] 4.3 Implement get node detail with breadcrumbs/path context.
- [x] 4.4 Implement create sibling, create child, create point, create hybrid, and create shortcut services.
- [x] 4.5 Implement rename and metadata update service.
- [x] 4.6 Implement reorder siblings service.
- [x] 4.7 Implement move node service with cycle prevention.
- [x] 4.8 Implement archive, restore, publish, and unpublish services.
- [x] 4.9 Implement subtree validation service for teacher publication checks.
- [x] 4.10 Implement point content save and publication services keyed by node id, including point title, teacher-only note, principle mode, equation/text, phenomenon explanation, safety note, related links, and video binding state.
- [x] 4.11 Implement point media bind, upload-and-bind, publish, unpublish, and delete-reference services keyed by node id.
- [x] 4.12 Implement related-link defaults and manual override services keyed by node id.
- [x] 4.13 Implement catalog search/filter service for teacher tree search.
- [x] 4.14 Remove domain writes that make `formal_experiments` or `experiment_video_points` authoritative after migration.

## 5. Backend Admin APIs

- [x] 5.1 Add admin API schemas for catalog nodes, node editor payloads, point content, teacher-only note, media bindings, related links, validation, and search diagnostics.
- [x] 5.2 Add admin API endpoints for chapter catalog root and child node reads.
- [x] 5.3 Add admin API endpoints for node create, update, rename, move, reorder, archive, restore, publish, and unpublish.
- [x] 5.4 Add admin API endpoints for point content save and publication.
- [x] 5.5 Add admin API endpoints for point-node media upload, existing media binding, publication, unpublication, and reference deletion.
- [x] 5.6 Add admin API endpoints for related-link read and replace.
- [x] 5.7 Add admin API endpoints for tree search and selected-node validation.
- [x] 5.8 Add admin API endpoint or response fields for search index state and preview.
- [x] 5.9 Remove or disable old admin experiment video-point write endpoints.
- [x] 5.10 Update admin router ownership tests for the new catalog endpoints.

## 6. Backend Student APIs

- [x] 6.1 Add student API schemas for chapter catalog root responses, directory node responses, point detail responses, breadcrumbs, and node cards.
- [x] 6.2 Replace student experiment group API usage with chapter catalog API usage.
- [x] 6.3 Replace student experiment detail API usage with point-node detail API usage.
- [x] 6.4 Ensure student APIs expose only published and class-visible catalog nodes and resources.
- [x] 6.5 Ensure point detail returns principle mode, equation or text, phenomenon explanation, safety note, videos, related links, and assessment context.
- [x] 6.6 Ensure student point APIs exclude teacher-only notes, draft-only metadata, raw source chunks, and evidence payloads.
- [x] 6.7 Ensure shortcut openings preserve source path while resolving canonical point content.
- [x] 6.8 Ensure no-video point details return a graceful no-video payload.
- [x] 6.9 Remove old student `/experiment-groups/{parent_code}` and `/experiments/{experiment_id}` dependencies from app code and tests.

## 7. Search, ES, and Index Events

- [x] 7.1 Replace video-library document builders with point-node document builders.
- [x] 7.2 Include chapter path, catalog path, point title, aliases, principle, phenomenon explanation, safety note, student-facing related text, formulae, reaction features, and published video metadata in point-node documents.
- [x] 7.3 Exclude raw teacher media assets from student search unless bound to published point nodes.
- [x] 7.4 Exclude teacher-only notes, raw AI source chunks, and `experiment_video_point_evidence` payloads from student search documents.
- [x] 7.5 Queue index upserts on node title, path, student-facing point knowledge, publication, related-link, and media-binding changes.
- [x] 7.6 Queue index deletes or disables on point unpublish/archive.
- [x] 7.7 Update ES document ids to use point node ids.
- [x] 7.8 Update ES diagnostics to report point-node index state and analyzer asset versions.
- [x] 7.9 Add or replace ES/IK dictionary assets for Harbin Institute of Technology stopwords, project chemistry stopwords, chemistry custom terms, and chemistry synonyms.
- [x] 7.10 Update the ES/IK Docker image or compose mounts so the dictionary assets are available inside the analyzer runtime.
- [x] 7.11 Update ES index mappings/settings so chemistry text fields use the IK analyzer plus stopword and synonym filtering where ES/IK supports it.
- [x] 7.12 Preserve Python-side formula/alias/query normalization as supplemental enrichment, not as the only synonym mechanism.
- [x] 7.13 Update production readiness validation to verify ES/IK, analyzer asset presence, analyzer behavior, and point-node indexing readiness.
- [x] 7.14 Add backend tests for search documents, raw media exclusion, teacher-note exclusion, and AI-evidence exclusion.
- [x] 7.15 Add analyzer smoke tests for formula/name aliases, Chinese/English reagent aliases, ion notation, and chemistry stopword filtering.

## 8. Questions, Assistant, Assessment, Analytics, and Feedback

- [x] 8.1 Update question bank schemas and services to store point node ids for primary point bindings.
- [x] 8.2 Update option-level diagnostic links to store point node ids.
- [x] 8.3 Update point-aware question generation/review flows to resolve catalog point nodes.
- [x] 8.4 Update AI assistant context payloads to accept point node id and source path context.
- [x] 8.5 Keep AI-generated evidence chunks separate from student search documents while linking them to point nodes.
- [x] 8.6 Preserve workbench source roles so teacher point content remains `student_page_context_only` and accepted evidence remains `experiment_video_point_evidence` plus canonical/RAG source refs.
- [x] 8.7 Add tests proving point content edits do not automatically rewrite accepted question evidence bindings.
- [x] 8.8 Update assessment session creation to include point node id and chapter context.
- [x] 8.9 Update assessment reports to resolve point titles from catalog nodes.
- [x] 8.10 Update analytics read models to aggregate weak points by point node id.
- [x] 8.11 Update feedback context capture to include point node id and catalog path where available.
- [x] 8.12 Add tests for migrated question, assistant, assessment, analytics, and feedback point contexts.

## 9. Admin Frontend API and State

- [x] 9.1 Add admin catalog API client module(s) for tree, nodes, point content, media, related links, publication, validation, and search diagnostics.
- [x] 9.2 Remove admin feature imports of old experiment video-point write APIs.
- [x] 9.3 Add React Query hooks for chapter catalog tree, selected node, children, validation, media assets, and index state.
- [x] 9.4 Add mutations for create, update, rename, move, reorder, archive, restore, publish, and unpublish.
- [x] 9.5 Add mutations for point content, video binding, media publication, related links, and search reindex actions where supported.
- [x] 9.6 Add pure mappers for node editor form hydration and request payloads.
- [x] 9.7 Add unit tests for admin catalog mappers and tree helpers.

## 10. Admin Frontend Tree Editor

- [x] 10.1 Replace the current experiment-first route content with the catalog tree workspace.
- [x] 10.2 Build chapter selector and tree toolbar with search, add root, refresh, and validation summary.
- [x] 10.3 Build collapsible tree rendering with node kind, status, validation, media, and index badges.
- [x] 10.4 Build node selection and focus behavior for search results.
- [x] 10.5 Build add sibling, add child, add point, add hybrid, and add shortcut actions.
- [x] 10.6 Build rename action with inline or modal editing.
- [x] 10.7 Build reorder and move behavior with validation and persisted order.
- [x] 10.8 Build archive/restore confirmation behavior.
- [x] 10.9 Build right-side basics editor for directory and shared node fields.
- [x] 10.10 Build point content editor for point title, teacher-only note, principle mode, equation/text, phenomenon explanation, safety note, and draft save.
- [x] 10.11 Make the teacher-only note visibly separate from student-facing point knowledge and label it as hidden from students/search.
- [x] 10.12 Build related-link editor using point node targets.
- [x] 10.13 Build video binding panel using point node media bindings.
- [x] 10.14 Build search preview and index state panel that previews only student-facing indexed content.
- [x] 10.15 Build publication and subtree validation panel.
- [x] 10.16 Ensure the workspace remains feature-modular and does not become a monolithic page.

## 11. Student Frontend API and Routes

- [x] 11.1 Add student catalog API client functions for chapter roots, directory detail, and point detail.
- [x] 11.2 Update student API types for catalog nodes, breadcrumbs, point detail, videos, related links, and assessment context.
- [x] 11.3 Add TanStack routes for chapter catalog directory nodes.
- [x] 11.4 Replace point route params from experiment id to stable point node id.
- [x] 11.5 Preserve source-aware route search context for chapter, directory, shortcut, search, and related-point openings.
- [x] 11.6 Remove student frontend dependency on legacy experiment group and experiment detail APIs.
- [x] 11.7 Update route navigation helpers for catalog nodes and point nodes.
- [x] 11.8 Update route tests for direct catalog URL, direct point URL, invalid node, and back behavior.

## 12. Student Frontend Prototype Flow

- [x] 12.1 Update periodic-table/chapter entry to navigate into standalone chapter catalog page.
- [x] 12.2 Build chapter page content aligned with the prototype: selected chapter context and top-level catalog entries.
- [x] 12.3 Build reusable recursive catalog directory page for any node depth.
- [x] 12.4 Build mobile breadcrumbs or equivalent path context for nested directory pages.
- [x] 12.5 Build node cards for directory, point, hybrid, and shortcut actions.
- [x] 12.6 Update point detail page to fetch by point node id.
- [x] 12.7 Update point detail page to display video, principle, phenomenon explanation, safety note, related links, and fixed test handoff.
- [x] 12.8 Verify point detail page never renders teacher-only note.
- [x] 12.9 Render graceful empty video state for published points without video.
- [x] 12.10 Preserve assistant context handoff using point node id.
- [x] 12.11 Preserve assessment handoff using point node id.
- [x] 12.12 Keep mobile-first layout without horizontal scrolling at 360, 390, and 430 CSS-pixel widths.

## 13. Cleanup of Legacy Contracts

- [x] 13.1 Remove retired backend write paths for experiment video-point content and media binding.
- [x] 13.2 Remove retired admin API client functions and types for experiment video-point writes.
- [x] 13.3 Remove retired student API client functions and types for experiment groups and experiment detail.
- [x] 13.4 Remove or rewrite tests that assert fixed chapter -> experiment -> point hierarchy.
- [x] 13.5 Remove compatibility barrels or aliases that preserve legacy point APIs.
- [x] 13.6 Update docs to describe chapter catalog tree architecture and teacher authoring workflow.
- [x] 13.7 Update README or deployment notes only if commands or required services change.

## 14. Verification

- [x] 14.1 Run `openspec validate experiment-catalog-tree-point-architecture --strict`.
- [x] 14.2 Run backend unit/integration tests.
- [x] 14.3 Run admin import boundary validation.
- [x] 14.4 Run admin typecheck.
- [x] 14.5 Run admin tests.
- [x] 14.6 Run admin build and build report.
- [x] 14.7 Run admin E2E smoke covering the catalog editor.
- [x] 14.8 Run student typecheck.
- [x] 14.9 Run student tests and E2E tests.
- [x] 14.10 Run student build.
- [x] 14.11 Run student mobile viewport QA at 360x780, 390x844, and 430x932.
- [x] 14.12 Rebuild and start the Docker Compose application stack including backend, admin, student, ES/IK, and workers.
- [x] 14.13 Verify ES/IK readiness, HIT stopwords, chemistry custom dictionary, chemistry synonym dictionary, and point-node search indexing inside the running stack.
- [x] 14.14 Verify student search results are driven by point title plus point knowledge and exclude teacher-only notes, raw media-library-only uploads, `source_chunks`, and `experiment_video_point_evidence`.
- [x] 14.15 Run full production readiness validation with compose smoke and E2E.
- [x] 14.16 Run `git diff --check`.
- [x] 14.17 Confirm no live code references old student/admin experiment point APIs as authoritative write paths.
