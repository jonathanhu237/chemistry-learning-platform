## Context

The product currently has two preview systems with different purposes:

- The full student-preview sandbox simulates the student app and route history.
- The catalog-tree preview is an authoring tool opened from the teacher catalog editor. It is short-lived, teacher-scoped, and currently opens only one point detail page in a phone frame.

The catalog data model already supports both `directory` and `point` nodes. A point preview is useful after a teacher selects a point, but a directory selection cannot show the student-facing second-level catalog page. That leaves teachers without WYSIWYG feedback for directory grouping, child ordering, selected-directory state, and mixed child folder/point lists.

This change generalizes catalog-tree preview from point preview to catalog node preview. Selecting a directory opens the student H5 catalog browser at that directory; selecting a point keeps opening the video/detail point page.

## Goals

- Let the teacher preview either a selected directory or a selected point from the catalog tree authoring workflow.
- Preserve the distinction between the full student sandbox and the catalog-tree authoring preview.
- Reuse real student H5 catalog/detail renderers so the preview matches the student experience instead of becoming a teacher-side mock.
- Keep preview mode read-only: no student session, learning progress, assessment, feedback, AI chat session, or analytics mutation.
- Scope preview authorization to the selected point or selected directory subtree.
- Make preview-local back/navigation behavior explicit so the point-player back action never becomes a no-op.

## Non-Goals

- This change does not replace the full student-preview sandbox.
- This change does not add student-side publishing rules or change what a real student can access.
- This change does not redesign the catalog editor tree, diagnostics panels, video binding workflow, or AI review workflow.
- This change does not enable real student AI chat or assessment from catalog-tree preview.

## Decisions

### Generalize to catalog node preview

The teacher catalog editor keeps one selected-node preview action. The backend accepts both `directory` and `point` nodes for preview-token creation. The returned preview URL SHOULD use catalog-node semantics, for example `/preview/catalog/nodes/:nodeId?preview_token=...`, while existing point preview URLs may remain as compatibility redirects or aliases.

Point nodes render the existing point detail/video preview. Directory nodes MUST render through the real student H5 second-level catalog shell (`FamilyCatalogShell`) with the selected directory injected as state, including the family/element context, breadcrumb/path context, selected-directory chip, child directories, child points, counts, and the same mobile spacing/back-arrow conventions used by the current student catalog UI. Directory preview MUST NOT fall back to an independent catalog detail panel such as `CatalogDirectoryPanel`, because that produces a separate page shape that teachers cannot treat as WYSIWYG.

### Keep the two preview systems separate

The catalog-tree node preview is an authoring preview for one selected catalog node. It should not bootstrap the full student app shell, student login state, pretest gates, or complete student route history. The full student-preview sandbox remains responsible for whole-app simulation.

### Token scope follows the selected node

Preview tokens are short-lived teacher-authorized tokens with a preview purpose and selected root node id.

- For a point token, read/media access is limited to that point.
- For a directory token, read access is limited to the selected directory and its descendants.
- Preview media access is allowed only for point media that belongs to the selected point or a descendant point of the selected directory.
- Tokens must not authorize unrelated siblings, ancestors outside the required breadcrumb context, non-preview endpoints, or normal student APIs.

### Reuse student renderers with preview loaders

The student frontend should reuse the existing catalog second-level shell and point detail components with preview-specific data loaders and `previewMode` guards. For directory preview, only route shell/data loading may be preview-specific; the visible catalog surface should be the same component path used by the real student chapter catalog page. This keeps visual behavior consistent while avoiding student mutations.

Preview loaders may include teacher-authoring draft or incomplete states so teachers can inspect what is being authored. The rendered output must still remain student-facing: placeholders are allowed, but teacher diagnostics, raw ids, AI evidence traces, and backend job details are not.

### Preview-local navigation and back behavior

Directory preview can navigate to descendants that are authorized by the token:

- selecting a child directory opens that directory in the same preview shell;
- selecting a child point opens the point detail preview;
- point back from a directory-origin preview returns to the originating directory;
- an isolated root preview with no preview-local parent should ask the shell to close or fall back to browser history.

The teacher preview iframe/shell should support this with route state or a small preview navigation stack. The point-player top-left back action must call this preview navigation contract instead of `noop`.

### Teacher editor affordance

The teacher editor preview affordance becomes selected-node preview. Point-specific actions such as video binding, related experiments, and point detail tabs remain point-only. Directory nodes gain preview support without pretending to have point-only video/detail controls.

## Risks And Mitigations

- Over-broad directory tokens could leak sibling or unrelated draft content. Mitigate with subtree checks in the preview domain and tests for sibling/ancestor rejection.
- Reusing student components could accidentally trigger student mutations. Mitigate with explicit `previewMode` props, disabled mutating actions, and tests that preview APIs do not create progress, assessment, feedback, AI, or analytics records.
- Route confusion could blur full sandbox and catalog preview behavior. Mitigate with separate preview URL prefixes and specs that name the two systems.
- Iframe back/close behavior can differ by browser. Mitigate with preview-local history first, then shell postMessage close/fallback behavior.
- Draft directory preview may differ from real student availability. Mitigate by documenting catalog-tree preview as authoring preview and keeping real student availability rules unchanged.

## Migration Plan

1. Add backend node-preview token/read support while keeping existing point preview behavior available.
2. Add student preview routes/loaders for catalog nodes and dispatch directory vs point rendering by node kind.
3. Update the teacher catalog editor preview action to be available for directory and point selections.
4. Update the preview shell/back contract so isolated preview back is never a no-op.
5. Add unit/e2e coverage for directory preview, point preview regression, token scope, non-mutating preview, and route inventory.
6. Remove or rename point-only frontend/API names only after compatibility coverage exists.
