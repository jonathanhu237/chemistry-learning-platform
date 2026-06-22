## Why

The new experiment directory draft is not a fixed chapter -> experiment -> point hierarchy. Each chapter can contain an uneven, human-authored multi-level directory before reaching learning points, and the student H5 navigation is expected to follow that directory structure.

The current platform uses `formal_experiments` as the parent of `experiment_video_points`, with many APIs, search documents, related links, and student routes keyed by `(experiment_id, point_key)`. That model makes the new catalog difficult to author, hard to move, and fragile when a point needs to appear under a different path. This change replaces the experiment-parent model with a chapter-scoped catalog tree and stable point nodes.

## What Changes

- **BREAKING** Replace the student-facing chapter -> experiment -> point model with chapter -> catalog node tree -> point detail.
- **BREAKING** Replace `experiment_id + point_key` as the primary point identity with stable catalog `node_id` / `point_id` identities.
- **BREAKING** Remove teacher-facing experiment-centered editing as the authoritative content authoring model; teachers author a chapter catalog tree instead.
- Add a chapter-scoped experiment catalog tree where each node can be a directory, point, hybrid directory+point, or shortcut/reference to another point.
- Add a teacher admin "left tree + right editor" workspace inspired by Feishu/Lark Wiki, Google Docs tabs/outline, Google Drive folders/shortcuts, Notion subpages, and Confluence page trees:
  - left side: searchable, collapsible, draggable tree with add sibling, add child, add point, add shortcut, rename, move, archive, and publish affordances;
  - right side: selected-node editor for metadata, student card copy, point learning content, video bindings, related links, search preview, publication state, and validation.
- Keep the student H5 design aligned with the provided prototype: periodic table entry -> chapter page -> recursive multi-level catalog page(s) -> concrete point video/detail page.
- Preserve the manually edited point authoring shape: point title, teacher-only note, experiment principle as equation or text, phenomenon explanation, safety note, related point links, bound videos, and fixed assessment handoff.
- Rebuild the video-library ES documents around published point nodes, not raw teacher media library assets, using point title plus student-facing point knowledge as the searchable source.
- Make ES/IK search production-grade for chemistry Chinese search: IK tokenizer, Harbin Institute of Technology stopwords, a maintained chemistry custom dictionary, and a maintained chemistry synonym dictionary must be part of the required app stack.
- Preserve existing AI-generated point chunks/evidence as a separate assistant/question-bank consumption path while migrating their point reference to stable node identities; this change does not replace the current `experiment_video_point_evidence` and RAG source-ref evidence chain with point-knowledge-driven retrieval.
- Migrate tests, seed data, production readiness validation, and E2E flows to the new catalog-tree contracts without keeping a legacy compatibility layer.

## Capabilities

### New Capabilities

- `experiment-catalog-tree`: Chapter-scoped multi-level experiment catalog nodes, stable point identity, shortcuts, ordering, publication, and migration away from experiment-parent point keys.
- `teacher-experiment-catalog-editor`: Teacher/admin authoring experience for the catalog tree, using a left tree and right editor to manage directories, points, point content, videos, links, search state, and validation.

### Modified Capabilities

- `experiment-centered-course-management`: No longer treats experiment units as the authoritative student-facing parent; course management becomes chapter catalog-tree management.
- `student-h5-learning-experience`: Student learning pages follow the prototype's chapter -> multi-level directory -> point video/detail flow instead of fixed experiment groups.
- `student-h5-route-stack-navigation`: Student routes must support durable catalog node/detail routes using node ids and source-aware return behavior.
- `experiment-assessment-point-binding`: Post-learning tests bind to stable point nodes while retaining chapter context.
- `experiment-video-point-question-binding`: Question and AI point bindings must reference stable catalog point nodes instead of `(experiment_id, point_key)`.
- `frontend-admin-maintainability`: Teacher frontend restructuring must preserve the established route/API/domain-module boundaries and avoid rebuilding a monolithic `App.tsx` or monolithic experiments page.
- `student-web-frontend-maintainability`: Student frontend route/page organization must keep the new recursive catalog screens localized and avoid returning to a monolithic H5 shell.

## Impact

- Database and migrations:
  - introduce catalog node, point content, media binding, related link, search index state, shortcut/reference, and migration tables;
  - retire or replace direct use of `formal_experiments`, `experiment_video_points`, `experiment_point_learning_content`, `experiment_point_related_links`, and `experiment_video_point_search_index_state` as primary contracts;
  - migrate existing formal experiments and point rows into catalog nodes without preserving legacy write paths.
- Backend:
  - replace admin `/experiments/{experiment_id}/video-points/{point_key}` point APIs with catalog-node APIs;
  - replace student `/experiment-groups/{parent_code}` and `/experiments/{experiment_id}` learning APIs with chapter catalog and point-detail APIs;
  - update video library search indexing to emit point-node documents;
  - update assessment, analytics, feedback, assistant, and question-bank point context to accept stable node ids.
- Teacher frontend:
  - replace the current experiment list/detail workflow with the catalog tree editor;
  - keep the existing admin engineering standard of domain API modules, feature modules, hooks, and scoped components.
- Student frontend:
  - implement the prototype-inspired flow with recursive catalog pages and point video/detail pages;
  - keep phone-first H5 design, TanStack route ownership, and source-aware back behavior.
- Search and worker stack:
  - ES/IK remains an application-required service;
  - search documents are generated from published point nodes and maintained through catalog/node/content/video/related-link changes;
  - analyzers must load IK segmentation, HIT stopwords, chemistry custom terms, and chemistry synonym expansion;
  - student search indexing must exclude teacher-only notes and AI evidence chunks;
  - raw teacher media library uploads remain excluded unless bound to a published point node.
- Validation:
  - strict OpenSpec validation, backend tests, admin typecheck/test/build/e2e, student typecheck/test/build/mobile QA, ES/IK readiness, compose smoke, and full production readiness validation must pass after implementation.
