## Baseline

Initial validation:

- `openspec validate catalog-arborist-sidebar-tree-polish --strict`: passed before implementation.

Current visual baseline captured against `http://localhost:5175/experiments`:

- `artifacts/catalog-arborist-sidebar-tree-polish/baseline-current-full.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/baseline-current-tree.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/baseline-current-tree-hover.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/baseline-directory-second-tab-visible.png`

Baseline summary:

- Current directory selection exposes 6 editor tabs, including point-only tabs.
- Current tree rows show the detached Ant Design switcher/indent system mixed with feature-owned row visuals.
- Baseline Playwright diagnostics had no console, page, or failed-request errors.

Current catalog feature file sizes before this pass:

- `CatalogTreeNodeList.tsx`: 142 lines. Owns Ant Design Tree wrapper, lazy child loading, selected keys, drop handling, and row title rendering.
- `CatalogTreeRow.tsx`: 109 lines. Owns row icons, drag grip, status/action layout, and row menu.
- `catalogTreeData.ts`: 132 lines. Owns Ant Design tree data, drop resolution, parent/sibling lookup, descendant checks, and fallback reorder.
- `catalogTree.css`: 443 lines. Owns workspace, Ant Design tree skin, editor panels, and responsive layout.
- `CatalogTreeEditor.tsx`: 189 lines. Owns selected editor orchestration, form hydration, tab list, media/query gating, and point-title save sync.

## Visual Target

The target is the user-provided Dribbble Sidebar Navigation Tree reference at `https://dribbble.com/shots/26899749-Sidebar-Navigation-Tree`, with `react-arborist`'s Gmail/sidebar demo accepted as the practical open-source behavior/quality reference.

Implementation must not copy proprietary Dribbble assets. It should reproduce the interaction and layout language with feature-owned CSS and open-source icons:

- soft nested guide lines;
- compact sidebar rows;
- chevron attached to directory icon;
- point rows aligned through a leaf spacer;
- folder icons for directories;
- chemistry experiment icons for point rows;
- full-row rounded selected state;
- subtle hover and trailing row actions;
- no always-visible six-dot drag grips.

## Ownership Plan

- `CatalogTreeNodeList.tsx`: Arborist adapter/orchestrator for selection, open/lazy load, move/reorder, and row renderer wiring.
- `CatalogTreeRow.tsx`: sidebar row renderer and icon/action mapping, or a compatibility export to new Arborist row modules.
- `catalogTreeData.ts`: Arborist data shape, lazy merge helpers, lookup helpers, and move/reorder payload mapping.
- `catalogTree.css`: feature-local Arborist/sidebar tree skin and editor tab/filtering polish.
- `CatalogTreeEditor.tsx`: selected-node tab filtering and point-only query gating.

## Dependency Setup

Installed admin frontend dependencies:

- `react-arborist@3.10.5`
- `lucide-react@1.21.0`

`npm install` completed successfully. npm emitted a Windows cleanup warning for a Rollup optional native package directory, but package installation and lockfile updates succeeded. `npm run validate:boundaries` passed after adding checks that keep `react-arborist` and `lucide-react` imports scoped to catalog tree modules.

## Implementation Summary

- Replaced the Ant Design Tree behavior path with `react-arborist` in `CatalogTreeNodeList.tsx`.
- Added an Arborist data adapter in `catalogTreeData.ts` with stable `id/name/kind/catalogNode/loaded/children` nodes, lazy child merge, lookup helpers, invalid-drop checks, same-parent reorder payloads, and cross-parent move payloads.
- Rebuilt `CatalogTreeRow.tsx` as a sidebar-style Arborist node renderer using `lucide-react` folder and `FlaskConical` icons. Directory chevrons sit immediately before folder icons; point rows reserve the same spacer and use experiment-specific icons.
- Removed the always-visible six-dot drag handle. Rows are draggable through Arborist; hover/selected actions are compact and feature-local.
- Changed directory child creation to a single `+` dropdown for child directory/point, and changed top-level wording to "添加到本章".
- Filtered editor tabs by node kind. Directories show only content, student-card, publish-checks, and advanced; points keep content, video, related, student-card, publish-checks, and advanced.
- Gated media-asset and related-point search queries so directory nodes do not fetch point-only data.

## Browser QA

Final QA used the Vite dev server at `http://localhost:5175/experiments` and a local-only smoke admin created inside the backend container:

- username: `codex_smoke_admin`
- purpose: browser screenshot/smoke validation only

Screenshots:

- `artifacts/catalog-arborist-sidebar-tree-polish/qa-full.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-tree-panel.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-tree-hover-actions.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-tree-expanded.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-directory-editor.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-point-editor.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-tree-narrow.png`
- `artifacts/catalog-arborist-sidebar-tree-polish/qa-summary.json`

QA checks from `qa-summary.json`:

- directory tab text: `内容 / 学生卡片 / 发布检查 / 高级`
- directory has no `视频` tab: passed
- directory has no `相关实验` tab: passed
- point tab text: `内容 / 视频 / 相关实验 / 学生卡片 / 发布检查 / 高级`
- point has `视频` tab: passed
- point has `相关实验` tab: passed
- first 11 visible rows had no detected icon/title/trailing/actions overlap

Drag cursor screenshots were not captured because reliable automated drag screenshots would risk mutating ordering in the shared local database. The Arborist move/drop behavior is covered by focused data-adapter tests and the invalid-drop code path.

Observed non-blocking QA diagnostic:

- `sysu-logo.svg` had two aborted requests during navigation/login screenshot setup. No page errors were emitted, and the catalog page itself rendered successfully.

## Final Validation

Commands run successfully:

- `openspec validate catalog-arborist-sidebar-tree-polish --strict`
- `openspec validate --all --strict --no-interactive`
- `git diff --check`
- `npm run typecheck`
- `npm test`
- `npm run validate:boundaries`
- `npm run build`
- `npm run build:report`
- `E2E_BASE_URL=http://localhost:4175 E2E_API_BASE_URL=http://localhost:8000 E2E_ADMIN_USERNAME=codex_smoke_admin E2E_ADMIN_PASSWORD=codex-smoke-12345 npm run e2e:smoke`

`git diff --check` emitted only Windows line-ending warnings and no whitespace errors.

Final production chunk report:

- `CatalogTreeWorkspacePage-DTvH4qtX.js`: 175.9 KB, gzip 47.0 KB
- `CatalogTreeWorkspacePage-x1Dd_LaG.css`: 8.3 KB, gzip 2.1 KB
- existing large chunks remain `charts-vendor` and `antd-vendor`; Arborist/lucide stayed scoped to the catalog lazy page path rather than a broad app-wide boundary.

Production preview smoke:

- preview base URL: `http://localhost:4175`
- smoke result: passed for `/overview`, `/experiments`, `/videos`, `/learning-assistant`, `/question-banks`, and `/analytics`
- diagnostics: no console warnings/errors, no 404s, no failed requests, no page errors
