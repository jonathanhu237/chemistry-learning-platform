## 1. Teacher Search Index Contract

- [x] 1.1 Add teacher catalog search configuration for enabled flag, index name, mapping version, timeout, and fallback policy without reusing student `VIDEO_LIBRARY_SEARCH_INDEX` as the teacher index.
- [x] 1.2 Define the teacher/admin Elasticsearch mapping using the existing IK analyzer assets, chemistry stopwords, chemistry custom dictionary, and synonym graph search analyzer.
- [x] 1.3 Implement a teacher search document builder for directory nodes with node id, chapter id, parent/path context, teacher note, publication/archive flags, and directory status facets.
- [x] 1.4 Implement a teacher search document builder for point placements with placement id, canonical point id, path context, teacher note, draft/published content, legacy identifiers, status facets, and chemistry-derived fields.
- [x] 1.5 Reuse backend chemistry normalization helpers to populate formulae, formula pairs, reactants, products, participants, aliases, strict aliases, reagent aliases, and annotated equation text where available.
- [x] 1.6 Add backend tests proving teacher search documents may include teacher-only/admin fields while student video-library documents still exclude those fields.

## 2. Independent Projection Fan-Out

- [x] 2.1 Decide and implement the projection job shape: either extend the existing Postgres-backed catalog point job table with target-index/job-type fields or add a dedicated teacher search job table.
- [x] 2.2 Ensure one catalog change can enqueue teacher projection work, student projection work, both, or neither according to independent visibility and data-scope rules.
- [x] 2.3 Wire point content saves so draft/unpublished edits refresh teacher search without upserting draft content into the student video-library index.
- [x] 2.4 Wire publish/unpublish/archive/restore changes so student and teacher projection jobs are queued independently with separate retry/error diagnostics.
- [x] 2.5 Wire directory title, move, reorder, archive, and restore changes so teacher path-context refreshes are queued for affected nodes and descendant point placements.
- [x] 2.6 Ensure directory changes queue student search refresh only for affected published student-visible descendant placements.
- [x] 2.7 Add tests proving teacher projection failure does not mark student projection failed, and student projection failure does not block teacher search indexing.

## 3. Backend Search API

- [x] 3.1 Replace the teacher catalog search endpoint internals with an ES-first search path against the teacher/admin index.
- [x] 3.2 Build the teacher search query planner with boosted title/path/content matches, teacher-note and legacy-id matches, chemistry synonym text routes, and structured formula routes.
- [x] 3.3 Apply selected chapter and active catalog status filter in the backend search query before limiting/ranking results.
- [x] 3.4 Return result rows with node id, node kind, title, breadcrumb, matched-field label when available, teacher status marker data, and stale-safe routing metadata.
- [x] 3.5 Return response metadata identifying `elasticsearch` versus `postgres_fallback`, index name or mapping version when appropriate, and whether ES synonym/chemistry recall was active.
- [x] 3.6 Preserve the current Postgres `ILIKE` search as a degraded fallback path and mark fallback responses explicitly.
- [x] 3.7 Add backend tests for alias/synonym search, formula search, status-filtered search, chapter-constrained search, fallback metadata, and stale-result-safe response shaping.

## 4. Teacher Frontend Search Overlay

- [x] 4.1 Update catalog tree API types and client code to consume the new search result contract and backend metadata.
- [x] 4.2 Replace the in-flow search result list with a dropdown/popover anchored to the catalog search input.
- [x] 4.3 Ensure the overlay uses absolute/floating positioning, bounded height, and scrolling so it may cover the tree but never pushes the tree downward.
- [x] 4.4 Render result rows with node type icon, title, breadcrumb path, matched-field label, and the same teacher status marker language used by the tree.
- [x] 4.5 Add keyboard and dismissal behavior: arrow navigation, Enter select, Escape close, outside-click close, query-clear reset, and chapter-change reset.
- [x] 4.6 On result selection, reveal the node through the existing tree state, expand necessary ancestors, scroll the row into view, select it, and open the existing editor.
- [x] 4.7 Add UI states for no matches, matches filtered out by the active status filter when reported, ES fallback/limited search, loading, error, and stale selected result.
- [x] 4.8 Add frontend tests or interaction coverage for overlay layout stability, result selection, dismissal behavior, status-filtered results, and fallback copy.

## 5. Operations and Validation

- [x] 5.1 Add a teacher search rebuild or bootstrap command that can recreate the teacher/admin search index from Postgres.
- [x] 5.2 Add diagnostics for teacher search index health, mapping version, analyzer asset availability, failed projection jobs, and fallback mode.
- [x] 5.3 Add ES/IK validation coverage proving required chemistry synonym/custom dictionary assets are available for teacher search.
- [x] 5.4 Update developer or operations documentation to explain the separate student and teacher search projections and their independent outbox/job status.
- [x] 5.5 Run focused backend catalog/search tests.
- [x] 5.6 Run teacher frontend typecheck and focused tests.
- [x] 5.7 Run ES/IK validation and teacher search rebuild smoke against the local Compose Elasticsearch service when search wiring changes.
- [x] 5.8 Run `openspec validate add-teacher-catalog-es-search-overlay --strict`.
