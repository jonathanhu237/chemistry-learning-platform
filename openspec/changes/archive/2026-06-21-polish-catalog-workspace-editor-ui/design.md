## Context

The catalog workspace already has the correct functional model: a chapter-scoped Arborist tree on the left, selected-node editing tabs on the right, directory-vs-point tab filtering, and publication/validation workflows. Recent catalog changes intentionally focused on tree behavior and sidebar polish, leaving the right editor's overall visual structure out of scope.

Current UI anchors:

- `CatalogTreeWorkspacePage.tsx` renders the page title, left chapter heading, chapter `Select`, tree search, tree list, and right editor shell.
- `CatalogTreeEditor.tsx` renders the no-selection empty state and composes `CatalogEditorHeader` plus Ant Design `Tabs`.
- `CatalogEditorHeader.tsx` renders selected-node tags, title, breadcrumb, and actions.
- `catalogTree.css` gives `catalog-editor-panel`, `catalog-editor-empty`, and every `catalog-editor-section` card styling, while also giving the header and tabs nav their own borders/shadows.

The resulting selected state is visually over-fragmented: an outer right panel plus a standalone header card, standalone tab bar card, and standalone content card. The no-selection state uses the same detached empty card and feels sparse at desktop width. On the left, the selected chapter is rendered twice: once as a heading and once as a full-width dropdown immediately below it.

## Goals / Non-Goals

**Goals:**

- Let teachers change chapters directly from the left current-chapter title without keeping a duplicate full-width chapter dropdown.
- Preserve the existing tree search as a node/content search, not a chapter search.
- Make the right editor render as one cohesive selected-node workbench surface.
- Make the no-selection state use the same workbench shell and feel intentional at desktop widths.
- Keep all changes localized to catalog tree workspace/editor components and styles.
- Preserve existing catalog tree behavior, editing forms, validation, publication, API calls, query keys, and tab visibility rules.

**Non-Goals:**

- Do not replace Arborist or change tree drag/drop behavior.
- Do not redesign the backend catalog model, API contracts, database, or media binding semantics.
- Do not add video upload inside catalog management.
- Do not create a global admin design-system rewrite or broad shared component abstraction.
- Do not change student H5 catalog/card behavior.

## Decisions

### Decision 1: Promote chapter selection into a title switcher

The left panel should replace the full-width chapter `Select` with a title-level switcher in the current-chapter heading. The heading remains the context anchor, but the title row becomes interactive via Ant Design `Dropdown`, `Popover`, or `Select`-like overlay.

Preferred behavior:

- The label remains small and secondary: `Current chapter`.
- The visible chapter title remains typographic, with a subtle chevron/button affordance.
- Activating the control opens the same chapter options currently used by the full-width select.
- Selecting a chapter reuses `setChapterId`, which already clears the selected node through the existing effect.
- The tree search input stays below the heading and searches catalog nodes only.

Alternatives considered:

- Keep the existing dropdown and only reduce its size: rejected because it still duplicates title content.
- Move chapter switching to the global page title: rejected because chapter is local context for the left tree and right editor, while the page title identifies the whole tool.
- Add a separate top toolbar: rejected because it adds another visual band without solving the left-panel duplication as cleanly.

### Decision 2: Treat the right side as one workbench surface

The selected-node editor should have one outer workbench container. Inside it, the selected-node header, tabs, and content are sections of the same surface rather than independent cards.

Preferred structure:

```tsx
<main className="catalog-editor-panel">
  <CatalogTreeEditor ... />
</main>

// selected state
<div className="catalog-editor catalog-workbench-surface">
  <form anchors />
  <CatalogEditorHeader />
  <Tabs className="catalog-editor-tabs" ... />
</div>
```

Styling direction:

- `catalog-editor-panel` owns the main border, radius, background, and shadow.
- `catalog-editor-header` uses internal padding and bottom border, not a separate card border/shadow.
- `.catalog-editor-tabs > .ant-tabs-nav` uses internal padding and bottom border, not an independent rounded card.
- `.catalog-editor-section` becomes an unframed content section by default.
- Small nested panels such as media rows, validation rows, and card previews may remain framed because they are repeated or genuinely subordinate items.

Alternatives considered:

- Keep separate cards and tune shadows: rejected because the visual issue is structural fragmentation.
- Convert everything to Ant Design `Card`: rejected because it would still produce nested-card clutter and would be heavier than the existing feature-local CSS.
- Rebuild forms into new components: rejected for this polish pass because form behavior is already stable.

### Decision 3: Give empty state the same workbench affordance

The no-selection state should not render as an unrelated large card with a tiny default illustration. It should use the right workbench shell and a compact message block that fits the page's authoring context.

Preferred empty state:

- A subtle icon or mark, not a large decorative illustration.
- Primary text such as `Select a directory or point to edit`.
- Secondary text that explains the split: directories organize student navigation; points own learning content and videos.
- Optional muted chips or hints for directory and point, but no tutorial-heavy text.
- The empty shell should maintain right-panel alignment with selected state.

Alternatives considered:

- Remove the empty panel entirely: rejected because the page would feel broken before selection.
- Keep Ant Design `Empty` unchanged: rejected because the default illustration looks detached in the large workbench area.

### Decision 4: Keep the implementation feature-local

This change should not create a global "Workbench" abstraction. The catalog page has specific tree/editor density, sticky behavior, and tab layout needs. The safest implementation is to update catalog-tree owned components and CSS only.

Allowed files:

- `CatalogTreeWorkspacePage.tsx`
- `CatalogTreeEditor.tsx`
- `CatalogEditorHeader.tsx`
- `catalogTree.css`
- focused tests/snapshots if current assertions depend on old visible structure

## Risks / Trade-offs

- [Risk] Title-level chapter switching could look like static text and become undiscoverable. -> Mitigation: include a clear chevron/icon button affordance, focus styles, and accessible label/title.
- [Risk] Removing the full-width select may reduce chapter-list scanning. -> Mitigation: keep the same option labels in the overlay and allow enough width for long chapter names.
- [Risk] Sticky header/tabs offsets can regress when the separate card wrappers are removed. -> Mitigation: simplify sticky treatment first; verify selected and no-selection screenshots at common desktop widths.
- [Risk] Form sections may feel too flat after removing card borders. -> Mitigation: keep internal spacing, group separators, and subordinate framed rows/previews where they carry real structure.
- [Risk] Mojibake in terminal output can make Chinese copy hard to verify from logs. -> Mitigation: rely on source edits, tests, and browser screenshot QA rather than terminal-rendered Chinese text alone.

## Migration Plan

1. Create the OpenSpec artifacts and validate the change before implementation.
2. Replace the left panel chapter select with a title-level switcher that reuses existing chapter options and state.
3. Update `CatalogTreeEditor` empty and selected-state markup to support a single workbench surface.
4. Update `CatalogEditorHeader` classes only as needed for integrated layout; preserve actions and mutations.
5. Refactor `catalogTree.css` so the right workbench is cohesive and the left title switcher is polished.
6. Run focused admin tests/typecheck/build where available and perform browser/screenshot QA if the dev server can run.
7. Mark tasks complete as each implementation step is verified.

Rollback is frontend-only: restore the previous full-width chapter select and card-like editor CSS. No database or backend rollback is required.

## Open Questions

None for implementation. The product direction is clear: reduce duplicated chapter UI and make the right editor visually cohesive while preserving behavior.
