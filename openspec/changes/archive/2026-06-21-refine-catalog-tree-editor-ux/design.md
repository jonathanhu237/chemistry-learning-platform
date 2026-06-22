## Context

The committed catalog-tree implementation already enforces the updated product model: chapter roots contain directory nodes and point leaves; directories act as navigation/category/card nodes; points own video learning content and stable point identity. The remaining issue is the teacher authoring experience.

Current admin screenshots and code show two UX problems:

1. The left tree uses mixed visual systems: Ant Design's default disclosure triangle, Ant Design drag affordance, custom green/blue node icons, a pale-green selected row card, and separated row controls. The result works, but it reads like a form table rather than a professional document/file tree.
2. The selected point editor exposes operational, content, navigation, binding, search, and validation fields in one vertical surface. Teachers see `Node ID`, node type, duplicate point/title concepts, card metadata, move fields, point knowledge, related links, videos, search-index diagnostics, and publication validation at the same priority.

Research references used for this design:

- Apple Human Interface Guidelines: [Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars) and [Outline views](https://developer.apple.com/design/human-interface-guidelines/outline-views) emphasize source-list hierarchy, clear selection, disclosure only where expansion exists, and predictable row density.
- GitHub Primer [Tree view guidelines](https://primer.style/product/components/tree-view/guidelines/) emphasize repository-like hierarchy, full-row focus/selection, clear nested structure, and contextual actions.
- PatternFly [Tree view design guidelines](https://www.patternfly.org/components/tree-view/design-guidelines) emphasize disclosure, keyboard behavior, and tree actions without crowding every row.
- Carbon [Tree view usage](https://carbondesignsystem.com/components/tree-view/usage/) and [style](https://carbondesignsystem.com/components/tree-view/style/) emphasize consistent indent, icon treatment, active/hover states, and scalable information density.
- MUI X [Tree View](https://mui.com/x/react-tree-view/) was reviewed as a mature option, but it pulls in a Material UI stack that conflicts with the current Ant Design shell.
- `react-arborist` was checked through npm on 2026-06-20. It provides drag/drop, custom rendering, virtualization, and React 19-compatible peer ranges through `react >=16.14`, but adds `react-dnd`, `react-dnd-html5-backend`, `react-window`, and `redux`.

Current implementation anchors:

- `apps/admin-web/src/features/catalog-tree/CatalogTreeNodeList.tsx` owns current tree rendering and Ant Design Tree drag callbacks.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeEditor.tsx` owns the large selected-node editor, including basics, point content, related links, video binding, search preview, and publication validation.
- `apps/admin-web/src/features/catalog-tree/catalogTree.css` owns tree and editor visual treatment.
- `apps/admin-web/src/api/catalogTree.ts` already exposes directory/point-only types and move/reorder/media/related-link APIs.

## Goals / Non-Goals

**Goals:**

- Make the left tree visually coherent, elegant, and fast to scan at admin desktop sizes.
- Clearly distinguish directories and point leaves without using noisy tags or card blocks inside tree rows.
- Replace obvious up/down ordering UI with drag ordering/moving plus an accessible fallback action.
- Keep row actions discoverable but contextual: hover, focus, selection, or row menu.
- Choose a mature tree behavior boundary and document the trade-off, with `react-arborist` as the preferred implementation candidate.
- Turn the right editor into a focused authoring workspace where default point editing shows the fields teachers need most.
- Move low-frequency/debug fields into advanced/publish panels.
- Preserve all current semantic constraints: no hybrid/shortcut, no catalog upload, no directory point-content ownership, and no teacher notes in student/search surfaces.
- Add visual QA tasks so implementation is judged against actual screenshots, not just compilation.

**Non-Goals:**

- Do not change backend catalog semantics or database shape unless implementation discovers a missing API for the UI contract.
- Do not redesign the student H5 catalog/cards in this change.
- Do not introduce arbitrary card layout builders for teachers.
- Do not add a media upload flow inside catalog management.
- Do not change ES indexing, RAG evidence semantics, or question-workbench evidence rules.
- Do not migrate to Material UI or replace the Ant Design admin shell.

## Decisions

### Decision 1: Use a file/source-list visual model

The catalog tree should visually resemble a professional file/source tree rather than a nested list of cards.

Required row language:

- A 16px disclosure chevron appears only for expandable directories.
- Point rows reserve the same chevron width with a spacer, so titles align.
- Directory and point icons use the same optical size, stroke weight, and color system.
- Selection is full-row and subtle, with a small accent edge or soft background rather than a bordered card.
- Hover/focus states are full-row and do not shift layout.
- Status is compact: one small pill or muted inline text, not multiple always-visible tags.
- Drag handle is visible on hover/focus/drag, placed inside the row rhythm rather than isolated far left.
- Guide lines are fine and quiet; indentation stays compact enough for deep chemistry catalog paths.
- Row title truncates predictably and preserves status/actions without overlap.

Alternative considered: keep the current Ant Design Tree row and only tune CSS. Rejected as the default path because the current result already demonstrates visual tension between Ant Design internals and custom row cards. It can still be selected if a spike proves the same polished row language is achievable with less dependency cost.

### Decision 2: Prefer `react-arborist` as behavior engine with a custom skin

Implementation should first spike `react-arborist` for the left tree. The value is that it separates tree behavior from rendering: the project can own a custom Git/Finder/VS Code-like row visual while relying on a mature library for drag/drop, virtualization, selection, and keyboard conventions.

Selection criteria:

- Supports controlled data, selection, open state, and row rendering.
- Supports drag reorder/move with before/inside/after drop intent and visible drop indicators.
- Allows rejecting drops onto point nodes, into descendants, or across disallowed chapter boundaries before API calls.
- Allows route-owned bundling so the dependency does not load in unrelated admin routes.
- Can meet the visual spec without fighting library CSS.
- Can be covered by unit tests and browser screenshot checks.

Fallback: continue with Ant Design Tree only if the spike proves it can match the required row language, drop indicator, keyboard fallback, and layout stability with less custom code than `react-arborist`.

Rejected option: MUI X Tree View. It is mature, but it introduces Material UI and Emotion peer dependencies into an Ant Design admin shell. That would increase design-system conflict for a single feature.

### Decision 3: Tree interactions are command-light by default

The tree should optimize for scanning and selection. Commands remain available without turning every row into a toolbar.

Default row:

```text
⌄  folder  卤、溴、碘的置换次序                  published
   ├─ file  氯水 + KBr 溶液 + CCl4              draft · 1/1 视频
   ├─ file  氯水 + KI 溶液 + CCl4               draft
   └─ file  溴水 + KI 溶液 + CCl4               draft
›  folder  氯水、溴水、碘水氧化性差异...
```

Actions:

- Top toolbar: create root directory, create root point if allowed, refresh, search.
- Selected row or hover menu: add child directory/point for directories, archive/restore, publish/unpublish where supported, copy id, and advanced actions.
- Drag: primary way to reorder and move.
- Keyboard/menu fallback: move before/after/into directory for accessibility and precision.

Always-visible up/down controls are removed from rows. They may appear only inside a fallback menu or focused advanced command surface.

### Decision 4: Editor becomes a selected-node workspace

The right side should feel like editing a document/node, not filling a backend object dump.

Shared sticky header:

- status pill
- node kind pill
- video count for point nodes
- selected node title
- breadcrumb/path
- primary actions: preview student view when available, publish/unpublish, archive/restore

Tabs or segmented sections:

- `内容`: primary authoring fields.
- `视频`: existing-media binding, preview, binding status.
- `相关实验`: related point links.
- `学生卡片`: directory card fields and constrained point card overrides.
- `发布检查`: validation errors/warnings and publication readiness.
- `高级`: raw node id, parent/order data, search-index diagnostics, API/debug metadata, copy-id actions.

Directory default content:

- directory title
- teacher-only note
- student-visible description
- optional student-card preview entry point

Point default content:

- point name/title as the single primary title concept
- teacher-only note with clear "teacher only / not indexed / not shown to students" treatment
- principle mode with equation/text branch
- phenomenon explanation
- safety note

Point fields not shown by default:

- raw `Node ID`
- parent id/display order controls
- ES/search preview JSON
- validation internals
- card cover/icon/accent/emphasis controls
- related-link sort internals

Alternative considered: keep one long form but collapse low-frequency cards. Rejected because a long form still communicates all concerns as equal priority and makes point content feel buried.

### Decision 5: Point title and node title are one visible concept

For point nodes, teachers should not have to maintain both "节点标题" and "点位名" in the primary editor. The UI should present one primary title field and map it to the correct payloads. If the backend still stores both node title and point title, implementation should synchronize them by default and expose divergence only in `高级` if there is a real product need.

For directory nodes, the title is the navigation/card title.

### Decision 6: Student-card customization is bounded

Directory cards can carry stronger presentation metadata because they are category/navigation cards: image, icon, accent, description, and layout variant.

Point card customization stays constrained: short description, optional cover/thumbnail override, icon/accent, and emphasis. It must not allow arbitrary layouts that make point rows look like directories or marketing cards. If no point override is configured, the point card should derive defaults from title, point knowledge summary, and bound video thumbnail.

### Decision 7: Visual QA is part of acceptance

This change is about interaction quality and visual clarity, so tests cannot stop at typecheck.

Implementation must include:

- browser screenshot checks at common admin widths, including narrow laptop width where the current row/action layout is most likely to collide;
- screenshot or DOM assertions for expanded directory, collapsed directory, selected point, hover/focus actions, drag/drop indicator, and right editor default point tab;
- text-overlap checks where practical through Playwright bounding boxes or focused visual review notes;
- a short implementation note comparing the chosen tree library/path with the research criteria.

## Risks / Trade-offs

- [Risk] `react-arborist` adds dependencies and styling surface. -> Mitigation: lazy-load/route-own the catalog workspace, document bundle impact, and keep a fallback to Ant Design Tree if the spike fails.
- [Risk] Drag/drop can become mouse-only. -> Mitigation: keep row menu or selected-node fallback movement and cover focus/keyboard interactions.
- [Risk] Hiding fields could make debugging harder for power users. -> Mitigation: move raw ids, parent/order, search diagnostics, and validation internals into an explicit `高级` or `发布检查` panel instead of removing them.
- [Risk] Splitting the editor can create state synchronization bugs. -> Mitigation: centralize form hydration/payload mapping and add mapper tests for directory and point cases.
- [Risk] Point title/node title synchronization may mask backend inconsistencies. -> Mitigation: define a deterministic mapping and surface mismatches in advanced/debug state if needed.
- [Risk] UI polish can regress without a concrete gate. -> Mitigation: require screenshot/Playwright checks and keep a small visual acceptance checklist in tasks.

## Migration Plan

1. Record the current tree/editor screenshots as baseline references in implementation notes or test artifacts.
2. Spike `react-arborist` and Ant Design Tree against the required interaction/visual criteria.
3. Select the tree behavior boundary and document the decision.
4. Refactor tree modules before visual rewrite so row rendering, drag logic, node actions, and search remain separate.
5. Refactor the selected-node editor into header plus task panels before changing detailed styling.
6. Move low-frequency fields into `高级`/`发布检查` while keeping existing API payload behavior.
7. Apply visual polish and run browser QA.

Rollback is application-code only: revert the UI dependency and components to the previous Ant Design Tree/editor path. No destructive data migration is part of this change.

## Open Questions

- Should point title/node title divergence be fully removed at the API layer in a later backend cleanup, or only hidden in this UI?
- Should the advanced panel be visible to all teachers, or gated behind a compact "developer/debug" affordance?
- Should the tree support cross-chapter moves in a later workflow, or explicitly keep all moves chapter-local?
- Should directory card previews render inline inside the editor, or open a student-page preview route when that exists?
