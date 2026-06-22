## Context

The previous `refine-catalog-tree-editor-ux` change split the catalog tree/editor modules and moved the right editor toward task-owned panels. That pass also documented `react-arborist` as the preferred mature tree engine, but retained Ant Design Tree to reduce implementation risk.

Post-implementation screenshots showed the Ant Design fallback still fails the desired visual language:

- the disclosure arrow is not visually attached to the folder/point row;
- Ant Design's outer tree layout and custom inner row layout create a "double tree row" feeling;
- six-dot drag grips are visible and hard to interpret;
- directory rows can still expose point-only editor tabs such as video and related experiments;
- labels such as "root node" expose data-structure language rather than teacher workflow language.

The user-provided visual target is the Dribbble "Sidebar Navigation Tree" reference (`https://dribbble.com/shots/26899749-Sidebar-Navigation-Tree`), with acceptance that `react-arborist`'s Gmail/sidebar demo is already close enough to the desired quality. The implementation should therefore use Arborist for tree behavior and build a feature-local sidebar skin, rather than continuing to fight Ant Design Tree internals.

Current implementation anchors:

- `apps/admin-web/src/features/catalog-tree/CatalogTreeNodeList.tsx` wraps Ant Design Tree and should become the Arborist adapter/orchestrator.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeRow.tsx` owns current row rendering and should become the sidebar row renderer or be replaced by Arborist node/render helpers.
- `apps/admin-web/src/features/catalog-tree/catalogTreeData.ts` owns current Ant Design tree data and drop helpers; it should evolve into Arborist data adaptation and move-payload mapping.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeEditor.tsx` builds tabs unconditionally and should filter tabs by node kind.
- `apps/admin-web/src/features/catalog-tree/catalogTree.css` owns all tree/editor visual styling and should hold the Arborist sidebar skin without global overrides.

Dependency research on 2026-06-20:

- `react-arborist@3.10.5`: MIT, React peer `>=16.14`, dependencies `react-dnd`, `react-dnd-html5-backend`, `react-window`, `redux`, `use-sync-external-store`; supports custom node, row, drag preview, cursor, selection sync, keyboard navigation, virtual rendering, `disableDrop`, and `onMove`.
- `lucide-react@1.21.0`: React peer supports React 19, `sideEffects: false`; suitable for `Folder`, `FolderOpen`, `FlaskConical`, `TestTubeDiagonal`, `PlayCircle`, `Plus`, `MoreHorizontal`, `ChevronRight`, `ChevronDown`, and `GripVertical`.
- `react-complex-tree@2.6.1`: accessible and capable, but heavier API and not as visually aligned with the requested Gmail/sidebar Arborist target.
- `@minoru/react-dnd-treeview`: capable drag tree but more of a DnD toolkit; less complete as a Finder/VS Code/Figma-like tree behavior layer.

## Goals / Non-Goals

**Goals:**

- Migrate the teacher catalog tree rendering from Ant Design Tree to `react-arborist`.
- Preserve lazy child loading, selected-node synchronization, search-result selection, move/reorder persistence, publication/archive actions, and accessible fallback commands.
- Make the left tree visually match the requested Dribbble/Gmail sidebar feeling:
  - clean nested guide lines;
  - compact rows;
  - chevrons attached to directory rows;
  - experiment icon for point nodes;
  - full-row rounded selected state;
  - quiet trailing metadata;
  - hover/selected actions instead of row clutter.
- Use `lucide-react` iconography for visual consistency and experiment semantics.
- Hide `视频` and `相关实验` editor panels for directory nodes and avoid running point-only queries for directories.
- Keep all new dependency use and styling scoped to the catalog route.
- Verify the result with screenshot/DOM visual QA against the current poor screenshots and the requested sidebar navigation reference.

**Non-Goals:**

- Do not change backend catalog APIs or database shape.
- Do not reintroduce hybrid or shortcut node types.
- Do not add media upload inside the catalog editor.
- Do not redesign the right editor's overall structure beyond node-kind tab filtering and query gating.
- Do not copy proprietary Dribbble assets; copy the interaction/spacing/visual language using project-owned CSS and open-source icons.
- Do not migrate the admin shell from Ant Design.

## Decisions

### Decision 1: Use `react-arborist` as the catalog tree engine

The Ant Design Tree fallback has reached the point where more CSS polish would still leave two competing tree systems: AntD's switcher/indent/content wrapper and the feature's custom row. `react-arborist` is explicitly designed for custom VS Code sidebar, Mac Finder, Windows Explorer, and Figma layer-panel style trees. It lets the project own the row visual while the library owns the complex behavior.

Implementation direction:

```tsx
<Tree
  data={arboristData}
  idAccessor="id"
  childrenAccessor="children"
  selection={selectedNodeId ?? undefined}
  rowHeight={34}
  indent={22}
  disableMultiSelection
  disableEdit
  disableDrop={disableCatalogDrop}
  onActivate={(node) => onSelect(node.data.catalogNode)}
  onMove={handleCatalogMove}
  onToggle={handleCatalogToggle}
  renderCursor={CatalogArboristCursor}
  renderDragPreview={CatalogArboristDragPreview}
>
  {CatalogArboristNode}
</Tree>
```

Alternatives considered:

- Continue Ant Design Tree: rejected because current screenshots show the visual mismatch is structural, not a small style bug.
- `react-complex-tree`: capable, but less directly aligned with Arborist's Gmail/sidebar demo and would still require a full skin.
- `@minoru/react-dnd-treeview`: useful for drag/drop but weaker as a complete file-tree behavior layer.

### Decision 2: Adapt catalog data to Arborist's internal/leaf model

Arborist treats a node as internal when `children` is an array and as a leaf when children are absent/null. Catalog directories must be internal even before their children are loaded so they can show a chevron and accept drops.

Proposed data shape:

```ts
type CatalogArboristNode = {
  id: string;
  name: string;
  kind: "directory" | "point";
  catalogNode: CatalogNodeCard;
  loaded: boolean;
  children?: CatalogArboristNode[] | null;
};
```

Mapping rules:

- directory with `has_children === true`: `children: loadedChildren ?? []`, `loaded: Boolean(loadedChildren)`;
- directory with no children yet but can accept children: `children: []`, `loaded: true` or `false` depending on fetch state;
- point: `children: null` or omit `children`, never accept children;
- root chapter is not rendered as an Arborist node; it remains page context.

Lazy loading:

- On directory toggle/open, if `kind === "directory" && has_children && !loaded`, fetch `listCatalogChildren(node_id)`.
- Merge loaded children without replacing unrelated open/selected state.
- After search selection or newly-created node selection, call Arborist API `openParents`/`scrollTo` where practical.

### Decision 3: Use the Dribbble/Gmail sidebar row language

The catalog row should be a single grid/flex row controlled by the feature, not an AntD Tree title inside an AntD Tree wrapper.

Required row anatomy:

```text
[guide area] [chevron/spacer] [icon] [title/subtitle] [trailing status/count] [hover actions]
```

Visual details:

- Row height: target 32-36px for normal rows.
- Indent: target 20-24px per level.
- Guide lines: soft vertical curves/lines similar to the reference; implemented with CSS pseudo-elements based on `node.level` and row classes where practical. If curved elbows are too brittle, use straight soft vertical guides and document the limitation.
- Chevron: visible only for directories; point leaf uses a same-width spacer.
- Icons:
  - directory: `Folder` or `FolderOpen`;
  - point: `FlaskConical` or `TestTubeDiagonal`;
  - video availability is trailing metadata, not the primary icon.
- Selected row: full-row rounded pill background, no card border.
- Hover row: light background, no layout shift.
- Drag handle: the row itself is the primary drag target via Arborist `dragHandle`; optional `GripVertical` appears only on hover/selected/drag for discoverability. No always-visible six-dot grip.
- Trailing actions:
  - directory selected/hover: child-add `+` and more menu;
  - point selected/hover: more menu only;
  - all trailing actions remain stable-width to avoid title/status overlap.
- Root action: rename visible action from "根节点" to teacher language such as "添加到本章", with a menu for `新建目录` and `新建点位`.

### Decision 4: Persist Arborist moves through existing catalog APIs

Arborist `onMove` provides `{ dragIds, dragNodes, parentId, parentNode, index }`. The adapter must map this into existing move/reorder APIs.

Rules:

- Single-node move is the supported path; if multiple drag ids are emitted, handle the first or reject multi-move explicitly.
- `parentId === null` maps to chapter root.
- If the new parent equals the old parent, build reorder items for that sibling set.
- If the new parent differs, call existing move API with `parent_id` and `display_order`.
- Reject drops:
  - onto/into point nodes;
  - into a dragged node's descendant;
  - across a different selected chapter;
  - into any unsupported root/chapter target.
- Show a controlled warning and do not persist on invalid drop.
- Preserve selected node after success.

### Decision 5: Keep non-drag movement available but secondary

Teachers who cannot drag precisely still need fallback commands. Those commands belong in the row more menu or advanced panel, not as always-visible row buttons.

Fallback commands:

- move before sibling;
- move after sibling;
- move into selected/explicit directory where supported;
- copy Node ID;
- archive/restore;
- publish/unpublish where supported.

### Decision 6: Filter editor tabs by selected node kind

Directory nodes are category/navigation/card nodes. They must not expose video binding or related experiment editing.

Tab rules:

```ts
const directoryTabs = ["content", "student-card", "publish", "advanced"];
const pointTabs = ["content", "video", "related", "student-card", "publish", "advanced"];
```

Behavior:

- When the selected node is a directory and the active tab is `video` or `related`, switch to `content`.
- `useCatalogMediaAssets` and related point search queries must be disabled for directory nodes.
- Directory selected-node header must not show point video status.
- Directory default content remains title, teacher-only note, student-visible description, and card presentation.

### Decision 7: Visual QA must compare against the target feeling, not just non-overlap

The previous visual QA could pass while the tree still felt wrong. This change needs explicit screenshot acceptance around the requested look.

QA artifacts should capture:

- baseline current poor state;
- new Arborist tree normal width;
- new Arborist tree narrow laptop width;
- expanded directory with child point rows;
- collapsed directory;
- selected directory;
- selected point;
- hover/selected row actions;
- drag cursor/drop target state if Playwright can simulate it reliably;
- directory editor without video/related tabs;
- point editor with video/related tabs.

## Risks / Trade-offs

- [Risk] Arborist adds dependencies (`react-dnd`, `react-window`, `redux`). -> Mitigation: import only from the lazy catalog route, verify build report, and document chunk impact.
- [Risk] Lazy loading with Arborist internal/leaf detection can accidentally remove chevrons for empty-but-expandable directories. -> Mitigation: centralize mapping tests for directory `children` and loaded state.
- [Risk] Drag/drop persistence index math can reorder incorrectly. -> Mitigation: unit-test move/reorder mapping for root, same parent, different parent, and invalid parent cases.
- [Risk] Custom guide lines can become fragile across row heights and depths. -> Mitigation: prefer simple, stable soft lines over elaborate curves; screenshot-test deep trees and document any accepted limitation.
- [Risk] `lucide-react` icon style may clash with Ant Design icons used elsewhere. -> Mitigation: scope lucide to catalog tree and use consistent stroke width/color via CSS.
- [Risk] Existing tests assert Ant Design Tree details. -> Mitigation: update tests to assert behavior and visual contract rather than specific AntD classes.

## Migration Plan

1. Keep the existing AntD Tree implementation as the rollback reference until Arborist parity is verified.
2. Add `react-arborist` and `lucide-react` dependencies.
3. Introduce Arborist data adapter and move/drop mapping tests before replacing the UI.
4. Replace `CatalogTreeNodeList` internals with Arborist while preserving the same public props used by `CatalogTreeWorkspacePage`.
5. Replace row rendering and CSS with the sidebar navigation skin.
6. Update editor tab filtering/query gating for directory nodes.
7. Run visual QA, full admin validation, OpenSpec validation, and build report.

Rollback is application-code only: remove the Arborist adapter/dependencies and restore the previous AntD Tree component path. No database or backend rollback is required.

## Open Questions

- Which point icon should be final: `FlaskConical`, `TestTubeDiagonal`, or a small icon variant chosen after screenshot comparison?
- Should directory rows show child count (`子节点 N`) as a trailing count, or only publication status by default?
- Should the top-level add action allow root point creation directly, or should root creation default to directory with point creation primarily inside directories?
- Should the draggable area be the full row or a hover-only subtle handle? The preferred default is full row for clean visuals, with cursor/tooltip affordance on hover.
