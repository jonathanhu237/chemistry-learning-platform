## Context

`CatalogNodeContentPanel` is reused in the main `知识内容` tab and in the `编辑内容` modal through the `variant="task"` path. The current chemical-equation authoring area correctly supports natural multiline input, backend preview, AI suggestions, candidate adoption, and inline `//` annotations, but it is presented as a two-card workbench with a full-width help banner and a separate action bar. That visual treatment makes one field feel larger than the rest of the point content form.

The change must preserve the existing data flow:

```text
multiline input
  -> debounced backend preview
  -> preview / candidates / apply candidate
  -> autosave payload derived from current input
```

## Goals / Non-Goals

**Goals:**

- Reduce the visible footprint of the chemical-equation area without removing multiline capacity or existing logic.
- Move principle mode selection and AI equation assistance into the experiment-principle header.
- Make teacher-only note, experiment principle, and student-facing content read as three related form sections.
- Keep phenomenon explanation and safety note as textarea fields with enough room for longer prose.
- Ensure the same component remains usable inside the reused edit-content modal.
- Keep implementation localized to catalog-tree editor components and CSS.

**Non-Goals:**

- Do not change backend preview, normalization, validation, AI assist, save, autosave, or hydration behavior.
- Do not change reaction equation data models, migrations, API contracts, or parser rules.
- Do not remove the preview pane, candidate adoption, AI analysis details, or inline annotation display.
- Do not introduce a new form library, global design system abstraction, or new dependency.

## Decisions

### Decision 1: Preserve behavior and compress chrome

The equation editor remains a two-pane input/preview surface on wide screens, but the panes become columns inside one compact field group rather than separate card-like sections. The full-width help banner becomes a short helper line attached to the experiment-principle section.

Alternative considered: replace the preview with a collapsed drawer. Rejected because teachers need immediate line-order feedback for many equations, and current preview logic is valuable.

### Decision 2: Put controls in the principle header

The `化学方程式 / 文字描述` selector and `AI 校对` button belong to the experiment-principle header. This keeps the action close to the field it affects and removes the separate bottom action strip from the equation editor.

Alternative considered: keep AI in the input pane footer. Rejected because it adds a second control area and makes the equation editor feel like a standalone app inside the form.

### Decision 3: Bound preview height instead of shrinking capability

Many points may have multiple reactions. The editor should keep the multiline input and preview content, but bound the preview area's height with internal scrolling so the student-facing fields are not pushed far below the fold.

Alternative considered: show only the first preview row and hide the rest behind `更多`. Rejected because line-by-line verification is central to the current workflow.

### Decision 4: Group student-facing prose fields

`现象解释` and `安全提示` remain textareas. On wide screens they can sit side by side inside a student-facing content group; in the modal or narrow layouts they stack vertically. This makes them feel like peer fields rather than leftovers after the equation workbench.

Alternative considered: convert either prose field to a smaller single-line input. Rejected because teachers may need substantial explanatory and safety text.

### Decision 5: Modal uses the same structure with tighter responsive behavior

The reused edit-content modal should not fork the component logic. It should use the same markup and switch to a stacked, non-sticky equation layout when available width is constrained or when the task-window variant is active.

Alternative considered: create a separate modal-specific component. Rejected because it would risk divergence in autosave, preview, and AI behavior.

## Risks / Trade-offs

- [Risk] Compressing the preview may make dense equation feedback harder to inspect. -> Mitigation: keep all rows available through internal scrolling and preserve candidate details.
- [Risk] Header controls could wrap awkwardly in the modal. -> Mitigation: use a responsive header that wraps controls below the label without overlapping text.
- [Risk] Moving the AI button could accidentally change behavior. -> Mitigation: keep the same `runEquationAssist` handler and loading state; only move where it is rendered.
- [Risk] Existing structure-sensitive tests may fail. -> Mitigation: update focused catalog contract assertions only where labels/classes intentionally move.
- [Risk] Compact chrome may hide the relationship between input and preview. -> Mitigation: keep explicit column labels and line-numbered preview rows.

## Migration Plan

1. Add OpenSpec delta requirements for compact point content layout and feature-local implementation.
2. Update `CatalogNodeContentPanel` markup to introduce grouped sections and move principle controls.
3. Update `catalogTree.css` to compact the equation editor, bound preview height, and support modal/narrow responsive behavior.
4. Update focused contract tests if they assert old class placement or copy.
5. Run focused catalog tests and frontend typecheck.

Rollback is frontend-only: restore the previous markup and CSS. No persisted data or backend migration is involved.

## Open Questions

None. The requested constraint is clear: preserve reaction-equation logic and reduce display footprint.
