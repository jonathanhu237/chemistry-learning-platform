## Why

Teachers need catalog search to behave like an authoring assistant inside the chapter tree, while students need a safe published learning-content search. The current teacher tree search is only a Postgres `ILIKE` lookup despite placeholder copy that implies broader content search, and it cannot use the Elasticsearch IK synonym and chemistry-recall capability already required for student search.

The teacher and student search projections have different data boundaries: teacher search must include draft/unpublished catalog nodes, directory nodes, teacher notes, legacy identifiers, status facets, and admin-only context; student search must remain limited to published student-visible placement documents. This change defines a separate teacher catalog search projection and a non-disruptive overlay result UI so the tree remains the navigation source of truth.

## What Changes

- Introduce an Elasticsearch-backed teacher catalog admin search projection that is separate from the student video-library search index.
- Reuse the existing ES/IK service, chemistry dictionaries, synonym graph search analyzer, formula normalization, and multi-route chemistry recall approach where appropriate.
- Index teacher/admin search documents for both directory nodes and point placements, including chapter/path metadata, node status facets, draft/unpublished fields, teacher-only notes, legacy identifiers, and chemistry-derived structured fields.
- Keep the student video-library index unchanged as a published, student-visible placement projection; do not add teacher-only fields to the student ES document.
- Replace the current in-flow search result rendering with a dropdown/popover anchored to the catalog search input. The overlay may cover the tree temporarily but MUST NOT push the tree downward.
- Preserve the accepted status-filter semantics: the active status filter narrows teacher search results, and result selection reveals and selects the matching node in the tree.
- Add controlled fallback behavior when ES is unavailable: use the existing deterministic Postgres search as a degraded teacher search path and label the response so the frontend does not imply synonym recall is active.

## Capabilities

### New Capabilities

- `teacher-catalog-admin-search`: Defines teacher-only catalog search indexing, query semantics, ES/Postgres fallback behavior, search result contract, and overlay interaction.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Refine catalog tree search interaction so results are shown in an anchored overlay rather than inserted into the tree flow, and selecting a result reveals the node in the existing tree/editor workspace.

## Impact

- Affected backend code:
  - `server/app/domains/catalog_tree/search.py` and related admin catalog router/schema code.
  - New or extended catalog teacher search index builder/sync service under catalog tree domain ownership.
  - Reuse or shared extraction helpers from `server/app/chemistry_search.py` and the student search query planner where ownership permits.
  - ES index bootstrap/diagnostic scripts and validation coverage for teacher/admin search.
- Affected teacher frontend code:
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx`
  - `apps/web-teacher/src/features/catalog-tree/CatalogTreeNodeList.tsx`
  - `apps/web-teacher/src/features/catalog-tree/catalogTreeMappers.ts`
  - `apps/web-teacher/src/api/catalogTree.ts`
  - `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
- Affected operations:
  - Existing Compose Elasticsearch service remains required for production-like search.
  - Teacher admin search needs its own index name, mapping version, rebuild command or job path, diagnostics, and fallback policy.
- No new third-party service is expected; the change uses the existing Elasticsearch/IK dependency.
