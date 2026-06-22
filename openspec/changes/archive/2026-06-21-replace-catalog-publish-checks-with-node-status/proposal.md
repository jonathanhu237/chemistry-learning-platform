## Why

The catalog point workbench currently compresses too many unrelated states into "publish checks" and a single warning marker in the tree. Teachers need a lightweight directory tree that still makes the right nodes actionable, while ES indexing and AI/RAG evidence remain clearly treated as asynchronous downstream consumption instead of core point readiness.

## What Changes

- Replace the teacher-facing `发布检查` concept with `节点状态`.
- Define a node status model that separates:
  - core point readiness: three learning fields plus exactly one experiment video presence;
  - publication visibility: placement/node visibility and shared point content visibility;
  - derived async consumption: ES/search and AI/RAG outbox state.
- Keep the catalog tree visually lightweight by showing at most one primary node status signal per row, plus simple directory aggregation.
- Move detailed status explanation, repair guidance, and async diagnostics into the selected-node status panel and advanced/sync diagnostics surfaces.
- Treat experiment video status as binary `有视频 / 无视频` for the teacher product model, not as a multi-video count.
- Preserve existing canonical point / placement context: placement nodes own catalog path and visibility; shared canonical points own content, video, AI evidence, and learning identity.
- Update copy, labels, and validation grouping so teachers see actionable Chinese product language instead of internal messages such as `Canonical point content has not been saved`.

## Capabilities

### New Capabilities
- `catalog-node-status-model`: Defines the normalized status taxonomy, priority rules, aggregation behavior, and boundaries between core node readiness and async ES/RAG consumption.

### Modified Capabilities
- `teacher-experiment-catalog-editor`: Replaces publish-check UI behavior with node-status UI behavior in the catalog tree and selected-node workbench.
- `catalog-point-index-evidence-jobs`: Clarifies that ES indexing and AI/RAG evidence jobs are derived asynchronous consumption statuses that must not overload the tree's primary point readiness marker.

## Impact

- Teacher frontend:
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeNodeList.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeRow.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogEditorHeader.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogPublishChecksPanel.tsx` or its replacement
  - catalog tree styles and visual QA artifacts
- Teacher API/types:
  - `apps/web-teacher/src/api/catalogTree.ts`
  - catalog status mappers and hooks
- Backend catalog status/validation:
  - `server/app/domains/catalog_tree/common.py`
  - `server/app/domains/catalog_tree/nodes.py`
  - `server/app/domains/catalog_tree/student_read_models.py`
  - `server/app/domains/catalog_tree/jobs.py`
- OpenSpec/contracts:
  - Adds the node status model contract.
  - Updates teacher catalog editor and async catalog job contracts.
- Tests and QA:
  - Backend validation/status tests.
  - Teacher frontend unit tests and visual QA for normal tree, problem tree, selected point, node status panel, and async diagnostics.
