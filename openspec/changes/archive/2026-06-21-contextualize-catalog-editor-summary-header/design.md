## Context

The previous change gave the selected-node editor a stronger title card, but the summary area still uses five uniform metric blocks for every node. That is visually tidy, yet it does not match how a complex experiment catalog is authored:

- A directory is a navigation and grouping object. Its useful header information is structure and readiness of the subtree.
- A point is a learning-content object. Its useful header information is content/resource completeness and publication readiness.
- `目录` and `点位` are identity cues, not dashboard metrics.
- Repeating both direct child count and descendant point count can make the header feel padded when the numbers overlap.

This follow-up keeps the title card and tab view from the prior change, but changes the information model inside the card.

## Goals / Non-Goals

**Goals:**

- Use a leading icon and small semantic cue to distinguish directories from point nodes.
- Show directory nodes with a compact structure summary and readiness summary instead of generic metric blocks.
- Show point nodes with a compact resource/readiness checklist: content, video, student card, related experiments, and publication checks.
- Make warnings and missing requirements visually stronger than already-good states.
- Merge or suppress redundant counts so the header does not look like it is filling space.
- Keep all data derived from the existing `CatalogNodeDetail` object.

**Non-Goals:**

- Do not change backend catalog APIs, validation rules, publication behavior, or stored data.
- Do not redesign the sidebar tree or editor tab behavior.
- Do not add new analytics counters or asynchronous queries.
- Do not introduce a global dashboard/stat-card component.

## Decisions

### Decision 1: Identity belongs in the title row

Directory/point identity should move out of the summary metrics. The title row will show a leading icon:

- `Folder` for directories
- `FlaskConical` for points

The icon can sit with the existing status dot and title. A small semantic cue may appear near the breadcrumb or helper line, but it should not compete with the title.

Alternatives considered:

- Keep a large `节点类型` block: rejected because the user already knows the kind from the tree and icon; it is not an action-driving metric.
- Use only color: rejected because the meaning should not rely on color alone.

### Decision 2: Directories use structure and readiness rows

Directory headers should answer:

1. What does this directory contain?
2. Is the subtree safe to publish?

Preferred directory summary:

- Structure line: `3 个直接子项 · 3 个点位` or `3 个点位` when direct children add little extra value.
- Readiness line: `发布检查通过` or `4 项待处理`.
- Optional note: `学生端可见`, `草稿`, or `已归档`.

Use one or two compact summary tiles/rows, not five equal boxes.

### Decision 3: Point nodes use a readiness checklist

Point headers should answer:

1. Is the learning content ready?
2. Are videos bound/published?
3. Is the student-facing card configured?
4. Are related experiments attached?
5. Is publication blocked?

Preferred point summary:

- `学习内容`: content status.
- `视频`: `已发布/已绑定` counts; `未绑定` should be visibly warning-like.
- `学生卡片`: configured/missing from existing node presentation fields.
- `相关实验`: count, muted when zero.
- `发布检查`: pass or issue count.

These can render as compact checklist chips/cards with icons. They do not need equal visual weight; warning items should be more prominent.

### Decision 4: Keep rendering data local and deterministic

All summary items should be computed in `CatalogEditorHeader.tsx` from existing `detail` and `node` data. Styling remains in `catalogTree.css`. No new hooks, queries, or API calls are needed.

## Risks / Trade-offs

- [Risk] Condensed summaries could hide a detail a teacher used to glance at. -> Mitigation: keep all fields accessible in the detailed tabs; the header only summarizes decision-driving state.
- [Risk] Warning styles could make healthy nodes look too quiet. -> Mitigation: successful states remain visible but use lighter treatment; problems get stronger treatment.
- [Risk] Student-card readiness may be approximate from current fields. -> Mitigation: derive from existing card description/image/icon fields and avoid wording that implies backend validation.
- [Risk] Header variants could diverge visually. -> Mitigation: share common title row, action group, and summary item primitives while changing content per node kind.

## Migration Plan

1. Validate the OpenSpec change before implementation.
2. Refactor `CatalogEditorHeader` summary item construction into directory and point variants.
3. Add leading kind icons and remove the large `节点类型` block.
4. Replace fixed metric grid styling with contextual summary rows/checklist styling.
5. Run focused catalog tests, typecheck, OpenSpec validation, build, and browser QA for directory and point selections.

Rollback is frontend-only: restore the previous fixed summary items in `CatalogEditorHeader` and related CSS.

## Open Questions

None for implementation. The display strategy is clear: identity as icon, state as badge, structure/resources as compact summaries, and warnings as the strongest header signal.
