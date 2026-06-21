## Context

The catalog workspace now has a cleaner left chapter switcher and a unified right editor shell, but the selected-node header still exposes object identity as small chips followed by a repeated title. The active form body can repeat the same title again, and the Ant Design tabs read as loose text labels instead of a workbench-level view switcher.

The user-provided reference points to a stronger pattern: a title summary card with the selected object name and large information blocks. This maps well to established interface guidance:

- Material Design cards summarize content and actions for a single subject.
- Material tabs organize related but distinct content areas.
- Apple tab views present mutually exclusive panes in the same area, while segmented controls work well for small sets of view options.

For this page, the selected catalog node is the single subject. Its status, type, child count, video count, and validation count should support the title rather than appear as tiny labels above it. The form switcher should feel attached to the selected-node workbench and strong enough to represent switching between editor panels.

## Goals / Non-Goals

**Goals:**

- Present the selected directory or point with a title summary card: prominent title, subtle breadcrumb, action group, and readable information blocks.
- Remove visually duplicated title treatment inside the active content panel when the title is already established by the summary card.
- Upgrade editor tab navigation into a polished workbench switcher for mutually exclusive panels.
- Keep directory-vs-point tab availability, form state, save behavior, publication actions, validation, and media binding unchanged.
- Keep implementation feature-local in catalog tree editor components and CSS.

**Non-Goals:**

- Do not change catalog data models, publication rules, or backend APIs.
- Do not redesign the left tree beyond preserving the existing chapter-title switcher.
- Do not introduce a new global admin design system, theme override, or third-party UI library.
- Do not convert every editor form into new reusable card components in this pass.
- Do not change student H5 behavior.

## Decisions

### Decision 1: Use a title summary card instead of status chips

`CatalogEditorHeader` will become a summary-card header. The selected node title remains the dominant element. Status/type/count details move into readable information blocks below or beside the title, depending on available width. Archive/restore, publish, and preview actions remain in the same header area.

This follows the user's reference image and matches card guidance: the header summarizes one selected subject and its related actions. Chips remain optional for secondary inline metadata elsewhere, but they should not carry the main object identity in this workbench.

Alternatives considered:

- Enlarge the current tags: rejected because it keeps the same weak information hierarchy.
- Keep title in the content form and shrink the header: rejected because the selected object should anchor the whole editor, not only one panel.
- Move status into a global toolbar: rejected because it separates status from the object it describes.

### Decision 2: Treat editor panels as tab views, not loose labels

The existing Ant Design `Tabs` behavior can stay, but CSS should make the navigation read as a workbench switcher: contained track, active segment, stronger affordance, and stable spacing. This borrows from Apple tab-view/segmented-control patterns for mutually exclusive panes and Material's tab grouping guidance.

The implementation should keep `activeKey`, filtered tab items, and tab labels intact so behavior and tests remain stable.

Alternatives considered:

- Replace `Tabs` with a custom segmented control: rejected because it would add behavior risk for little gain.
- Keep underline-only tabs: rejected because the user specifically identified the selected-form switcher as a major visual problem.
- Put every panel in separate cards: rejected because it recreates the disconnected-card feel.

### Decision 3: Remove duplicate body title only from the directory content panel

The directory basics panel currently starts with a title heading that duplicates the selected-node title directly above it. This pass will keep the editable form label (`目录标题`) but remove or soften the redundant panel H2. Other panels may keep their own section headings where they describe a distinct form purpose, such as student card copy or publication checks.

Alternatives considered:

- Remove all form headings: rejected because some panels need task context.
- Keep all headings unchanged: rejected because it leaves the exact title repetition the user called out.

### Decision 4: Keep the change feature-local

All presentation changes should stay in:

- `CatalogEditorHeader.tsx`
- `CatalogTreeEditor.tsx`
- `CatalogNodeContentPanel.tsx`
- `catalogTree.css`
- focused catalog tests if visible structure changes

No route shell, backend, or global theme changes are required.

## Risks / Trade-offs

- [Risk] The summary card could become too tall and reduce form space. -> Mitigation: use compact metric blocks and responsive wrapping, not oversized marketing-card spacing.
- [Risk] Long chemical titles could collide with action buttons. -> Mitigation: allow wrapping and place actions in a flexible group with stable minimum sizes.
- [Risk] Stronger tab styling could look like nested cards. -> Mitigation: style the tab nav as one internal switcher band attached to the workbench, with the content remaining unframed.
- [Risk] Tests that query old heading text may need adjustment. -> Mitigation: keep form labels stable and update only structure-sensitive assertions.

## Migration Plan

1. Validate the OpenSpec change before implementation.
2. Update `CatalogEditorHeader` markup to render the title summary card and information blocks.
3. Update `CatalogTreeEditor` tab class/structure only as needed for the workbench switcher.
4. Remove the duplicated directory content heading from `CatalogNodeContentPanel` while preserving editable title fields.
5. Refine feature-local CSS for summary card, info blocks, action alignment, and tab switcher.
6. Run focused catalog tests, typecheck, OpenSpec validation, and browser visual QA for selected directory/point states.

Rollback is frontend-only: restore the old header chip row and tabs CSS. No data migration is required.

## Open Questions

None. The implementation direction is clear from the user's reference and the prior exploration.
