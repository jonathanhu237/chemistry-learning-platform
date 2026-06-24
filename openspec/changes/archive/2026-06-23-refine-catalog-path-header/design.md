## Context

The implemented chapter catalog browser now treats catalog orientation as a small mobile breadcrumb system instead of a text path. The current product rule is:

- first line: fixed learning scope chip on the left, `搜索` and `更多` tools on the right;
- second line: child directory breadcrumb chips, from left to right, horizontally scrollable;
- current/leaf directory: rightmost chip with selected styling;
- full chip text: never truncated, because the rail itself scrolls.

This replaces the older idea of a protected, ellipsized path row. The old approach still forced students to read a single compressed path string and required a separate `上一级` button. The current interaction makes every ancestor directly tappable and scales to arbitrarily long directory names.

## Goals / Non-Goals

**Goals:**

- Keep the learning scope visible as the stable root context.
- Keep `搜索` and `更多` reachable in the first row without competing with deep child paths.
- Render nested catalog ancestry as horizontally scrollable chips on a second row.
- Show breadcrumb chips at natural content width, with no `max-width`, ellipsis, or clipped text.
- Highlight the current directory as the rightmost selected chip.
- Let students jump to any ancestor by tapping its chip, replacing the need for `上一级`.
- Keep search result cards focused on result title and direct parent directory, with ancestor context as weaker metadata.

**Non-Goals:**

- Do not redesign the catalog tree, element rail, point detail page, or bottom navigation.
- Do not add a new backend endpoint or data model.
- Do not introduce another gesture library or mobile simulation dependency.
- Do not reintroduce a full-path-only text row or a separate `上一级` action.

## Decisions

### Decision: Split catalog orientation into root row and child breadcrumb row

The header becomes:

- Row 1: learning scope/root chip on the left, `搜索` and `更多` on the right.
- Row 2: child directory chips only, displayed from root child to current leaf.

Rationale: root scope is stable and should not be swept away by child-path scrolling. Child paths can be arbitrarily long and should scroll independently below the fixed action row.

### Decision: Make chips natural-width and rely on horizontal scrolling

Breadcrumb chips must not use `max-width`, `text-overflow: ellipsis`, or text clipping. The scroll container owns overflow.

Rationale: once the UI is a horizontal rail, protective text truncation is counterproductive. Students can swipe the rail to read complete names.

### Decision: Remove `上一级` in favor of tappable breadcrumbs

Every breadcrumb chip navigates directly to its directory. Root navigates to the catalog root. The current chip remains tappable but keeps `aria-current="page"`.

Rationale: tappable ancestors are more direct than a single-step button and match common mobile file/path navigators.

### Decision: Search results emphasize direct parent directory

Result cards keep the title first, display `父目录：<direct parent>` as primary metadata, and show only ancestor context as weak secondary text. The weak ancestor hint omits the result itself and does not compete with the parent line.

Rationale: students scanning results usually need to know "which directory this point belongs to" first, not parse a long full path.

## Risks / Trade-offs

- [Risk] Long root scope names can compete with actions in the first row. -> Mitigation: the root chip area scrolls horizontally while action buttons stay fixed.
- [Risk] Deep paths add vertical height because the child row is separate. -> Mitigation: the row is compact and appears only when nested.
- [Risk] Scrollable chips can hide earlier ancestors off-screen. -> Mitigation: the active/current chip scrolls into view on directory changes, and students can swipe back to earlier ancestors.
- [Risk] Tests may preserve the old single-line path contract. -> Mitigation: route tests now assert the two-row structure, no `上一级`, root-row separation, child-row breadcrumbs, clickable ancestor jump, and direct-parent search metadata.
