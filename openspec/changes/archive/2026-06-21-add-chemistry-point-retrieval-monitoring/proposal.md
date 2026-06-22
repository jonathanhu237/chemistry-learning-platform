## Why

Chemistry experiment point search is no longer a generic text-search problem: each result is a catalog point placement with directory context, canonical point identity, structured three-element content, reaction-equation rows, chemistry dictionaries, ES indexing state, and AI/RAG evidence behavior. Teachers need a monitor that shows whether AI, RAG, ES, dictionaries, recall routes, and point-level indexing are healthy and explainable before the 76 normalized three-element records are imported and used for ES testing.

## What Changes

- Rename and broaden the teacher `AI 接入` surface into an intelligent monitoring surface for AI/RAG/ES status while keeping provider credential and feature-switch ownership separated according to existing settings boundaries.
- Add global monitoring for ES index health, dictionary assets, published point counts, pending/failed index jobs, and retrieval-path readiness.
- Add query-level retrieval diagnostics so teachers/operators can test a query and inspect normalization, chemical synonym expansion, IK tokenization, multi-route recall counts, merged ranking, and result reasons.
- Treat student-facing search results as catalog point placement documents: `placement_node_id` is the ES document identity, `canonical_point_id` supports deduplication and smart-pointer grouping, and catalog path fields provide context, filters, and weak recall.
- Separate chemistry vocabulary into strict chemical synonyms, reagent/formulation aliases, condition terms, phenomenon terms, and property terms so ES expansion does not confuse entity equivalence with observations or experimental behavior.
- Strengthen equation-aware recall with formula, reactant, product, participant, equation-row, condition, and reaction-feature fields instead of flattening equation principles into ordinary text.
- Preserve the existing Postgres-backed outbox/job model for ES and RAG freshness, and make its status visible at both global and selected-point levels.
- Reframe the selected point `AI 上下文` diagnostics as point retrieval diagnostics that show ES, RAG, AI, search-preview, job-state, and student-visible content contracts together.

## Capabilities

### New Capabilities
- `chemistry-point-retrieval-monitoring`: Global and point-level teacher monitoring for chemistry search dictionaries, ES index health, multi-route recall diagnostics, AI/RAG/ES runtime state, and ranking explanations.

### Modified Capabilities
- `ai-access-configuration`: The existing `AI 接入` navigation/page scope changes from provider-centric wording to intelligent monitoring wording while preserving credential and feature-switch boundaries.
- `student-h5-video-library-search`: Student video-library search requirements expand from generic ES-backed search to chemistry-aware point placement retrieval with directory context, canonical grouping, dictionary layers, and equation-aware recall.
- `catalog-point-index-evidence-jobs`: ES/RAG job requirements expand to clarify placement-level documents, canonical fan-out, save-vs-publish indexing semantics, and global observability.
- `catalog-point-ai-context-workbench`: Point AI context diagnostics expand into point retrieval diagnostics covering ES search preview, RAG probe/evidence, AI runtime health, and raw job/index state.
- `teacher-experiment-catalog-editor`: The catalog editor diagnostic entry labels and secondary panels change to distinguish authoring from retrieval monitoring without exposing debug fields in the default editing flow.

## Impact

- Teacher frontend navigation and `apps/web-teacher/src/features/ai-config` monitoring UI.
- Teacher catalog point diagnostics in `apps/web-teacher/src/features/catalog-tree`.
- Admin APIs for AI runtime, ES index diagnostics, point job state, point AI/RAG context, and new retrieval-debug endpoints.
- Backend ES index mapping/query construction in `server/app/domains/video_library`.
- Chemistry dictionary assets under `data/seed/search`, including strict synonyms, reagent aliases, stopwords, IK dictionaries, and analyzer manifests.
- Catalog point search document construction and ES outbox/job state under `server/app/domains/catalog_tree`.
- Student H5 video-library search ranking and result grouping, while keeping raw diagnostics teacher-only.
