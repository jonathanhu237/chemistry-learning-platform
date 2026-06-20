# Experiment Catalog Tree Architecture

The experiment learning model is now `chapter -> directories -> points`. Every catalog node has a stable `node_id`; point nodes use that same id as the point identity. Legacy `(experiment_id, point_key)` values are migration inputs only and must not be used as the authoritative student or teacher route identity.

## Teacher Authoring

The admin `/experiments` workspace loads the catalog tree editor:

- Left pane: chapter selector, searchable draggable tree, create directory/point, move, reorder, archive, restore, publish, and validation actions.
- Right pane: selected-node editor. Directory nodes own title, teacher-only note, student-visible description, and card presentation. Point nodes own title/summary plus constrained point-card overrides.
- Point nodes expose point content fields: point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related links, and bound videos.
- Directory nodes are navigation/category/card nodes only. They cannot own point content, video bindings, related links, assessment identity, or standalone search documents.
- Teacher-only notes are admin-only state. They are excluded from student APIs, Elasticsearch documents, student search summaries, and question evidence payloads.
- Related links default from nearby catalog points but remain manually editable through `target_node_id` links.
- Video upload belongs to the media library. The catalog editor only binds existing media assets to point nodes.

## Student Flow

The student prototype flow is:

1. Periodic table or home entry opens a chapter page.
2. The chapter page loads `/api/student/chapters/{chapter_id}/catalog`.
3. Directory nodes load `/api/student/catalog/nodes/{node_id}` and render their child directory/point cards.
4. Point nodes open `/api/student/catalog/points/{node_id}` and render the video detail page.

Student point detail exposes only published, student-visible content: principle, phenomenon explanation, safety note, published videos, visible related links, breadcrumbs, and assessment context keyed by `point_node_id`.

## Search And Evidence Boundary

Student video-library search is an Elasticsearch projection from published catalog point nodes. Search documents are derived from point title, student-visible point knowledge, visible related links, published video metadata, and ancestor directory title/description as category context. Directory nodes never appear as standalone results. Search documents must exclude teacher-only notes, raw media-library-only uploads, `source_chunks`, and `experiment_video_point_evidence`.

AI-generated chunks/evidence and student search documents remain separate consumers:

- Teacher-authored point content may be passed into question workbench as `student_page_context_only`.
- Accepted question evidence must be freshly generated against catalog node ids or deterministic catalog seed keys; old `experiment_video_point_evidence` point bindings are retired.
- This change migrates point identity to stable catalog node ids; it does not make point content a RAG chunk source.

The committed catalog seed is regenerated from `docs/实验目录_整理版.md`. The 30 examples in `docs/30点位例子.txt` are mapped to concrete leaf point nodes through semantic title/path/reagent matching, with reviewed overrides recorded for ambiguous candidates.

## Deployment Requirements

Elasticsearch with IK analysis is an application service, not an optional fallback. The Compose ES image must include:

- IK tokenizer support.
- HIT stopwords plus project chemistry stopwords.
- Chemistry custom dictionary.
- Chemistry synonym dictionary.

Production readiness and compose smoke checks verify the ES/IK service, analyzer assets, analyzer behavior, and point-node indexing readiness.
