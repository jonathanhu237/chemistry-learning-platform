# Experiment Catalog Tree Architecture

The experiment learning model is now `chapter -> directories -> point placements -> canonical experiment points`. Every catalog node has a stable `node_id`, but a point node is a placement: it answers where this experiment appears in the chapter tree. The reusable experiment identity is `experiment_catalog_points.id`, exposed as `canonical_point_id`. Legacy `(experiment_id, point_key)` values are migration inputs only and must not be used as the authoritative student or teacher route identity.

Use the two ids deliberately:

- `placement_node_id` / `node_id`: route target, breadcrumbs, chapter/path context, display order, publication/path availability, and search document id.
- `canonical_point_id`: shared experiment content, reaction equations, media bindings, related-link identity, AI evidence state/bindings, question references, assessment identity, analytics identity, and reuse count.
- Directory nodes never have `canonical_point_id`.
- A canonical point may have multiple active placements. Editing shared experiment fields from any placement updates every synchronized placement.
- Removing a placement removes only that catalog location while other active placements remain. Archiving the last active placement is blocked until a future explicit canonical archive decision exists.
- Do not introduce live `shortcut`, `reference`, or `hybrid` catalog node kinds. Synchronized reuse is modeled by multiple point placement nodes targeting one canonical point.

## Teacher Authoring

The admin `/experiments` workspace loads the catalog tree editor:

- Left pane: chapter selector, searchable draggable tree, create directory/point, move, reorder, archive, restore, publish, and validation actions.
- Right pane: selected-node editor. Directory nodes own title, teacher-only note, student-visible description, and card presentation. Point nodes own title/summary plus constrained point-card overrides.
- Point placements expose shared point content fields through their canonical point: point title, teacher-only note, principle mode, reaction equation rows or text, phenomenon explanation, safety note, related links, and bound videos.
- Reaction equation rows preserve teacher-entered raw text and store backend-normalized display text, mhchem, formulae, aliases, participants, reaction features, and validation warnings. The legacy `principle_equation` field remains a compatibility summary of raw equation rows; AI, ES, and RAG consumers should prefer backend-normalized rows.
- Directory nodes are navigation/category/card nodes only. They cannot own point content, video bindings, related links, assessment identity, or standalone search documents.
- Teacher-only notes are admin-only state. They are excluded from student APIs, Elasticsearch documents, student search summaries, and question evidence payloads.
- Related links default from nearby catalog points but are stored by canonical source/target identity with backend-resolved placement display targets.
- Video upload belongs to the media library. The catalog editor only binds existing media assets to point nodes, and one video point has exactly one current video resource.

## Student Flow

The student prototype flow is:

1. Periodic table or home entry opens a chapter page.
2. The chapter page loads `/api/student/chapters/{chapter_id}/catalog`.
3. Directory nodes load `/api/student/catalog/nodes/{node_id}` and render their child directory/point cards.
4. Point placements open `/api/student/catalog/points/{placement_node_id}` and render the video detail page.

Student point detail exposes only published, student-visible content: principle, phenomenon explanation, safety note, published videos, visible related links, breadcrumbs, and assessment context keyed by `canonical_point_id` with `placement_node_id` retained for route/path context. `canonical_node_id` is retained only as a compatibility bridge during migration.

## Search And Evidence Boundary

Student video-library search is an Elasticsearch projection from published point placements. Search documents are one document per published placement, derived from canonical point title/content/media plus the placement chapter/path and ancestor directory title/description as category context. Directory nodes never appear as standalone student results. Student search documents must exclude teacher-only notes, raw media-library-only uploads, `source_chunks`, and `experiment_video_point_evidence`.

Teacher catalog search is a separate Elasticsearch projection for authoring. It indexes active directory nodes and point placements, including draft/unpublished content, teacher notes, legacy identifiers, status facets, path context, and chemistry-derived formula/alias fields. Teacher search state is stored in `experiment_catalog_teacher_search_index_state` and is independent from the student video-library projection state.

AI-generated chunks/evidence and student search documents remain separate consumers:

- Teacher-authored point content may be passed into question workbench as `student_page_context_only`.
- Accepted question evidence must be freshly generated against canonical experiment points with placement context; old `experiment_video_point_evidence` point bindings are retired.
- This change migrates shared point resources to canonical point identity; it does not make point content a RAG chunk source.

## Point Jobs And Evidence Refresh

Catalog point ES sync and catalog-node evidence refresh are coordinated through PostgreSQL tables, not Redis/Rabbit/Celery in the first implementation:

- `experiment_catalog_point_jobs` is the job/outbox record for student ES upsert/delete, teacher catalog search upsert/delete, and RAG evidence refresh/delete work. Open pending/running jobs are idempotent by placement node id, job type, and payload, while storing `canonical_point_id` when a point placement owns one.
- `experiment_catalog_point_search_index_state` stores the student video-library ES projection state for placement documents; `experiment_catalog_teacher_search_index_state` stores the teacher catalog search projection state for directory and point documents.
- `experiment_catalog_point_evidence_state` records missing, pending, running, succeeded, failed, stale, disabled, and unavailable evidence states.
- `experiment_catalog_point_evidence_bindings` stores selected chunk bindings against `canonical_point_id` and canonical `source_chunks.id`; it never owns or deletes canonical chunks or embeddings. `source_placement_node_id` records where the refresh was triggered.
- Point content edits, publication changes, moves, video binding changes, and related-point changes mark evidence stale and may enqueue refresh when `CATALOG_POINT_EVIDENCE_AUTO_REFRESH=true`.
- RAG evidence refresh uses structured catalog point context and the configured BGE/RAG runtime. BGE unavailable or timeout failures are recorded on the job and evidence state while teacher saves remain committed.

An external broker is justified only when throughput, distributed scheduling, or operational isolation requires it. The public job-state and manual trigger API should remain stable if that happens later.

The committed catalog seed is regenerated from `docs/实验目录_整理版.md`. It imports 569 visible catalog nodes: 176 directories and 393 point placements. Those placements resolve to 357 canonical experiment points through reviewed duplicate grouping. Chapter 21 remains empty. The 30 examples in `docs/30点位例子.txt` are mapped to concrete leaf point placements and canonical points through semantic title/path/reagent matching, with reviewed overrides recorded for ambiguous candidates. The corrected hypochlorite siblings `NaClO + MnSO₄` and `NaClO + 品红溶液` remain distinct canonical points.

## Deployment Requirements

Elasticsearch with IK analysis is an application service, not an optional fallback. The Compose ES image must include:

- IK tokenizer support.
- HIT stopwords plus project chemistry stopwords.
- Chemistry custom dictionary.
- Chemistry synonym dictionary.

Production readiness and compose smoke checks verify the ES/IK service, analyzer assets, analyzer behavior, and point-node indexing readiness.
