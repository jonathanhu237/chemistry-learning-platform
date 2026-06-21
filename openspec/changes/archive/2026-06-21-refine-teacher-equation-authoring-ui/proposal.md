## Why

The current multi-equation editor technically satisfies backend normalization requirements, but its teacher-facing UI feels like a loose toolbar plus blank form rather than a chemistry authoring surface. Teachers need a simpler flow modeled after lightweight mhchem/ChemType-style entry: type plain equations, insert common chemistry symbols when needed, see an inline normalized preview, and keep advanced parser details out of the main path.

## What Changes

- Replace the flat equation helper toolbar with a compact equation authoring area centered on per-equation cards.
- Provide each equation row with raw input, inline backend-normalized preview/status, and row-level reorder/delete actions.
- Move common chemistry snippets into a grouped popover/dropdown instead of permanently occupying the page.
- Rename the teacher action from backend-oriented wording such as “后端预览” to product wording such as “检查”.
- Keep the frontend assistive only: it submits raw teacher text and displays backend preview/save responses without becoming the authoritative parser.
- Preserve the text-principle path and required point content fields without adding a heavy structure/reaction drawing dependency.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Point content equation authoring must present a teacher-friendly, card-based, Chinese UI that keeps backend-normalized previews visible without exposing backend implementation language as the main workflow.

## Impact

- `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
- `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
- `apps/web-teacher/src/features/catalog-tree/catalogTreeContracts.test.ts`
- No new third-party chemistry editor dependency.
- No backend schema/API contract change expected; existing preview/save normalization remains authoritative.
