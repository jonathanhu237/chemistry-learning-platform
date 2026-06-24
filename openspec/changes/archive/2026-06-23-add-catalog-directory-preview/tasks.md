## 1. Backend Preview Domain

- [x] 1.1 Generalize the teacher preview-token domain from point-only preview to catalog node preview while preserving existing point preview behavior.
- [x] 1.2 Encode preview token scope with selected root node id, selected node kind, preview purpose, teacher identity fields, and expiry.
- [x] 1.3 Implement directory-scoped preview reads that return a student-catalog-compatible directory payload for the selected directory and authorized descendants.
- [x] 1.4 Keep point-scoped preview reads compatible with the existing student point detail payload and existing point preview URL behavior.
- [x] 1.5 Enforce subtree authorization so a directory token can read only the selected directory and descendants, while a point token can read only that point.
- [x] 1.6 Extend preview media authorization so media is allowed only for the selected point or descendant points inside the selected directory scope.
- [x] 1.7 Register the new or generalized catalog node preview routes in the canonical route inventory without introducing FastAPI/runtime imports into domain modules.
- [x] 1.8 Add backend tests for directory token creation, point token regression, subtree rejection, point-scope rejection, media scope, expired tokens, and route inventory.

## 2. Student Preview Routes

- [x] 2.1 Add a student frontend catalog node preview route, such as `/preview/catalog/nodes/:nodeId`, that accepts `preview_token` and dispatches by returned node kind.
- [x] 2.2 Preserve the existing `/preview/catalog/points/:nodeId` point preview path as a compatibility route, redirect, or alias.
- [x] 2.3 Add preview data loaders for catalog directory payloads and point detail payloads without requiring student login or normal student session state.
- [x] 2.4 Reuse the real student second-level catalog shell (`FamilyCatalogShell`) for directory preview, including family/element header, selected-directory state, child folder/point list, breadcrumb/path context, search/more controls where applicable, and counts; do not render an independent `CatalogDirectoryPanel` preview surface.
- [x] 2.5 Reuse the real student point detail/player renderer for point preview and keep the current video/title/content layout intact.
- [x] 2.6 Replace preview `noop` back behavior with preview-local navigation: child point back returns to directory, child directory back returns to parent preview context, and isolated root back asks the shell to close or falls back to browser history.
- [x] 2.7 Guard preview mode so finish learning, assessment, feedback, real AI chat sessions, student progress, and analytics mutations are hidden, disabled, or routed to non-mutating preview notices.
- [x] 2.8 Add student frontend tests for directory preview rendering, child navigation, point preview regression, back behavior, and mutation guards.

## 3. Teacher Catalog Editor

- [x] 3.1 Update the selected-node preview affordance so `鬚・ｧ亥ｭｦ逕溽ｫｯ` is available for both directory and point nodes.
- [x] 3.2 Keep point-specific editing controls unavailable for directory nodes, including video binding, point detail editing, related experiments, and learning-card-only controls.
- [x] 3.3 Update the teacher preview token request and preview shell URL handling to consume catalog node preview URLs returned by the backend.
- [x] 3.4 Update the `/catalog-preview` phone-frame shell title/copy so it works for directory and point previews without implying point-only content.
- [x] 3.5 Add teacher frontend tests for directory preview action visibility, point preview regression, directory point-control absence, preview shell URL handling, and blocked-popup fallback.

## 4. Verification

- [x] 4.1 Run backend tests covering catalog preview token/read/media routes and route inventory.
- [x] 4.2 Run `apps/web-student` typecheck, focused tests, and build for preview route changes.
- [x] 4.3 Run `apps/web-teacher` typecheck, focused tests, and build for catalog editor and preview-shell changes.
- [x] 4.4 Manually verify a teacher catalog point preview still opens the video/detail page in the phone frame.
- [x] 4.5 Manually verify a teacher catalog directory preview opens the student H5 second-level directory page with the selected directory, child directories, child points, counts, and mobile layout.
- [x] 4.6 Manually verify preview back behavior does not no-op in isolated point preview or directory-origin point preview.

