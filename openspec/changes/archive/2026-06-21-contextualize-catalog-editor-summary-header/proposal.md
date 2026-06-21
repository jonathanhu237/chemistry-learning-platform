## Why

The selected-node summary header now has a solid visual container, but it still treats low-value metadata such as `node type` and overlapping child counts as first-class metric blocks. Teachers need the header to summarize the selected catalog object in a way that matches the experiment catalog model: directories organize learning paths, while point nodes own learning content, resources, and publication readiness.

## What Changes

- Replace the fixed five-block summary layout with contextual header summaries:
  - Directory nodes show a folder identity, publication state, and a compact structure/readiness summary.
  - Point nodes show a lab-point identity, publication state, and a resource/readiness checklist.
- Demote `目录/点位` from a large text metric to a leading icon and small semantic cue.
- Merge or hide redundant counts such as direct child count and descendant point count when they do not independently help a teacher decide what to do.
- Elevate actionable readiness signals, especially missing videos, missing learning content, related experiments, and publication check issues.
- Keep node actions, tab filtering, form save, media binding, validation, and backend API behavior unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Refine the selected-node summary header so directories and point nodes show context-specific identity, structure, resource, and readiness information instead of generic fixed metric blocks.
- `frontend-admin-maintainability`: Keep the display strategy feature-local and derived from existing catalog detail data without new API calls or broad design-system changes.

## Impact

- Affected frontend code:
  - `apps/admin-web/src/features/catalog-tree/CatalogEditorHeader.tsx`
  - `apps/admin-web/src/features/catalog-tree/catalogTree.css`
  - focused catalog editor tests if source-contract assertions need adjustment
- No backend API, database, route, auth, query key, or dependency changes are expected.
- Visual QA should cover selected directory and selected point states, including warning/readiness presentation.
