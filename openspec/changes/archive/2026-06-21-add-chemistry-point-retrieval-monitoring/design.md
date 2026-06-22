## Context

The current Compose backend is configured for Elasticsearch through `VIDEO_LIBRARY_SEARCH_BACKEND=elasticsearch`, `VIDEO_LIBRARY_SEARCH_URL=http://elasticsearch:9200`, and `VIDEO_LIBRARY_SEARCH_INDEX=student-video-library`. The existing index mapping already uses IK analyzers for text fields and keyword fields for formulae/reaction features. The running index, however, only reflects the previous smaller point-content attempt; the normalized 76-record seed now contains 71 equation-mode point records, 5 text-mode point records, and 122 reaction-equation rows that must preserve their mode split for ES testing.

The catalog model is not a flat document list. A student-visible search hit is a point placement in a directory tree. The same canonical experiment point may appear under more than one directory path, and the directory path may legitimately change the best placement for a query. The system also has a Postgres-backed point job/outbox model: point content saves, publication changes, node moves, media bindings, and related links enqueue ES/RAG work and expose point-level index/evidence state.

Teacher-facing monitoring currently exists in fragments:

- The teacher `AI 接入` page monitors OpenAI-compatible connectivity and RAG/BGE runtime state.
- The backend exposes `/api/admin/video-library/index/diagnostics`, including ES health, document counts, sync-status counts, and analyzer dictionary asset metadata.
- The catalog point workbench exposes selected-point AI context, RAG probe, ES state, job state, and search preview.

This change makes those fragments a coherent monitoring and diagnostics capability for AI/RAG/ES retrieval.

## Goals / Non-Goals

**Goals:**
- Make the teacher monitor show AI, RAG, ES, dictionary, indexing, and retrieval-route health in one global place.
- Keep selected-point diagnostics available in the catalog workbench, but reframe them as retrieval diagnostics rather than generic AI context.
- Model ES search documents as point placements with canonical point grouping and directory context.
- Use directory matches as filters, context, and weak point recall rather than as the primary final result type for student experiment-video search.
- Separate strict chemical synonyms from reagent/formulation aliases, conditions, phenomena, and properties.
- Add equation-aware recall and ranking concepts for formulae, reactants, products, participants, equation rows, conditions, and reaction features.
- Make query diagnostics explain normalization, IK tokenization, dictionary expansion, per-route recall counts, merged ranking, and result reasons.
- Preserve teacher-only diagnostics; student APIs must not expose raw ES DSL, analyzer tokens, job payloads, rerank internals, or dictionary operational details.
- Preserve the existing Postgres-backed outbox/job model and its save-vs-publish visibility semantics.

**Non-Goals:**
- Do not make directories the default student-facing result object for experiment-video search.
- Do not import public chemical databases wholesale into ES synonym filters.
- Do not replace BGE/RAG evidence retrieval with ES search; ES search and RAG remain separate but monitored together.
- Do not expose dictionary editing to all teachers in the first iteration; dictionary assets may be read-only unless an explicit admin editing workflow is later designed.
- Do not require a chemical structure engine such as RDKit, Ketcher, or substructure search for the high-school experiment point search surface.

## Decisions

### 1. Index point placements, not only canonical points

The ES document identity remains the catalog placement node id. Each document includes:

- `placement_node_id` / `node_id`: the routeable document identity.
- `canonical_point_id`: stable experiment identity used for deduplication and smart-pointer grouping.
- `catalog_path`, `chapter_id`, and ancestor context: directory-derived filters and weak recall context.
- Student-facing point title, principle, phenomenon explanation, safety note, related point titles, videos, and chemistry terms.

Alternative considered: index one document per canonical point. That loses directory-specific context and cannot explain why a duplicate experiment should rank differently under different chapter/section searches.

### 2. Directories are recall context, not the default final search object

Directory titles and paths should be indexed into point placement documents. If a query matches a directory such as “卤素 氧化性”, the search system may recall descendant point placements and rank them with directory-path evidence. The final student experiment-video search result should still be a point/experiment learning action, not a passive directory hit, unless a separate browse/navigation result type is explicitly requested.

Alternative considered: index directories as equal result documents. That is useful for teacher tree search, but it can create dead-end or overly broad student search results and would make chemistry point ranking harder to reason about.

### 3. Chemistry vocabulary is layered

The retrieval vocabulary must distinguish:

- Strict chemical synonyms: equivalent names/forms for the same entity, such as `H2O2`, `H₂O₂`, `过氧化氢`, `双氧水`.
- Reagent/formulation aliases: experiment-use forms such as `酸性高锰酸钾溶液`, `KMnO4/H+`, and `氯水`.
- Condition terms: `酸性`, `碱性`, `加热`, `水浴`, `通风橱`.
- Phenomenon terms: `褪色`, `黄色沉淀`, `气泡`, `刺激性气体`, `分层`.
- Property terms: `氧化性`, `还原性`, `漂白性`, `酸性`, `碱性`.

Strict chemical synonyms may participate in synonym expansion for text search and query normalization. Phenomena, properties, and conditions must not be treated as strict synonyms because they describe observations or behavior, not entity equivalence.

Alternative considered: place all chemistry-adjacent words in one synonym file. That improves recall superficially but causes false high-weight matches, such as `刺激性气体` being treated as equivalent to `SO2` in a title.

### 4. Use multi-route recall with route explanations

The search query path should produce multiple candidate routes:

- Text route: title, subtitle/path, principle, phenomenon, safety, aliases, and search text through IK analyzers.
- Strict synonym route: query expansion from reviewed chemical aliases.
- Formula route: exact keyword matching on normalized formulae.
- Equation route: matching within reaction equation rows, including reactants, products, participants, and equation signatures.
- Condition/phenomenon/property route: keyword matching on controlled tags and extracted features.
- Directory route: chapter/path/ancestor matches that recall point placements under the matching context.

The final ranking should prefer complete, chemically meaningful matches over broad text matches:

1. Same equation row contains all query chemical participants.
2. Formula/participant fields contain all query chemical entities.
3. Point title exact or strict-synonym match.
4. Principle/equation display match.
5. Phenomenon/feature/property match.
6. Directory/path/search-text fallback match.

Implementation may use ES `bool.should` clauses, explicit boosts, rescoring, or a later RRF-style merge as long as diagnostics show which route contributed to each result.

Alternative considered: rely only on `multi_match` plus existing `formulae` terms. That is simpler but cannot explain or prioritize equation-row co-occurrence such as `H2O2 KMnO4`.

### 5. Global monitoring and point diagnostics have separate responsibilities

The global monitoring page should answer “is the system healthy and why do queries behave this way?” It should show:

- AI provider health and usage.
- RAG/BGE runtime status and retrieval capability.
- ES cluster/index status, document counts, index settings/analyzer metadata, and sync status.
- Dictionary assets, line counts, hashes, missing files, and dictionary categories.
- Query diagnostics for normalization, IK analysis, dictionary expansion, route counts, final ranking, and result reasons.

The point workbench diagnostics should answer “why is this selected point searchable, unsearchable, or usable by AI?” It should show:

- Student-visible point content and normalized equation rows.
- ES search preview document for the selected placement.
- ES outbox/index state and recent jobs.
- RAG evidence state, dynamic RAG probe, generated queries, candidate counts, final evidence, and failures.
- Teacher-only notes clearly separated from student-visible and indexed content.

Alternative considered: place every diagnostic in the point workbench. That makes global health and dictionary debugging hard to discover and repeats system-level status inside every point.

### 6. Preserve outbox semantics and publication safety

The existing domain flow should remain authoritative:

- Saving point content creates draft state and queues delete for active placements, so unpublished edits do not leak into student search.
- Publishing queues upsert for active placements.
- Unpublish/archive queues delete.
- Directory move/rename queues affected subtree point indexes.
- Media and related-link changes queue affected point indexes.
- Jobs are idempotent, retryable, and visible through state tables and recent job records.

The monitoring UI should describe this as final consistency rather than instant ES persistence. Manual refresh/retry actions should continue to use controlled job APIs.

Alternative considered: synchronous ES writes on every save. That would make saves slower, complicate rollback, and risk exposing drafts if publication semantics are bypassed.

## Risks / Trade-offs

- [Risk] Over-expanding synonyms can degrade ranking and create misleading title matches. → Keep strict entity synonyms separate from reagent, condition, phenomenon, and property dictionaries; expose dictionary categories in diagnostics.
- [Risk] Directory weak recall can dominate specific chemistry searches if over-boosted. → Keep path/catalog matches lower than title, equation, and formula routes; require route explanations in diagnostics.
- [Risk] One canonical point can produce multiple placement hits that look duplicated. → Support canonical grouping/deduplication while preserving placement-specific context and path explanation.
- [Risk] Query diagnostics may expose internal ES DSL, tokenization, job payloads, or raw evidence to students. → Restrict diagnostics to teacher/admin APIs and keep student responses typed and curated.
- [Risk] ES analyzer changes may require index recreation or dictionary deployment into the ES container. → Display analyzer asset hashes and mapping version; include rebuild tasks and rollback to the previous index mapping.
- [Risk] Existing local Python runs may use `VIDEO_LIBRARY_SEARCH_BACKEND=local` while Compose uses `elasticsearch`. → Surface effective backend and fallback state prominently in monitoring.
- [Risk] Equation parsing failures can remove useful formula recall. → Store raw equation text, parser warnings, validation status, and fallback extracted formulae so diagnostics can show partial recall rather than silently dropping rows.
- [Risk] The monitoring page may become too broad if it mixes operational metrics with authoring tasks. → Use tabs/sections and keep editing controls in settings or point workbench; the global page remains monitoring-first.
