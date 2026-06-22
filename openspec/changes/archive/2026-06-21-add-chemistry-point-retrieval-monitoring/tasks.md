## 1. Baseline and Import Contract

- [x] 1.1 Confirm Compose and local effective search backends, ES index name, analyzer settings, fallback behavior, and current diagnostic API output.
- [x] 1.2 Snapshot the current `student-video-library` mapping, document count, published point-content count, sync-status counts, and representative query rankings before changes.
- [x] 1.3 Finalize the normalized 76-record import contract, preserving text-mode principles, equation-mode principles, reaction rows, raw equations, normalized equations, warnings, and source provenance.
- [x] 1.4 Define the replacement plan for the incorrect previous 30-record seed attempt so the new import does not flatten equation-mode principles into ordinary text.

## 2. Chemistry Data and Dictionary Assets

- [x] 2.1 Define the point-placement search document schema with placement node id, canonical point id, chapter id, catalog path, student-visible three-element content, videos, related text, aliases, formulae, reaction rows, and feature fields.
- [x] 2.2 Split chemistry vocabulary assets into strict chemical synonyms, reagent/formulation aliases, condition terms, phenomenon terms, property terms, IK custom dictionary terms, and stopwords.
- [x] 2.3 Implement or update formula normalization so ASCII formulae, Unicode-subscript formulae, Chinese names, common names, and reviewed aliases can map to canonical chemistry entities where appropriate.
- [x] 2.4 Keep phenomenon, property, and condition terms out of strict synonym expansion, while still making them available as lower-risk recall and diagnostic feature terms.
- [x] 2.5 Add dictionary metadata collection for category, logical source, file path, line count, hash/version, missing-file state, and whether the asset affects app normalization or ES/IK analysis.

## 3. ES Mapping and Multi-Route Retrieval

- [x] 3.1 Extend the ES mapping for point placements with structured keyword/text fields for canonical identity, placement identity, catalog path, aliases, formulae, reactants, products, participants, equation rows, conditions, phenomena, properties, and reaction features.
- [x] 3.2 Update indexing to emit one document per active published point placement and include directory-derived context without making directories default student result documents.
- [x] 3.3 Build a chemistry-aware query planner with separate routes for text, strict synonyms, exact formulae, equation-row co-occurrence, condition tags, phenomenon/property tags, directory context, and fallback search text.
- [x] 3.4 Tune ranking so same-equation-row and participant-set matches outrank broad text matches, direct title or strict-synonym matches outrank phenomenon-only matches, and directory/path matches remain supporting evidence.
- [x] 3.5 Preserve student-facing search response shape while carrying internal route reasons, ES score, and ranking explanations for teacher diagnostics only.
- [x] 3.6 Add index rebuild or migration handling for analyzer/mapping changes, including a clear rollback path to the previous index behavior.

## 4. Outbox, Jobs, and Publication Semantics

- [x] 4.1 Ensure point content changes fan out ES sync jobs to every active placement of the affected canonical point.
- [x] 4.2 Preserve draft-save behavior that queues delete/hide actions so unpublished edits do not leak into student search.
- [x] 4.3 Preserve publish/upsert and unpublish/archive/delete behavior for all active placements.
- [x] 4.4 Queue reindex jobs for affected descendant point placements when directory title, movement, chapter, order, or visibility changes affect catalog path context.
- [x] 4.5 Queue reindex jobs when media bindings or related-point titles change search-visible point metadata.
- [x] 4.6 Extend index/job diagnostics to distinguish pending, running, synced, failed, disabled, unavailable, retryable, stale, and directly-bypassed states.
- [x] 4.7 Keep ES indexing and RAG evidence refresh as separate job types while allowing the monitoring UI to display them together.

## 5. Global Intelligent Monitoring

- [x] 5.1 Rename the teacher navigation and page framing from provider-centric `AI 接入` wording to monitoring-oriented wording such as `智能监控` or `AI/RAG/ES 监控`.
- [x] 5.2 Keep provider credential editing, feature switches, dictionary import/editing, and catalog authoring controls separated from passive monitoring and diagnostic probes.
- [x] 5.3 Add global status sections for AI provider health, RAG/BGE health, ES backend/index health, dictionary assets, indexing state, and retrieval readiness.
- [x] 5.4 Add a query diagnostic panel that shows normalized query terms, extracted formulae, strict synonym expansion, feature-term matches, IK/analyzer output where available, route counts, ranked placement results, and per-result route reasons.
- [x] 5.5 Add teacher/operator-only authorization guards so diagnostics, ES DSL details, analyzer tokens, dictionary hashes, job payloads, and rerank internals are never exposed through student APIs.

## 6. Point Workbench and Catalog Editor Diagnostics

- [x] 6.1 Rename selected-point `AI 上下文` affordances to point retrieval diagnostics wording such as `点位检索诊断`.
- [x] 6.2 Show selected placement identity, canonical point identity, catalog path, publication state, student-visible content, normalized equation rows, and search-preview document fields in point diagnostics.
- [x] 6.3 Show ES index state, desired action, recent ES jobs, error messages, retryability, and whether the selected placement is expected to be student-searchable.
- [x] 6.4 Show static evidence bindings, dynamic RAG probe output, generated RAG query plans, candidate counts, and RAG failures separately from ES search state.
- [x] 6.5 Keep teacher-only notes and operational diagnostics visually separated from student-visible/indexed content.
- [x] 6.6 Update catalog editor node behavior so point nodes can open retrieval diagnostics, while directory nodes show directory metadata, recursive point counts, and reindex-impact hints rather than point-level AI/RAG/ES panels.

## 7. Verification

- [x] 7.1 Import the normalized 76-record dataset into a test environment and verify the expected split of equation-mode records, text-mode records, and reaction rows is preserved after persistence.
- [x] 7.2 Rebuild or refresh ES and verify indexed point-placement counts, published-content counts, canonical grouping, and sync-status counts are explainable from diagnostics.
- [x] 7.3 Test chemistry queries such as `H2O2 KMnO4`, `双氧水 高锰酸钾`, `SO2 刺激性气体`, `黄色沉淀`, `氧化性`, and chapter/directory phrases against both student search and teacher diagnostics.
- [x] 7.4 Verify teacher diagnostics explain normalization, synonym expansion, formula recall, equation-row co-occurrence, directory weak recall, route counts, and final ranking without changing student-facing response payloads.
- [x] 7.5 Add automated tests for dictionary categorization, formula normalization, search-document building, query planning, publication/outbox transitions, point placement fan-out, and teacher-only diagnostic authorization.
- [x] 7.6 Perform frontend checks for the intelligent monitoring page, point retrieval diagnostics panel, catalog editor node states, loading/error/empty states, and no-overlap responsive layout.
