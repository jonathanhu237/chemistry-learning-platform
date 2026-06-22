## 1. Editor Structure

- [x] 1.1 Update `CatalogNodeContentPanel` so point content is grouped into teacher note, experiment principle, and student-facing content sections.
- [x] 1.2 Move the principle mode selector into the experiment-principle header and move the existing AI equation action into that header when equation mode is active.
- [x] 1.3 Preserve the current equation input, preview, AI assist, candidate adoption, and autosave handlers while changing only their rendered layout.

## 2. Compact Styling

- [x] 2.1 Replace the equation help banner and separate pane cards with compact field-group styling.
- [x] 2.2 Bound the equation preview area height and make preview rows denser without removing row order, annotations, candidates, or adoption actions.
- [x] 2.3 Present phenomenon explanation and safety note as textarea peers in a responsive student-facing content group.
- [x] 2.4 Ensure the reused edit-content modal uses non-sticky, stacked or compact behavior without crowding controls.

## 3. Verification

- [x] 3.1 Update focused catalog contract tests if they assert old layout structure.
- [x] 3.2 Run focused catalog tests.
- [x] 3.3 Run teacher frontend typecheck or an equivalent compile check.
- [x] 3.4 Run OpenSpec validation for `compact-content-equation-layout`.

## 4. Safe Principle Mode Switching

- [x] 4.1 Add confirmation before switching away from non-empty chemical-equation or text-principle content.
- [x] 4.2 Clear the discarded principle-mode fields only after confirmation so the app still saves one active mode.
- [x] 4.3 Update focused catalog contract checks for the confirmation workflow.
- [x] 4.4 Mark the destructive confirmation action as danger and clarify switch dialog button labels.
