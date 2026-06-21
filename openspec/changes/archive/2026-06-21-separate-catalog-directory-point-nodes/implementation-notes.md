# Implementation Notes

## Baseline

- Initial validation: `openspec validate separate-catalog-directory-point-nodes --strict` passed before implementation.
- Current size baseline:
  - `server/app/domains/catalog_tree/tree.py`: 1368 lines; owns node CRUD, validation, point content, media binding, related links, search preview, student catalog read models, point detail, and media file resolution.
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeEditor.tsx`: 414 lines; owns node basics, point content, related links, video binding, upload-and-bind UI, move controls, and validation rendering.
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeNodeList.tsx`: 177 lines; owns recursive tree rows and always-visible up/down reorder buttons.
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx`: 208 lines; owns route workspace, search, create modal, and root controls.
  - `apps/student-web/src/api.ts`: 685 lines; owns all student API contracts including catalog types.
- Live old-semantics scan found catalog `hybrid`, `shortcut`, `shortcut_target_node_id`, `POINT_CAPABLE_KINDS`, and catalog upload-and-bind references in backend schemas/services/routes, admin catalog UI/API/mappers/tests, student catalog API/routes/cards, validation scripts, and live OpenSpec/docs.
- Local Compose database node kind distribution before migration work: `directory=76`, `point=300`, `hybrid=1`, `shortcut=0`; the single hybrid row is `cat-exp-2357c4f318ce81208c56e4d5` titled `氯、溴、碘的置换次序`, with no shortcut target rows.

## Implementation Choices

- Tree UI library spike: selected Ant Design `Tree` with `draggable` because AntD is already a production dependency, integrates with current styling and accessibility, and covers the required drag/drop and row action behavior without adding `react-arborist`. `react-arborist` remains a better fit only if the tree grows enough to require virtualization.
- Backend catalog tree split:
  - `common.py`: shared SQL row shaping, validation, breadcrumbs, parent/cycle checks.
  - `nodes.py`: node structure CRUD, move/reorder/status, admin detail/search.
  - `directories.py`: directory card and constrained point-card payload normalization.
  - `points.py`: point content and point publication.
  - `media_bindings.py`: existing-media binding and binding status changes.
  - `related_links.py`: manual and generated related point links.
  - `search_documents.py`: student-visible ES/search document construction and index queueing.
  - `student_read_models.py`: student chapter, directory, and point detail read models.
  - `files.py`: catalog-specific student media file resolution.
- Catalog upload-and-bind was removed from catalog routes, hooks, API client, and editor UI. Teachers upload in the media library and bind processed assets from the catalog point editor.
- Migration edge case: a stale `experiment_catalog_point_search_index_state` row by itself is not treated as material point ownership. A split point created only from derived search state is removed unless it also has content, media bindings, related links, legacy point identity, evidence, assessment, event, feedback, mastery, question, or posttest references.

## Final Validation

- `openspec validate separate-catalog-directory-point-nodes --strict`: passed.
- `openspec validate --all --strict --no-interactive`: 45 passed.
- Backend: architecture validation passed; `python -m pytest server/tests -q` passed with 187 tests.
- Admin frontend: `typecheck`, `test`, `validate:boundaries`, `build`, and `build:report` passed. Existing large vendor chunks remain reported for charts and Ant Design.
- Student frontend: `typecheck`, `test`, `test:e2e`, `build`, and `qa:mobile` passed. Mobile QA covered 360, 390, 430, and 1024px viewports.
- ES/IK and Compose: analyzer assets, IK smoke, video-library readiness, compose stack smoke, and production readiness with compose smoke and E2E enabled all passed.
