## Why

The catalog point workbench currently mixes point identity, student-facing content, preview, diagnostics, publication, and destructive lifecycle actions as if they were peers. This makes the selected-point card visually noisy and obscures the actual next step a teacher should take.

## What Changes

- Move generic preview and diagnostics actions into a secondary `更多` menu instead of showing `预览学生端` / `高级` beside publish and archive actions.
- Drive the selected-node primary action from a derived status machine instead of only checking `node.status`.
- Treat point title as a header-level identity field with an inline edit affordance; remove it from the routine content form.
- Move `多目录共享实验` copy from the content tab into the selected-point identity/status area.
- Rename and visually normalize the point content tab section so `内容`, `视频`, and `相关实验` use a consistent information hierarchy.
- Allow teacher preview to represent non-published point states where safe, so preview remains a general inspection action.
- Tighten the student-availability/status semantics so a point is only considered student-available when both the catalog placement and shared point content are published.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: refine selected-point header actions, point identity placement, content tab hierarchy, preview affordance, and status-machine-driven primary actions.

## Impact

- Frontend:
  - `apps/web-teacher/src/features/catalog-tree/CatalogEditorHeader.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
  - `apps/web-teacher/src/features/catalog-tree/catalogTreeMappers.ts`
  - `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
  - focused catalog tree tests/contracts
- Backend:
  - catalog node status summary semantics
  - teacher preview service archive/published-state handling where needed
- No database migration or new external dependency is expected.
