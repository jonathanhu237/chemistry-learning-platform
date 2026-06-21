## 1. Discovery And Migration Inventory

- [x] 1.1 Inventory every database table, migration, backend service, frontend type, seed script, ES document, and test that treats `experiment_catalog_nodes.id`, `node_id`, or `point_node_id` as the sole point identity.
- [x] 1.2 Produce a current duplicate-placement report for outline leaves, including exact duplicate-title groups, candidate canonical groups, chapter/path examples, and ambiguous groups requiring product review.
- [x] 1.3 Identify all existing point-resource tables that must move to canonical point identity, including content, reaction equations, media bindings, related links, evidence state/bindings, question references, assessment context, analytics, feedback, and search index state.
- [x] 1.4 Define the migration compatibility field names and API bridge policy for old `node_id`, `canonical_node_id`, and `source_node_id` fields versus new `placement_node_id` and `canonical_point_id`.
- [x] 1.5 Add a reviewed grouping fixture or mapping file for known duplicate experiment leaves, including `Na2SiO3 + CO2`, `Al2(SO4)3 + NH3·H2O + NaOH`, and `BeSO4 + NH3·H2O + NaOH`.
- [x] 1.6 Verify the grouping fixture keeps `NaClO + MnSO4` and `NaClO + 品红溶液` as distinct canonical experiments and sibling placements.

## 2. Database Model And Migrations

- [x] 2.1 Add canonical experiment point storage with stable id, title/summary/lifecycle fields, audit metadata, and timestamps.
- [x] 2.2 Add a point-placement target reference from point catalog nodes to canonical experiment points while keeping directory nodes targetless.
- [x] 2.3 Add database constraints so point placements target exactly one canonical point and directories cannot target canonical points.
- [x] 2.4 Add uniqueness or guard constraints preventing duplicate active placements of the same canonical point under the same parent unless explicitly allowed.
- [x] 2.5 Migrate singleton point nodes into one canonical point plus one placement.
- [x] 2.6 Migrate reviewed duplicate point groups into one canonical point plus multiple placements.
- [x] 2.7 Create migration audit storage recording old node id, placement node id, canonical point id, grouping decision, and conflict status.
- [x] 2.8 Add conflict detection for grouped point content, videos, evidence, question references, publication state, and placement metadata.
- [x] 2.9 Migrate point content and reaction equations from placement/node identity to canonical point identity.
- [x] 2.10 Migrate media bindings from placement/node identity to canonical point identity.
- [x] 2.11 Migrate related links to canonical source and target point identity with placement display resolution metadata where needed.
- [x] 2.12 Migrate evidence state and evidence bindings to canonical point identity while preserving canonical RAG chunks and embeddings.
- [x] 2.13 Migrate question-bank, assessment, analytics, feedback, and search-state point references to canonical point identity with source placement context where available.
- [x] 2.14 Add rollback-safe archival behavior so migrations preserve mapping/audit rows and avoid hard-deleting point resources.

## 3. Backend Catalog Domain

- [x] 3.1 Add canonical point lookup, creation, update, archive, and active-placement-count helpers in the catalog domain.
- [x] 3.2 Update node creation so creating a new point creates both a canonical point and first placement.
- [x] 3.3 Add reuse creation so adding an existing experiment creates a new placement targeting an existing canonical point.
- [x] 3.4 Update node move/reorder/status flows to operate on placements without changing canonical point identity.
- [x] 3.5 Add final-placement removal guards requiring explicit canonical archive confirmation.
- [x] 3.6 Update node detail read models to include placement id, canonical point id, active placement count, and placement list for authorized teacher/admin callers.
- [x] 3.7 Update point content save/publish flows to resolve placement ids to canonical point ids before writing shared content.
- [x] 3.8 Update publication validation to distinguish placement availability errors from canonical point content errors.
- [x] 3.9 Update related-link read/write flows to store canonical target ids and resolve student display placements at read time.
- [x] 3.10 Update backend validation to reject `shortcut`, `reference`, `hybrid`, and unsupported node kinds as live catalog node types.

## 4. Media, Evidence, Questions, And Assessment

- [x] 4.1 Update media binding APIs and services to bind videos to canonical experiment points and display them through every published placement.
- [x] 4.2 Update evidence refresh jobs so placement-triggered refresh resolves to canonical point identity.
- [x] 4.3 Update evidence state/bindings validation to reject placement-only rows after migration.
- [x] 4.4 Update question-bank point binding code to store canonical point ids and optional source placement context.
- [x] 4.5 Update point-aware question detail and option diagnostic links to render canonical point titles and placement context.
- [x] 4.6 Update assessment context to use canonical point id for learning identity and placement id/path for route context.
- [x] 4.7 Update analytics and feedback references so historical records remain readable after placement removal.
- [x] 4.8 Add migration validation that removed placements do not orphan canonical point resources or question/evidence references.

## 5. Student APIs And Search

- [x] 5.1 Update student chapter and directory catalog APIs so point cards represent placements and carry route-safe placement ids.
- [x] 5.2 Update student point detail API to resolve placement id to canonical content, videos, related points, and assessment context.
- [x] 5.3 Add controlled unavailable responses for missing, archived, unpublished, or path-unavailable placements and archived canonical points.
- [x] 5.4 Update response schemas to include explicit `placement_node_id` and `canonical_point_id` while bridging existing fields during migration.
- [x] 5.5 Rework video-library search document construction to create one document per published placement.
- [x] 5.6 Ensure canonical content/video changes enqueue search upserts for all active published placements.
- [x] 5.7 Ensure placement path/publication/status changes enqueue only that placement's search update or delete.
- [x] 5.8 Update ES source fields and route targets to include placement id, canonical point id, chapter/path context, and canonical content.
- [x] 5.9 Add local-search and ES-search fallback behavior for placement document ids.

## 6. Teacher Frontend

- [x] 6.1 Update catalog tree types so point rows are placement entries targeting canonical experiment points.
- [x] 6.2 Add "create new experiment" flow that creates a canonical point and first placement.
- [x] 6.3 Add "reuse/add to directory" flow for searching existing canonical experiments and creating synchronized placements.
- [x] 6.4 Add UI copy that avoids internal "reference node" language and explains synchronized reuse in teacher-readable terms.
- [x] 6.5 Show reuse count and placement locations when editing an experiment with multiple placements.
- [x] 6.6 Show a shared-content warning before editing canonical point fields from any reused placement.
- [x] 6.7 Label placement-local fields separately from shared canonical fields.
- [x] 6.8 Add placement removal behavior that removes only the selected location when other placements remain.
- [x] 6.9 Add final-placement removal confirmation or blocking UI according to the backend final archival contract.
- [x] 6.10 Update validation and search preview UI to distinguish placement issues from canonical point issues.
- [x] 6.11 Add an explicit independent-copy or fork affordance only if needed, separate from normal reuse.

## 7. Student Frontend

- [x] 7.1 Update student route params and navigation helpers to treat point routes as placement routes.
- [x] 7.2 Update point detail page state to render canonical content with source placement breadcrumbs.
- [x] 7.3 Preserve source-aware return from chapter pages, nested directory pages, search results, related links, and recent-learning entries.
- [x] 7.4 Handle wrong-id and unavailable-placement responses without crashing the authenticated shell.
- [x] 7.5 Update search result rendering to show placement path/chapter context while avoiding user-facing reference terminology.
- [x] 7.6 Update related point navigation to use backend-resolved placement route targets.

## 8. Seed And Data Tooling

- [x] 8.1 Update the catalog seed generator to emit canonical point records plus placement records from `docs/实验目录_整理版.md`.
- [x] 8.2 Preserve the full chapter directory tree and full placement path for every leaf point.
- [x] 8.3 Apply reviewed grouping rules for known duplicate leaves and keep ambiguous duplicates separate.
- [x] 8.4 Update the 30 sample content mapping so examples bind to canonical points through their selected placements.
- [x] 8.5 Add seed validation for canonical point count, placement count, duplicate grouping decisions, and placement-to-canonical integrity.
- [x] 8.6 Add smoke queries proving the same canonical experiment can be found from multiple chapter/path placements.
- [x] 8.7 Implement the corrected outline importer so it writes the full active catalog baseline after canonical point/placement schema migration.
- [x] 8.8 Run the corrected outline importer against the target development database after the architecture migration is complete.
- [x] 8.9 Verify the imported active visible catalog contains exactly 569 visible nodes: 176 directories and 393 point placements.
- [x] 8.10 Verify chapter 21 remains empty and no node, placement, canonical point, or placeholder content is created from `暂无对应实验内容`.
- [x] 8.11 Verify every active point placement targets exactly one active canonical experiment point and every non-archived imported canonical point has at least one active placement.
- [x] 8.12 Verify reviewed duplicate groups are represented as multiple placements targeting one canonical point, while ambiguous duplicate groups remain separate and reported.
- [x] 8.13 Verify the corrected hypochlorite sibling points `NaClO + MnSO4` and `NaClO + 品红溶液` remain distinct sibling placements targeting distinct canonical points.
- [x] 8.14 Verify the 30 sample content examples import to 30 unique target placements and their canonical point bindings.
- [x] 8.15 Replace or retire the old independent duplicate point seed baseline so it is no longer authoritative after the corrected import.
- [x] 8.16 Produce an import report with directory count, point placement count, total visible node count, canonical point count, duplicate grouping count, ambiguous duplicate count, and sample-content binding count.
- [x] 8.17 Rebuild or resync student video-library ES documents from the imported placement baseline.

## 9. Tests And Validation

- [x] 9.1 Add migration tests covering singleton points, reviewed duplicate groups, conflicting grouped resources, and final-placement deletion guards.
- [x] 9.2 Add backend unit tests for canonical point creation, reuse placement creation, placement movement, content editing from reused placements, and placement removal.
- [x] 9.3 Add backend API contract tests for student point detail placement resolution and teacher placement/canonical payloads.
- [x] 9.4 Add ES/search tests proving one document per published placement and shared canonical upserts across all placements.
- [x] 9.5 Add question/evidence/media tests proving shared resources bind to canonical points and not placement-only ids.
- [x] 9.6 Add frontend tests for teacher reuse flow, shared edit warning, placement list, and final-placement removal prompt.
- [x] 9.7 Add student frontend tests for placement routes, breadcrumbs, search-result navigation, and unavailable placement handling.
- [x] 9.8 Run seed/import validation and confirm the full corrected outline is active in the database with 176 directories, 393 point placements, and 569 visible nodes.
- [x] 9.9 Run `openspec validate add-catalog-point-placement-references --strict`.
- [x] 9.10 Run relevant backend test suites for catalog tree, student catalog, media bindings, search, evidence, questions, and assessment.
- [x] 9.11 Run relevant frontend checks for web-teacher and web-student.
- [x] 9.12 Run ES smoke validation against rebuilt placement documents, including duplicate-placement searches that return the same canonical experiment from multiple chapter/path contexts.

## 10. Documentation And Operational Checks

- [x] 10.1 Update catalog architecture docs to explain canonical experiment points versus catalog placements.
- [x] 10.2 Update production operations docs with migration order, validation queries, ES rebuild expectations, and rollback/audit notes.
- [x] 10.3 Document teacher-facing product language for reuse, synchronized copy, shared edit warning, and final-placement archival.
- [x] 10.4 Add developer notes for when to use canonical point id versus placement node id.
- [x] 10.5 Add architecture validation or repository search checks preventing live reintroduction of shortcut/reference node kinds.
