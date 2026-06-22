## Context

The teacher catalog workbench currently has a search box whose placeholder implies search across title, learning content, teacher note, and legacy experiment id. The implementation is a lightweight backend search under the admin catalog API: it constrains by chapter, uses Postgres `ILIKE`, returns flat matching nodes, and the frontend applies the active status filter before rendering results above the tree. This is useful as a fallback, but it does not provide IK segmentation, chemistry synonyms, formula-aware ranking, or the richer search behavior teachers expect while editing catalog content.

The student video-library search is already an Elasticsearch projection with IK analysis and chemistry dictionaries. Its boundary is intentionally narrow: it indexes published student-visible point placements only, excludes teacher-only notes, excludes draft/unpublished content, excludes raw media resource labels, and treats directories only as path/category context for descendant point documents. That boundary must remain intact.

The teacher search problem is different. Teachers need to find draft and unpublished nodes, directory nodes, point placements, old ids, teacher remarks, chemical equations, aliases, status-filtered work items, and reused canonical points from within the current chapter tree. Search results are a navigation aid for the tree/editor, not a student learning result page.

Product research also points toward a transient search overlay rather than inserting results into the main tree flow. Apple and Material search patterns keep suggestions/results anchored to the search field and let the user commit a result before changing the main content. In this workbench, the search remains in the directory-tree context, so the result panel may temporarily cover the tree, but it must not push the tree down or reflow the authoring workspace.

## Goals / Non-Goals

**Goals:**

- Provide teacher catalog search with Elasticsearch-backed IK segmentation, chemistry synonyms, and formula-aware recall.
- Keep teacher/admin search and student search as separate Elasticsearch projections with separate mappings, index names, document scopes, sync states, and diagnostics.
- Preserve the existing accepted status-filter semantics: active filters narrow the matching result set and use the same status model as the tree.
- Render search results in a dropdown/popover anchored to the catalog search box, without changing tree layout height.
- Let result selection reveal the matching node in the authoritative tree and open the existing editor.
- Keep Postgres search as a controlled fallback when teacher ES is unavailable or disabled.
- Make index sync and diagnostics explicit enough that developers can tell whether teacher ES, student ES, or Postgres fallback answered a query.

**Non-Goals:**

- Do not change the student video-library index scope or expose teacher-only fields to students.
- Do not replace the tree with an ES-backed tree. Postgres remains the authoritative catalog structure and editor state.
- Do not make search results edit nodes directly; they only navigate/reveal/select.
- Do not introduce a new search service dependency beyond the existing Elasticsearch/IK service.
- Do not implement global admin-site search; this is scoped to the current chapter catalog workbench.
- Do not require search results to include AI/RAG evidence or canonical chunk content.

## Decisions

### Decision 1: Create a separate teacher catalog admin search index

Create a new teacher/admin Elasticsearch projection, for example `teacher-catalog-admin-search-v1`, instead of adding admin fields to the student video-library index.

The teacher index will represent both directory nodes and point placements. Documents should include:

- stable routing identifiers: `node_id`, `node_kind`, `chapter_id`, `parent_id`, `canonical_point_id` when applicable
- tree context: title, summary, breadcrumb/path text, ancestor titles, display order context when useful
- teacher/admin fields: directory or point teacher note, draft/unpublished content, legacy experiment id, legacy point key, migration aliases
- status facets: primary state, missing-field keys, video/content/readiness facets, publication/archival flags, sync-attention facets
- chemistry fields for points: raw and normalized reaction rows, formulae, formula pairs, reactants, products, participants, aliases, strict aliases, reagent aliases, condition/phenomenon/property tags
- result display fields: compact title, path, matched-field labels, and enough metadata for the frontend to render a row without reading ES internals

Alternative considered: reuse the student index and add hidden admin fields. Rejected because it violates the student search boundary, risks leaking teacher-only notes, and cannot represent directories or drafts correctly.

Alternative considered: keep Postgres only and expand query terms in the app. Rejected as the primary path because teachers need IK segmentation and synonym behavior that already exists in ES; Postgres remains valuable only as fallback.

### Decision 2: Search documents are read models, not authoritative catalog data

The teacher ES document is a denormalized read model derived from Postgres. It must not become the source of truth for tree hierarchy, content saves, publication state, media binding, or canonical point identity.

The teacher frontend must use ES search responses for candidate rows only. When a teacher selects a result, the app must load or reveal the node through the existing catalog tree API and editor state. If ES contains a stale hit, the reveal step should handle "not found, archived, or no longer in current chapter" as a controlled stale-result state.

Alternative considered: let ES return the tree slice and render it directly. Rejected because the tree supports editing, movement, ordering, ancestor expansion, and status aggregation that are owned by Postgres services.

### Decision 3: Query planning combines ES text synonyms with structured chemistry routes

Teacher search should reuse the same analyzer assets as student search: IK tokenization, chemistry custom dictionary, stopwords, and `synonym_graph` search analyzer backed by the chemistry synonym file. The query planner should also reuse chemistry normalization helpers for formula extraction and strict alias expansion.

The ES query should combine:

- high-boost exact/phrase matches for node title and point title
- text matches over path, directory context, teacher note, principle, phenomenon, safety, and legacy labels
- structured keyword matches over formulae, formula pairs, participants, reactants, products, aliases, and equation rows
- optional highlight/matched-field information for result row labels
- ES filters for `chapter_id`, node kind where requested, archive visibility, and the active status filter

The active status filter must be applied in the backend/ES request, not only after the frontend receives results. The frontend may still defensively apply the same matcher, but backend filtering is required so counts, top-N ranking, and empty states are meaningful.

Alternative considered: rely only on analyzer text fields. Rejected because formula search needs exact normalized routes; generic tokenization is not enough for terms like `SO3^2-`, `Na2S2O3`, or multiple reagents in one equation row.

### Decision 4: Fan out one catalog change into independent projection jobs

Catalog saves, publication changes, moves, archive/restore actions, directory title changes, point content edits, and video binding changes are Postgres facts. A fact may affect both student and teacher search, but the ES outbox must not be modeled as one job that writes both indexes atomically.

Use either separate job types in the existing Postgres-backed job/outbox table or a dedicated teacher-search job table. The important contract is:

- one catalog change may enqueue a student projection job, a teacher projection job, both, or neither
- student projection jobs apply student-visible rules and upsert/delete published placement documents
- teacher projection jobs apply admin-visible rules and upsert/delete teacher catalog search documents
- each projection target has its own sync status, retry count, error message, diagnostics, and rebuild command
- failure in teacher search indexing must not mark student search indexing failed
- failure in student search indexing must not hide teacher search results when the teacher index is healthy

Directory changes require special care. A directory title or position change may update the teacher directory document and may also require reindexing descendant teacher point documents because path text changes. It may also require student descendant placement refresh, but only for published student-visible placements. These are separate projection fan-outs from the same underlying change.

Alternative considered: a single "catalog ES sync" job that writes both indexes. Rejected because the data scopes, visibility rules, and retry semantics differ. Coupling them would either leak teacher fields to students or make admin search fail because a student-only rule blocked a document.

### Decision 5: Use an anchored overlay for result display

The teacher search UI should render a floating dropdown/popover anchored to the search field:

- It opens when the trimmed query reaches the configured minimum length or when a recent query has results.
- It is positioned over the tree area with bounded height and scrolling.
- It must not insert result rows into the normal tree DOM flow or push the `章节目录树` content down.
- It closes on Escape, outside click, query clear, chapter change, or successful result selection.
- It keeps keyboard navigation: up/down changes active result, Enter selects, Escape closes.
- Selecting a result expands the needed ancestor path, scrolls the tree row into view, selects the node, and opens the existing editor.

The overlay header may show compact context such as `当前章节`, active filter label, backend source (`ES` or degraded fallback), and result count. Rows should show node type, title, breadcrumb, matched field label, and the same status marker language used by the tree.

Alternative considered: keep the current inline result list above the tree. Rejected because it changes the tree layout while searching and makes search results feel like a second tree rather than a temporary navigation aid.

### Decision 6: Fallback is explicit and product-safe

When teacher ES is disabled, unavailable, empty, or fails a query, the backend may fall back to the current Postgres search. The response must include metadata such as `backend: "elasticsearch"` or `backend: "postgres_fallback"` and whether synonym/chemistry ES recall was active.

The frontend should adjust helper copy or a subtle status line accordingly. It must not claim synonym search is active during fallback. Empty states should distinguish:

- no matches in the current chapter/filter
- matches exist before the active status filter but none survive it, if the backend can cheaply report this
- ES unavailable and fallback returned limited results

Alternative considered: silently fall back to Postgres. Rejected because teachers would be confused when ES-only synonyms do not work.

### Decision 7: Keep student and teacher diagnostics separated

Teacher search diagnostics may show ES route reasons, analyzer terms, matched fields, stale projection state, and legacy ids. Student search responses must continue hiding these internals.

Admin diagnostics should answer:

- which backend answered the query
- which index and mapping version were used
- whether analyzer assets and synonym files are available
- whether a selected node has stale or failed teacher-search projection state
- whether a result came from title, path, equation, teacher note, legacy id, or synonym expansion

Alternative considered: extend student video-library diagnostics for teacher search. Rejected because the projection scope and privacy boundary differ.

## Risks / Trade-offs

- [Risk] Two ES projections add operational complexity. -> Mitigation: keep one Elasticsearch service but separate index names, mapping versions, rebuild commands, and status records.
- [Risk] Directory edits can create large descendant reindex fan-out. -> Mitigation: enqueue idempotent projection jobs by target index and node id; batch descendant refreshes and cap duplicate pending jobs.
- [Risk] Teacher search could expose admin-only data through the wrong API. -> Mitigation: keep teacher index endpoints under admin auth only, never query teacher index from student APIs, and add tests that student documents exclude teacher-only fields.
- [Risk] ES can be stale immediately after an autosave. -> Mitigation: preserve Postgres as source of truth on selection/reveal, show projection status in diagnostics, and use near-real-time teacher upserts after commit where practical.
- [Risk] Formula and synonym behavior can diverge from student search over time. -> Mitigation: reuse analyzer assets and shared chemistry normalization helpers, with separate tests for teacher query payloads.
- [Risk] Overlay positioning can collide with the tree scroll container. -> Mitigation: anchor the overlay to the search wrapper, give it a fixed max height, preserve keyboard navigation, and verify desktop and constrained widths.

## Migration Plan

1. Add teacher catalog search configuration: enabled flag, index name, mapping version, timeout, and fallback policy. Default local development may fall back when ES is disabled; production-like runs should prefer ES.
2. Add teacher/admin search mapping using existing ES/IK analyzer assets plus teacher-specific fields and status facets.
3. Add a teacher search document builder from catalog Postgres state for directories and point placements.
4. Add projection fan-out: catalog changes enqueue independent student and teacher ES jobs as required by visibility and data-scope rules.
5. Add rebuild/diagnostic commands or endpoints for the teacher search index.
6. Replace the admin catalog search endpoint internals with ES-first teacher search plus Postgres fallback metadata.
7. Update the teacher frontend API types and render search results in an anchored overlay.
8. Add tests for index document purity, query semantics, status filters, fallback metadata, overlay behavior, and result reveal.
9. Run OpenSpec strict validation, focused backend tests, teacher frontend typecheck/tests, ES/IK validation, and a compose smoke path when index wiring changes.

Rollback is safe because Postgres remains authoritative. If teacher ES causes problems, disable the teacher search ES flag and fall back to the existing Postgres search endpoint while keeping the student index unchanged.

## Open Questions

- The exact teacher index name and environment variable names can be chosen during implementation, but they must remain distinct from `VIDEO_LIBRARY_SEARCH_*` student settings.
- The implementation can either extend the existing catalog point job table with target-index/job-type fields or add a dedicated teacher search job table. The chosen shape must preserve independent status and retry semantics.
