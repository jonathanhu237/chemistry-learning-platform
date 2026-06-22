## Why

The Arborist catalog tree now has the right overall direction, but the remaining row metadata and header controls still feel like implementation UI rather than a polished teacher sidebar. The tree still exposes English status text such as `published`, duplicates add entry points between the chapter header and tree header, and lacks a reliable directory-level point count like the shared Dribbble/Gmail sidebar reference.

## What Changes

- Replace raw English node status labels in the left tree with Chinese-facing status language and a compact status-dot visual system.
- Add a backend-provided recursive directory point count so each directory row can show the total number of point leaves under that directory, regardless of whether descendants are currently loaded in the client.
- Keep point rows focused on point identity and optional video completion metadata; do not reuse the directory descendant count for point rows.
- Enlarge and tune directory/experiment icons so folder and experiment-point rows read clearly at sidebar density.
- Simplify the left panel header so there is one obvious add surface for the selected chapter:
  - remove the duplicate chapter-header `目录 / 点位` add controls;
  - keep a compact tree-toolbar `+` action with a menu for `新建目录` and `新建点位`;
  - reserve any secondary actions such as refresh, expand all, or collapse all for a subtle more menu.
- Preserve the existing Arborist tree engine, drag/drop behavior, directory-vs-point split, right editor structure, stable node identity, media binding separation, and backend publication semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Tighten the sidebar tree visual contract for status display, recursive directory point counts, experiment icon sizing, and non-duplicated chapter add actions.
- `frontend-admin-maintainability`: Require the recursive count field, UI mappers, tree row rendering, header controls, and focused tests to stay within catalog feature/API boundaries.

## Impact

- Backend catalog tree read model:
  - extend node card selection and serialization with a recursive directory descendant point count;
  - ensure root, children, detail, and search/list responses expose the same field consistently.
- Admin catalog API types:
  - extend `CatalogNodeCard` with the count field.
- Admin catalog feature:
  - update tree row rendering, status mappers, tooltips, selected/hover states, icon sizing, trailing metadata layout, and tree header controls;
  - update tests so raw `published`, `draft`, and `archived` are not rendered in the visible left tree.
- Validation:
  - run OpenSpec strict validation;
  - run backend tests covering recursive count shape;
  - run admin unit/contract tests, typecheck, build, and browser screenshot QA for normal and narrow teacher sidebar widths.
