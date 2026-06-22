## Why

The catalog workbench now has the right overall direction, but the learning-content taxonomy and filter contracts are still inconsistent. Teachers see counts for missing content, ready-to-publish, and published points, yet some filters can return an empty tree because summary counts, directory descendant aggregates, and row matching do not share one status model.

## What Changes

- Reclassify point learning content so `学生可见内容` owns three required peer fields: `实验原理`, `现象解释`, and `安全提示`.
- Keep the existing experiment-principle authoring modes, but treat `化学方程式` and `文字描述` as input modes under `实验原理`, not as separate top-level content categories.
- Expose structured missing-content keys for `实验原理`, `现象解释`, and `安全提示` while preserving the coarse `缺内容` state.
- Add focused workbench filters for missing specific fields, such as `缺内容：实验原理`, without turning the top summary chips into a noisy list of every sub-state.
- Fix status filtering so `待发布` and `已发布` use the same state source as the displayed counts and can reveal matching descendants through their ancestor directories.
- Add content-editor missing-field guidance that is inline, compact, and field-targeted rather than a large blocking warning.
- Make principle mode switching safe with autosave so an empty newly selected mode does not get reverted by stale detail hydration or autosave refreshes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `experiment-catalog-tree`: Refine chapter workbench filter semantics, search/filter visibility, and point learning content grouping.
- `catalog-node-status-model`: Refine missing-content status keys, exact missing-field copy, and directory descendant aggregate counts used by filters.
- `catalog-point-natural-equation-authoring`: Clarify principle mode switching and autosave behavior for equation/text principle modes.

## Impact

- Affected backend code:
  - `server/app/domains/catalog_tree/common.py`
  - `server/app/domains/catalog_tree/nodes.py`
  - catalog tree API schema/type payloads as needed for structured missing-field counts
- Affected teacher frontend code:
  - `apps/web-teacher/src/api/catalogTree.ts`
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeNodeList.tsx`
  - `apps/web-teacher/src/features/catalog-tree/catalogTreeMappers.ts`
  - `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
  - `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
- Focused backend and frontend contract tests must cover fine-grained missing fields, descendant filter matching, ready/published filters, and autosave-safe principle mode switching.
- No new third-party dependencies are expected.
