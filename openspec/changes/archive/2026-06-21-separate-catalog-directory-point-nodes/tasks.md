## 1. Baseline and Safety Checks

- [x] 1.1 Run `openspec validate separate-catalog-directory-point-nodes --strict` before implementation and record the initial pass.
- [x] 1.2 Capture current catalog-tree file sizes and responsibility map for `server/app/domains/catalog_tree/tree.py`, admin catalog-tree components, and student catalog components.
- [x] 1.3 Search for live `hybrid`, `shortcut`, `shortcut_target_node_id`, `POINT_CAPABLE_KINDS`, and catalog upload-and-bind references to establish the removal baseline.
- [x] 1.4 Verify the current local database or seed data shape for existing `hybrid` or `shortcut` catalog rows and document migration assumptions.

## 2. Database and Migration

- [x] 2.1 Add a migration after `020_experiment_catalog_tree.sql` that normalizes catalog node kinds to `directory` or `point`.
- [x] 2.2 Define deterministic migration behavior for existing `hybrid` rows, preserving audit metadata when a row cannot be safely collapsed.
- [x] 2.3 Define deterministic migration behavior for existing `shortcut` rows, preserving audit metadata and removing live shortcut resolution semantics.
- [x] 2.4 Tighten `experiment_catalog_nodes.node_kind` database constraints to allow only `directory` and `point`.
- [x] 2.5 Remove or retire live `shortcut_target_node_id` constraints/index assumptions from application-facing behavior.
- [x] 2.6 Add directory card presentation storage for student-visible description, image reference, icon key, accent/theme token, and layout variant.
- [x] 2.7 Add point card presentation override storage or metadata contract for cover image, short description, icon key, accent/theme token, and emphasis flag.
- [x] 2.8 Ensure point node ids remain stable and existing point content, media bindings, related links, assessments, analytics, feedback, and search state retain their node references.
- [x] 2.9 Add migration tests for node-kind normalization, directory/card fields, point identity stability, and audit metadata.

## 3. Backend Catalog Service Split

- [x] 3.1 Create catalog tree service modules for node structure, directories, points, media bindings, related links, search documents, student read models, and file resolution.
- [x] 3.2 Move node lookup/create/update/move/reorder/status and parent/cycle validation out of the catch-all tree service.
- [x] 3.3 Move directory metadata, card presentation, directory validation, and directory student-card shaping into a directory-owned module.
- [x] 3.4 Move point content, point publication validation, point card overrides, and point detail shaping into a point-owned module.
- [x] 3.5 Move existing-media binding, binding status changes, and bound-media read models into a media-binding module.
- [x] 3.6 Move manual/generated related point link behavior into a related-link module.
- [x] 3.7 Move student-visible search document construction and index queueing into a search-document module.
- [x] 3.8 Move student chapter catalog, directory detail, and point detail orchestration into a student read-model module.
- [x] 3.9 Move catalog-specific media/thumbnail file resolution into a file-resolution module if still needed by catalog routes.
- [x] 3.10 Delete or shrink `server/app/domains/catalog_tree/tree.py` so it no longer owns all catalog tree responsibilities.
- [x] 3.11 Update backend architecture validation to fail on reintroduced hybrid/shortcut live paths, catalog upload-and-bind live paths, or a recreated catalog tree catch-all module.

## 4. Backend API and Schema Semantics

- [x] 4.1 Update `server/app/catalog_tree_schemas.py` so catalog node kind schemas accept only `directory` and `point`.
- [x] 4.2 Remove shortcut target fields from live admin and student response/request schemas.
- [x] 4.3 Add directory card presentation request/response schemas.
- [x] 4.4 Add constrained point card presentation request/response schemas.
- [x] 4.5 Update admin catalog endpoints to reject point content, media bindings, related links, point publication, and search-document operations on directory nodes.
- [x] 4.6 Update admin catalog endpoints to reject child creation or node moves under point nodes.
- [x] 4.7 Update student catalog endpoints so directory routes return directory/card/children data and point routes return point/video/detail data.
- [x] 4.8 Update stale or unsupported node-kind handling to return controlled errors instead of silently treating unknown nodes as point-capable.
- [x] 4.9 Remove backend upload-and-bind endpoint behavior from catalog routes and services.

## 5. ES and Student Video-Library Search

- [x] 5.1 Update point document generation so only published point nodes create student video-library documents.
- [x] 5.2 Include ancestor directory title/description/card category text as lower-weight category/path context in descendant point documents.
- [x] 5.3 Ensure directory nodes never appear as standalone video-library search result documents.
- [x] 5.4 Ensure teacher-only directory notes and teacher-only point notes are excluded from all student search documents and snippets.
- [x] 5.5 Ensure raw media-only uploads, `source_chunks`, and `experiment_video_point_evidence` remain excluded from student ES documents.
- [x] 5.6 Update ES/IK smoke validation to cover a directory-text query returning descendant point results.
- [x] 5.7 Update video-library search tests for directory category matching, point-only result identity, and no directory standalone results.

## 6. Admin Frontend Tree Interaction

- [x] 6.1 Run a short implementation spike comparing Ant Design Tree draggable and `react-arborist` against required drag, drop, styling, virtualization, and accessibility behavior.
- [x] 6.2 Document the selected tree/drag approach and dependency trade-off in implementation notes or final task review.
- [x] 6.3 Replace always-visible per-row up/down buttons with drag-and-drop movement and a clear drop indicator.
- [x] 6.4 Add hover/focus/selected row actions for add, archive, restore, publish, and more actions without cluttering every row.
- [x] 6.5 Render directory and point rows with distinct icons, labels, hierarchy indentation, and status treatment.
- [x] 6.6 Validate drag drops in the UI so points cannot receive children and cycles/cross-chapter moves are prevented or confirmed before API calls.
- [x] 6.7 Provide an accessible fallback move/reorder action through a selected-node action or row menu.
- [x] 6.8 Preserve selection and expanded ancestor context after move/reorder refresh where practical.

## 7. Admin Frontend Editor Panels

- [x] 7.1 Update `apps/admin-web/src/api/catalogTree.ts` types and payload builders to support only directory and point nodes.
- [x] 7.2 Remove hybrid, shortcut, and shortcut target UI from create and edit forms.
- [x] 7.3 Split the selected-node editor into directory basics/card panel, point content panel, point media-binding panel, related-links panel, publication/validation panel, and search-preview panel.
- [x] 7.4 Add directory editor fields for teacher-only note, student-visible description, card image, icon, accent/theme token, and layout variant.
- [x] 7.5 Add constrained point card override fields without allowing arbitrary point-card layout changes.
- [x] 7.6 Remove local file input and upload-and-bind controls from the catalog point video panel.
- [x] 7.7 Keep existing-media selection, binding, unbinding, binding publication, and preview behavior for point nodes.
- [x] 7.8 Add a media-page navigation hint for teachers who need to upload a new video before binding.
- [x] 7.9 Update catalog editor CSS so tree rows are visually polished, directory/point distinction is clear, and text/actions do not overlap on common admin widths.
- [x] 7.10 Update catalog frontend mapper tests for directory card fields, point card overrides, node-kind restrictions, and stale unknown node handling.

## 8. Student Frontend Catalog Flow

- [x] 8.1 Update student catalog API types so live node kinds are only `directory` and `point`.
- [x] 8.2 Remove shortcut source-node assumptions and hybrid node handling from student routes, cards, and navigation helpers.
- [x] 8.3 Update directory cards to render student-visible title, description, image/icon/accent/layout presentation, and navigation affordance.
- [x] 8.4 Update point cards to render as video learning entries with distinct point styling and constrained card overrides.
- [x] 8.5 Ensure directory routes fetch durable directory detail by node id and reject or redirect point ids according to route policy.
- [x] 8.6 Ensure point routes fetch durable point detail by node id and reject or redirect directory ids according to route policy.
- [x] 8.7 Preserve source-aware return behavior through normal route/search/path context without shortcut-specific state.
- [x] 8.8 Update mobile catalog UI QA so directory cards and point cards are visually distinct and tappable at 360px, 390px, and 430px widths.

## 9. Documentation and OpenSpec Alignment

- [x] 9.1 Update `docs/catalog-tree-architecture.md` to remove hybrid/shortcut and document directory-vs-point semantics.
- [x] 9.2 Update production operations docs for catalog upload ownership and search document source rules.
- [x] 9.3 Update formal OpenSpec deltas if implementation discovers a required semantic correction.
- [x] 9.4 Search repository docs/specs for stale statements claiming catalog nodes may be hybrid or shortcut and update live docs.

## 10. Backend Tests

- [x] 10.1 Add tests that directory nodes cannot own point content, video bindings, related point links, or point publication state.
- [x] 10.2 Add tests that point nodes cannot have children.
- [x] 10.3 Add tests that hybrid/shortcut requests are rejected by backend schemas or routes.
- [x] 10.4 Add tests for directory card presentation persistence and student payload exposure without teacher notes.
- [x] 10.5 Add tests for constrained point card overrides and point detail payload behavior.
- [x] 10.6 Add tests that catalog upload-and-bind backend behavior is absent from live catalog routes.
- [x] 10.7 Add service-boundary tests for nodes, directories, points, media bindings, related links, search documents, and student read models.
- [x] 10.8 Update backend route inventory and contract tests for removed shortcut/upload catalog endpoints.

## 11. Frontend Tests

- [x] 11.1 Update admin catalog tree mapper tests for directory/point-only node types.
- [x] 11.2 Add admin catalog editor tests for directory card editing and point editor panel visibility.
- [x] 11.3 Add admin catalog video panel tests that verify upload controls are not present and existing-media binding remains available.
- [x] 11.4 Add admin tree interaction tests or smoke coverage for drag move/reorder and invalid drop feedback where practical.
- [x] 11.5 Update student E2E tests for chapter -> directory card -> nested directory -> point detail flow.
- [x] 11.6 Update student E2E tests for wrong route type handling and direct durable directory/point URLs.
- [x] 11.7 Update student mobile QA assertions for visual distinction between directory cards and point cards.

## 12. Full Validation

- [x] 12.1 Run `openspec validate separate-catalog-directory-point-nodes --strict`.
- [x] 12.2 Run `openspec validate --all --strict --no-interactive`.
- [x] 12.3 Run `git diff --check`.
- [x] 12.4 Run backend architecture validation.
- [x] 12.5 Run backend tests.
- [x] 12.6 Run admin frontend `typecheck`, `test`, `validate:boundaries`, `build`, and build-report.
- [x] 12.7 Run student frontend `typecheck`, `test:e2e`, `build`, and mobile viewport QA.
- [x] 12.8 Run ES/IK readiness and student video-library search smoke.
- [x] 12.9 Run compose smoke with backend, admin-web, student-web, postgres, elasticsearch, tusd, and video-worker.
- [x] 12.10 Run production readiness validation with compose smoke and E2E enabled.
- [x] 12.11 Confirm repository search finds no live `hybrid`, `shortcut`, `shortcut_target_node_id`, or catalog upload-and-bind implementation paths outside migration/archive/docs/test allowances.
