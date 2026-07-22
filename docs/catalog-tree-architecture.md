# Experiment Catalog Tree Architecture

The learning catalog model is:

```text
chapter -> directory -> directory -> point placement -> canonical experiment point
```

Every catalog node has a stable `node_id`. A point node is a placement: it answers where an experiment appears in the curriculum tree. The reusable experiment identity is `experiment_catalog_points.id`, exposed as `canonical_point_id`.

Use the identities deliberately:

- `placement_node_id` / `node_id`: routes, breadcrumbs, chapter/path context, order, visibility, publication, Home recommendation, and teacher-search document identity.
- `canonical_point_id`: shared content, equations, media bindings, related links, assessment identity, analytics identity, question references, and evidence.
- Directory nodes never have a `canonical_point_id`.
- A canonical point may have multiple active placements; editing shared experiment content through one placement updates every view of that canonical point.
- Archiving one placement does not remove other placements. Archiving the final active placement requires the explicit `archive_final_placement` confirmation and preserves content/history for restoration.
- Live shortcut/reference/hybrid node kinds are not supported. Reuse is modeled by multiple point placements targeting one canonical point.

Legacy `(experiment_id, point_key)` values are migration/lineage inputs only. They are not authoritative route identities.

## Teacher Authoring

The current teacher `/experiments` route owns catalog authoring:

- Left pane: chapter selection, teacher catalog search, draggable tree, create, move, reorder, archive, restore, publish, and validation.
- Right pane: node editor, point content, equations, video bindings, related links, Home recommendation, search/evidence state, and preview.
- Directory nodes own title, teacher note, student description, ordering, and presentation only.
- Point placements expose canonical point title/content, principle mode, structured equations, phenomenon, safety, related links, and bound video.
- Reaction rows preserve teacher input while storing normalized display text, mhchem, formulae, aliases, participants, reaction features, and validation warnings.
- Teacher notes never appear in student payloads, Home search, student summaries, or question evidence.
- Video upload belongs to the teacher media workflow; the catalog binds ready media to a point.

The editor can mark a published point placement as an explicit Home recommendation and assign a non-negative order. The relational owner is `student_home_video_recommendations`; removing the mark returns the item to ordinary catalog ordering. Only an explicit mark may produce the student `recommended` reason.

## Student Read Models

Learn navigation follows the published tree:

1. Chapter pages load `/api/student/chapters/{chapter_id}/catalog`.
2. Directory pages load `/api/student/catalog/nodes/{node_id}`.
3. Point placements load `/api/student/catalog/points/{placement_node_id}`.

Point detail exposes only published student-visible content, ready/published media, visible related links, breadcrumbs, and assessment context. It carries both `placement_node_id` for route/path and `canonical_point_id` for shared learning identity.

Home uses `/api/student/home-video-feed`. Its default feed and `q` search parameter query the same PostgreSQL catalog/video read model. Eligible rows require a published placement, published canonical content, a published binding, and playable non-placeholder media. Recommendation-first ordering and query-bound cursor pagination are deterministic. Clicking a card navigates to the owning point placement.

Durable student video save state is favorite-only. Favorites reuse the same point/video read model and do not create a second content owner.

## Search Boundaries

There are three intentionally different retrieval paths:

### Student Home discovery

- Fact/read-model owner: PostgreSQL.
- Scope: published playable point placements only.
- Search fields: path, title/content, equations, formulae, aliases, reactants/products, and chemistry-derived tags available in the relational model.
- Operational model: no index, sync state, rebuild command, or Elasticsearch diagnostics.

### Teacher catalog-authoring search

- Fact owner: PostgreSQL catalog tables.
- Projection: a separate Elasticsearch/IK index.
- Scope: active directory and point nodes, including draft/unpublished authoring context, teacher notes, statuses, paths, equations, formulae, aliases, and legacy identifiers.
- State owner: `experiment_catalog_teacher_search_index_state`.
- Rebuild: `python scripts/rebuild_teacher_catalog_search_index.py --recreate`.

### Textbook RAG

- Corpus owner: published source documents/chunks and online textbook versions in PostgreSQL.
- Vector projection: the configured textbook RAG Elasticsearch index.
- Providers: administrator-configurable embedding and rerank HTTP APIs; online extraction may use configured MinerU OCR.
- Consumers: Atom, teacher learning assistant, catalog evidence refresh, and evidence-aware question workflows.

Teacher catalog search and textbook RAG do not share documents or state. Student Home does not introduce another vector/index-management path.

## Point Jobs And Evidence

Catalog asynchronous work is coordinated through PostgreSQL rather than a separate broker in the current design.

`experiment_catalog_point_jobs` accepts only:

- `teacher_search_upsert`
- `teacher_search_delete`
- `rag_evidence_refresh`
- `rag_evidence_delete`

Open jobs are idempotent by owner/action/payload and retain placement/canonical identity. The supporting state tables are:

- `experiment_catalog_teacher_search_index_state` for the teacher authoring projection;
- `experiment_catalog_point_evidence_state` for RAG evidence lifecycle; and
- `experiment_catalog_point_evidence_bindings` for selected canonical `source_chunks` references.

Point content, status, placement, media-binding, or related-link changes can mark evidence stale. When automatic refresh is enabled they may enqueue RAG evidence work. Search/RAG failures update their own job/state records while the teacher's PostgreSQL edit remains committed.

The evidence binding table references canonical chunks; it does not own or delete source documents, chunks, embeddings, or online textbook versions.

## Seed And Deployment Contract

The protected catalog seed contains 569 nodes: 176 directories and 393 point placements resolving to 357 canonical experiment points. The full point-content seed contains 393 published content records. Counts and checksums are enforced by `data/seed/manifests/core_resources.json`.

Elasticsearch/IK is part of the production graph for teacher catalog search. The image must include IK tokenization, project chemistry stopwords, chemistry custom terms, and synonyms. Production/Compose validation checks the analyzer assets and teacher-search rebuild; it does not attempt to rebuild a student video index.

Relevant checks:

```bash
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/rebuild_teacher_catalog_search_index.py --recreate
python scripts/validate_teacher_catalog_search.py
python scripts/validate_production_readiness.py
```
