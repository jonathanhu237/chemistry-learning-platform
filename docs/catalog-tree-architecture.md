# Experiment Catalog Tree Architecture

The experiment learning model is now `chapter -> catalog nodes -> point`. A catalog node has a stable `node_id`; point-capable nodes use that same id as the point identity. Legacy `(experiment_id, point_key)` values are migration inputs only and must not be used as the authoritative student or teacher route identity.

## Teacher Authoring

The admin `/experiments` workspace loads the catalog tree editor:

- Left pane: chapter selector, searchable tree, create sibling/child/point/hybrid/shortcut, move, reorder, archive, restore, publish, and validation actions.
- Right pane: selected-node editor. Directory, hybrid, point, and shortcut nodes share title/summary/status editing.
- Point-capable nodes expose point content fields: point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related links, and bound videos.
- Teacher-only notes are admin-only state. They are excluded from student APIs, Elasticsearch documents, student search summaries, and question evidence payloads.
- Related links default from nearby catalog points but remain manually editable through `target_node_id` links.

## Student Flow

The student prototype flow is:

1. Periodic table or home entry opens a chapter page.
2. The chapter page loads `/api/student/chapters/{chapter_id}/catalog`.
3. Directory and hybrid nodes load `/api/student/catalog/nodes/{node_id}`.
4. Point and shortcut nodes open `/api/student/catalog/points/{node_id}`. Shortcuts preserve the source node in route context while resolving the canonical point content.

Student point detail exposes only published, student-visible content: principle, phenomenon explanation, safety note, published videos, visible related links, breadcrumbs, and assessment context keyed by `point_node_id`.

## Search And Evidence Boundary

Student video-library search is an Elasticsearch projection from catalog point nodes. Search documents are derived from point title, student-visible point knowledge, visible related links, and published video metadata. They must exclude teacher-only notes, raw media-library-only uploads, `source_chunks`, and `experiment_video_point_evidence`.

AI-generated chunks/evidence and student search documents remain separate consumers:

- Teacher-authored point content may be passed into question workbench as `student_page_context_only`.
- Accepted question evidence remains `experiment_video_point_evidence` plus canonical/RAG source refs.
- This change migrates point identity to stable catalog node ids; it does not make point content a RAG chunk source.

## Deployment Requirements

Elasticsearch with IK analysis is an application service, not an optional fallback. The Compose ES image must include:

- IK tokenizer support.
- HIT stopwords plus project chemistry stopwords.
- Chemistry custom dictionary.
- Chemistry synonym dictionary.

Production readiness and compose smoke checks verify the ES/IK service, analyzer assets, analyzer behavior, and point-node indexing readiness.
