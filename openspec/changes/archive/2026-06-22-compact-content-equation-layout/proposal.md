## Why

The point knowledge content editor currently makes the reaction-equation workbench visually dominate the form, while phenomenon explanation and safety note look like unrelated fields beneath it. Teachers need the existing multiline equation logic to remain intact, but the overall page and reused edit-content modal need a more compact, scan-friendly form layout.

## What Changes

- Reframe the point content editor as grouped authoring sections: teacher-only note, experiment principle, and student-facing content.
- Keep chemical-equation mode, natural multiline input, backend preview, AI assistance, suggestion adoption, annotation suffixes, autosave, and save payload behavior unchanged.
- Move the principle mode selector and AI equation action into the experiment-principle header area.
- Replace the current two-card equation workbench with a compact single-field layout that uses lighter pane chrome, reduced helper copy, bounded preview height, and denser preview rows.
- Allow phenomenon explanation and safety note to remain textarea fields while presenting them as a coherent student-facing content group, using two columns on wide surfaces and one column in constrained/modal layouts.
- Apply the compact layout to both the main knowledge-content tab and the reused edit-content modal.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Tightens point knowledge content form layout requirements so reaction-equation authoring remains capable but no longer visually overwhelms the form.
- `frontend-admin-maintainability`: Clarifies that this presentation refinement stays inside catalog-tree owned editor modules and styles.

## Impact

- Affected frontend code:
  - `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
  - `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
  - focused catalog tree contract tests if structure-sensitive assertions need updating
- No backend API, schema, migration, equation normalization, AI assist contract, or save payload changes.
- No new dependencies.
