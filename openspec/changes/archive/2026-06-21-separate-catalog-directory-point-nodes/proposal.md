## Why

The catalog tree implementation currently treats nodes as flexible directory, point, hybrid, or shortcut objects, but the updated product model requires a stricter split between navigation directories and video learning points. The current backend also concentrates catalog tree behavior in one large service module, making this change the right moment to correct the tree architecture rather than extending the existing mixed-concern implementation.

## What Changes

- **BREAKING** Replace catalog node kinds with exactly `directory` and `point`; remove `hybrid`, `shortcut`, shortcut target fields, shortcut route semantics, and point-capable directory behavior from API contracts, database constraints, frontend types, and specs.
- **BREAKING** Treat directory nodes as navigation/category/card nodes only: title, teacher note, student-visible description, and card presentation metadata. Directories MUST NOT own point knowledge, video bindings, related point links, assessment identity, or ES result identity.
- **BREAKING** Treat point nodes as the only stable video learning point identity. Point nodes keep point title, teacher-only note, point knowledge, video bindings, related links, assessment context, AI context handoff, and ES indexing.
- Update student search semantics so directory text contributes category/path context to descendant point documents, but directory nodes do not appear as standalone video-library search results.
- Remove video upload from the catalog node editor. The editor may bind existing media assets, unbind, and publish/unpublish bindings; new uploads remain owned by the media/video upload page.
- Add directory and point card presentation contracts. Directory cards support stronger student-facing customization; point cards support limited, consistent overrides so point lists remain visually coherent.
- Replace per-row up/down ordering controls with a professional draggable tree interaction that clearly distinguishes directory and point nodes, supports create/delete/move/reorder efficiently, and avoids cluttered always-visible action buttons.
- Refactor the catalog tree backend and admin frontend so this change does not add more behavior to the existing large tree implementation. Tree structure, directory metadata, point content, media bindings, related links, student read models, and search document building must have clear owners.

## Capabilities

### New Capabilities
- `catalog-tree-service-architecture`: Backend ownership boundaries for the catalog tree domain, including service/module split, router thinness, validation gates, and prevention of a new catalog tree monolith.

### Modified Capabilities
- `experiment-catalog-tree`: Restrict node kinds to directory and point, redefine directory/category and point/search semantics, and remove hybrid/shortcut behavior.
- `teacher-experiment-catalog-editor`: Update the teacher workspace for directory-vs-point editing, card presentation, existing-media binding only, and draggable tree interaction.
- `frontend-admin-maintainability`: Strengthen catalog editor frontend boundaries so tree interaction, node editors, card presentation, and media binding panels remain split.
- `student-h5-learning-experience`: Align student catalog pages with directory cards as navigation categories and point cards/details as the only video learning entries.
- `student-h5-route-stack-navigation`: Remove shortcut source-route behavior and retain source-aware return through normal directory paths, search results, and related point links.
- `student-web-frontend-maintainability`: Keep recursive catalog UI reusable while removing hybrid/shortcut client assumptions and preserving route/page ownership.

## Impact

- Database and migrations: `experiment_catalog_nodes.node_kind` constraints, shortcut columns/indexes, directory metadata/card presentation fields, and migration normalization for any existing `hybrid` or `shortcut` records.
- Backend API/schema/domain: `server/app/catalog_tree_schemas.py`, `server/app/api/admin/admin_catalog_tree.py`, `server/app/api/student/student_catalog.py`, `server/app/domains/catalog_tree/*`, video-library search document generation, production validation scripts, and tests.
- Admin frontend: `apps/admin-web/src/api/catalogTree.ts`, catalog tree workspace, tree list interaction, selected-node editor modules, media binding UI, card presentation forms, CSS, and boundary tests.
- Student frontend: catalog API types, catalog node cards, directory pages, point detail route behavior, video-library search result handling, and mobile QA.
- Dependencies: likely add one mature tree/drag dependency for the admin tree, favoring an Ant Design-compatible approach or `react-arborist` after implementation spike.
- Validation: OpenSpec strict validation, backend architecture validation, backend tests, admin typecheck/tests/build/boundary checks, student typecheck/e2e/build/mobile QA, ES/IK smoke, and production readiness.
