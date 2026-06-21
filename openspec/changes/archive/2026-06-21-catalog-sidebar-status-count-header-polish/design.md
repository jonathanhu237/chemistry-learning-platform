## Context

The previous Arborist polish pass replaced the old Ant Design Tree behavior and moved the teacher catalog tree toward the shared Dribbble/Gmail sidebar target. The remaining issues are smaller but still visible in the first-screen authoring experience:

- tree rows still render raw backend status values such as `published`;
- the status tag is visually louder than the sidebar reference and competes with the node title;
- directory rows do not show the useful "how many point leaves are under this folder" count from the reference;
- client-side counting would be inaccurate because children are loaded lazily;
- the left panel has duplicated creation controls: a chapter heading `目录 / 点位` control and a tree header add control;
- point/folder icons are close to the right idea, but too small for the current sidebar density.

Current implementation anchors:

- `server/app/domains/catalog_tree/common.py` owns `node_select()`, `row_dict()`, and `node_card()` for catalog node card read-model shape.
- `apps/admin-web/src/api/catalogTree.ts` owns the `CatalogNodeCard` frontend contract.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeRow.tsx` owns Arborist row rendering, row metadata, icons, action menus, and visible status output.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeNodeList.tsx` owns the tree toolbar/header and root add menu.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx` owns the current chapter heading and duplicate root add controls.
- `apps/admin-web/src/features/catalog-tree/catalogTreeMappers.ts` owns kind/status mappers and should own Chinese-facing status labels.

## Goals / Non-Goals

**Goals:**

- Make the left tree visible language fully Chinese-facing; raw `published`, `draft`, and `archived` must not appear in visible tree rows.
- Replace the selected/unselected row status tag strategy with a quieter status-dot system inspired by the Dribbble/Gmail sidebar reference.
- Add an authoritative recursive directory point count to catalog node cards so directory rows can show a stable trailing number independent of lazy loading.
- Keep point rows distinct from directory rows; point rows may show video binding completion, but not a directory descendant count.
- Increase folder and experiment point icon size enough to read clearly in the current sidebar row density.
- Remove duplicate root creation controls and keep one compact tree-toolbar add action for creating top-level directory or point nodes in the selected chapter.
- Keep all changes scoped to the catalog tree/admin feature and existing backend catalog tree read-model modules.

**Non-Goals:**

- Do not change the Arborist tree engine or replace it with another tree dependency.
- Do not redesign the right editor layout in this change.
- Do not add video upload inside the catalog tree editor.
- Do not alter point publication semantics, ES indexing semantics, media binding APIs, related-link APIs, or stable node identity.
- Do not make directory status represent an aggregate child status unless a later product change explicitly asks for it.
- Do not implement a global admin design-system rewrite.

## Decisions

### Decision 1: Add a backend-owned `descendant_point_count` field

Directory count must mean "the number of point leaf nodes under this directory across all descendant levels." Because the Arborist tree lazy-loads children, the frontend cannot compute that value reliably from the currently loaded tree. The catalog node card should therefore expose a backend-owned field:

```ts
type CatalogNodeCard = {
  // existing fields...
  descendant_point_count: number;
};
```

Semantics:

- for a directory node, count descendant nodes where `node_kind = 'point'`;
- count descendants recursively, not just direct children;
- exclude archived descendants from normal teacher tree counts because normal tree listings also exclude archived nodes;
- for a point node, return `0` so renderers can treat the field uniformly;
- counts are read-time values and are refreshed on the next root/children/detail/search fetch after move, archive, restore, or creation.

Implementation options:

- Correlated recursive CTE inside `node_select()`: simple and keeps the read-model shape centralized. This is acceptable for the current catalog size and can be indexed/optimized later if needed.
- Separate aggregate query per list endpoint: more efficient for large batches but risks inconsistent shape across roots, children, detail, and search.
- Frontend-only count: rejected because lazy loading makes it misleading.

### Decision 2: Render status as a dot first, Chinese text only when explicit

The left tree should use status dots for scanning and avoid loud English tags. The mapper should expose both display labels and status classes:

- `published` -> `已发布`, green dot;
- `draft` -> `草稿`, amber dot;
- `archived` -> `已归档`, neutral gray dot.

Directory rows use the directory node's own status dot. The dot is not a subtree aggregate. Validation warnings remain a separate warning icon because "publish status" and "has validation issue" are different meanings.

Suggested row behavior:

- unselected row: show a small status dot near trailing metadata and expose the Chinese label through `aria-label`/tooltip;
- selected or focused row: optionally show a compact Chinese label such as `已发布` if the row needs additional clarity, but never render raw backend English;
- point row: show video completion such as `1/1` only when media exists or when selected/hovered, so video metadata does not dominate the tree.

### Decision 3: Directory count is trailing metadata, not part of the title

The Dribbble reference uses quiet right-aligned numbers. The catalog sidebar should mirror that pattern:

```text
[chevron] [folder]  氯、溴、碘的置换次序       [8] [status dot] [+] [...]
[spacer ] [flask ]  氯水 + KBr 溶液 + CCl4      [1/1] [status dot] [...]
```

Rules:

- directory trailing number is `descendant_point_count`;
- do not show `0` if it makes empty directories noisy; prefer hiding zero or showing it only on selected/hover if product wants empty-state visibility;
- point trailing video ratio is not the same field and must not appear on directories;
- warning icon and hover actions must not shift title/icon alignment when they appear.

### Decision 4: Use one root creation surface in the tree toolbar

Creation controls should feel like a sidebar tool, not a form header. The root creation affordance should live beside the tree title:

```text
目录树                                      [+] [...]
```

The `+` menu contains:

- `新建目录`
- `新建点位`

The chapter heading should keep context only:

```text
当前章节
第 13 章 卤族元素
```

It should not also expose a separate `目录 / 点位` segmented add control. The route/page title area should not expose another visible root creation button while this tree toolbar is the selected design. Refresh, expand all, and collapse all can live in a subtle `...` menu or a single icon-only toolbar control if implemented.

### Decision 5: Keep the polish feature-local

The change touches both backend and frontend, but it should remain narrow:

- backend shape changes stay in catalog tree read-model functions and tests;
- frontend API type changes stay in `apps/admin-web/src/api/catalogTree.ts`;
- row rendering, labels, icons, and toolbar layout stay in catalog tree feature modules;
- status mapping should be centralized in `catalogTreeMappers.ts` so no row renders raw backend values directly.

## Risks / Trade-offs

- [Risk] A per-row recursive count query could become expensive for very large chapters. -> Mitigation: start centralized and tested in `node_select()`; if performance regresses, replace the correlated count with a batched recursive aggregate while preserving the same API field.
- [Risk] Status dots can become too subtle for teachers. -> Mitigation: include Chinese tooltip/aria label and allow a compact Chinese chip on selected/focused rows.
- [Risk] Removing duplicate add buttons may make creation less discoverable for first-time users. -> Mitigation: keep the tree-toolbar `+` visually aligned with familiar VS Code/Gmail sidebar patterns and give menu labels explicit Chinese wording.
- [Risk] Existing tests may assert raw status strings. -> Mitigation: update tests to assert semantic labels/classes rather than backend enum text.
- [Risk] Mojibake in terminal output can hide Chinese label regressions during CLI review. -> Mitigation: verify in browser screenshots and use source-level tests for mapper return values.

## Migration Plan

1. Add `descendant_point_count` to the backend node card query and serializer with default `0`.
2. Extend the admin API type and test fixtures with the new field.
3. Add Chinese status label/dot mappers.
4. Update Arborist row rendering and CSS for icon size, status dot, directory count, and stable trailing layout.
5. Remove duplicate root creation controls from the chapter heading/page title, leaving the tree-toolbar `+` menu as the visible root creation surface.
6. Update focused tests and browser screenshots.
7. Run strict OpenSpec validation, backend tests, admin tests/typecheck/build, and browser QA.

Rollback is code-only: remove the count field rendering and restore the previous add controls if needed. The backend field is additive and does not require database migration.
