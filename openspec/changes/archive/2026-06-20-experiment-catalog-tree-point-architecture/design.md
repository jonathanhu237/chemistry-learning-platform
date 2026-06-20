## Context

The product direction has changed from a fixed chapter -> experiment -> point catalog to a variable-depth chapter -> directory tree -> point catalog. The latest draft and prototype show the student flow as periodic table/home entry -> selected chapter page -> one or more directory pages -> concrete point video/detail page. Different chapters can have different depths and grouping labels.

The current implementation is centered on `formal_experiments` and `experiment_video_points`. Point content, point videos, point related links, video-library search documents, question bindings, assistant context, assessment handoff, analytics, and student routes all rely on `experiment_id` plus `point_key`. That identity is not stable enough for the new authoring model because a teacher may move a point between directories, rename a node, or expose the same point through a shortcut without changing the point itself.

The teacher authoring surface is the highest-risk UX area. The student side can follow the provided prototype, but teachers need a fast editor similar to Feishu/Lark Wiki, Google Docs tabs/outline, Google Drive folder/shortcut organization, Notion subpages, and Confluence page trees: a navigable tree where the selected node opens an editor, and node structure can be edited in context.

## Current Implementation Findings

The current system is close to the desired direction in a few places, but the boundaries are not explicit enough for the new tree architecture.

- Admin point content currently exists through `ExperimentPointLearningContentRequest` in `server/app/experiment_admin_schemas.py`, with `point_title`, `principle_mode`, `principle_equation`, `principle_text`, `phenomenon_explanation`, `safety_note`, and generic `metadata`.
- The current admin form exists in `apps/admin-web/src/features/experiments/pointContent/PointContentModal.tsx` and its mapper in `pointContentMapper.ts`. It already edits title, principle, phenomenon explanation, safety note, and related links, but it does not have an explicit teacher-only note field.
- Related experiment links are real product scope, not optional cleanup. The current editor already exposes them, and the new tree model must keep teacher-editable related links keyed by stable point node ids.
- Student video-library search currently builds point documents in `server/app/domains/video_library/search.py` from published teacher point content. `_point_document` uses point title, principle, phenomenon explanation, safety note, extracted formulae, aliases, and reaction features. Existing tests such as `server/tests/test_student_video_library.py` assert that search text does not include `source_chunks` or `experiment_video_point_evidence`.
- ES mapping currently lives in `server/app/domains/video_library/index_client.py`. It creates a `chemistry_ik` analyzer with IK tokenizer plus lowercase only. This is not yet the full target because it does not wire HIT stopwords, a chemistry custom dictionary, or a synonym dictionary into the ES analyzer/runtime.
- The current helper `server/app/chemistry_search.py` loads `data/seed/search/chemical_aliases.json` and `data/seed/search/chemical_stopwords.txt`, extracts formulae, expands aliases, and normalizes queries. This is useful but incomplete: it is Python-side enrichment, not a full ES custom dictionary + stopword + synonym analyzer contract.
- The current compose stack already requires an ES image with the IK plugin through `server/Dockerfile.elasticsearch-ik`, `docker-compose.yml`, `.env.example`, and `VIDEO_LIBRARY_SEARCH_ANALYZER=ik_max_word`. This requirement must remain mandatory for the whole app, not an optional search sidecar.
- The current question workbench already includes teacher point content in context, but labels it as `student_page_context_only` in `server/app/domains/questions/workbench.py`. The true evidence path remains `experiment_video_point_evidence` plus canonical/RAG source refs. That is acceptable for this change and must not be silently rewritten into "point knowledge drives RAG retrieval."
- Existing AI-generated chunks/evidence and student ES video-library documents are separate consumer systems. AI/question generation consumes reviewed evidence and source chunks; student search consumes teacher-authored, student-facing point documents.

## Goals / Non-Goals

**Goals:**
- Replace the authoritative experiment-parent point model with a chapter-scoped catalog tree.
- Make stable catalog `node_id` / `point_id` the point identity for content, video binding, search, questions, AI context, analytics, feedback context, and assessment handoff.
- Support arbitrary catalog depth per chapter while keeping the student H5 route stack durable and phone-first.
- Build a teacher admin workspace with a left tree and right editor so teachers can create, move, rename, publish, and validate nodes without editing ids.
- Preserve manually authored point fields: point title, teacher-only note, principle equation or text, phenomenon explanation, safety note, related links, video resources, and "go test" handoff.
- Keep ES/IK as an application-required service and index only published point-node learning documents, not raw teacher media library assets.
- Require the ES/IK analyzer stack to include IK tokenizer, Harbin Institute of Technology stopwords, a chemistry custom dictionary, and a chemistry synonym dictionary.
- Preserve AI-generated point chunks as a separate assistant/evidence consumption path while migrating their reference target to stable point nodes.
- Preserve the current question workbench evidence model: teacher point content may remain context marked `student_page_context_only`, while accepted evidence continues to come from `experiment_video_point_evidence` and RAG source refs.
- Preserve existing engineering standards: slim backend domains, admin domain API clients, route/feature boundaries, tests, compose smoke, and production readiness validation.

**Non-Goals:**
- Do not finalize the teaching catalog copy itself. The catalog draft can still change; this change provides the flexible structure to hold it.
- Do not preserve legacy `/experiments/{experiment_id}/video-points/{point_key}` write APIs as compatibility routes.
- Do not expose the teacher raw media library to student video-library search unless a media asset is bound to a published point node.
- Do not create an AI-generated authoring flow for point content; teachers manually edit learning content.
- Do not include teacher-only notes in student H5 payloads, student video-library ES documents, or student-visible search snippets.
- Do not change the accepted question evidence chain in this change; point knowledge is student-facing learning content, not a replacement for reviewed evidence chunks.
- Do not redesign the student visual style beyond implementing the prototype's navigation logic.

## Decisions

### Decision 1: Use one catalog node tree per chapter

Each chapter owns a tree of `experiment_catalog_nodes`. A node has a stable id, optional parent id, chapter id, title, summary, display order, status, and kind. Root nodes are the top-level entries under a chapter. Children can be nested to arbitrary depth subject to a configured safety limit.

Alternative considered: keep `formal_experiments` as the first directory level and add subdirectories underneath. Rejected because it preserves a false domain concept and keeps code biased toward experiment units even when the real catalog uses uneven categories.

### Decision 2: Treat point capability as node capability, not separate tree type

Nodes support these authoring kinds:
- `directory`: navigation/grouping only.
- `point`: playable/detail learning point.
- `hybrid`: directory that also has point detail content.
- `shortcut`: a navigation entry that references an existing point node without duplicating its content.

The right editor derives available tabs from node capability. A teacher can start with a directory and later enable point content without recreating the node.

Alternative considered: separate folder table and point table. Rejected because the teacher mental model and products like Notion/Confluence treat pages/nodes as the editable unit, and because hybrid nodes are plausible in this curriculum.

### Decision 3: Use stable ids everywhere point identity matters

Point learning content, video bindings, related links, question bindings, AI evidence, search index state, assessment events, analytics, and feedback context must reference point-capable nodes by stable id. Slugs, titles, path labels, legacy codes, and display order are not identity.

Alternative considered: continue using `(experiment_id, point_key)` and compute synthetic ids. Rejected because it would make moves/renames fragile and keep hidden legacy coupling.

### Decision 4: Use shortcuts for multi-path appearance

If one point belongs under multiple conceptual paths, the system creates a shortcut/reference node that points to the canonical point node. Student navigation may show the shortcut in its local path, but detail, videos, questions, and search use the target point identity.

Alternative considered: duplicate point content under each path. Rejected because it creates conflicting content versions and makes search/assessment analytics ambiguous.

### Decision 5: Teacher frontend is a tree editor, not a table-first experiment manager

The admin feature becomes a chapter catalog editor:

```text
Teacher Catalog Workspace
  Left Tree
    search
    collapse/expand
    add sibling/child/point/shortcut
    drag reorder/move
    rename/archive/publish state
  Right Editor
    node basics
    student card/summary
    point learning content
    video bindings
    related links
    search preview/index status
    validation/publication
```

This keeps teachers close to the structure they are authoring and avoids asking them to pre-classify every row as experiment, directory, or point before they can write.

Alternative considered: keep the current experiment list with nested point panels. Rejected because the user explicitly wants a document/wiki-like tree and the new catalog is not experiment-centered.

### Decision 6: Student frontend follows prototype flow with recursive catalog pages

Student H5 routes should support:

```text
/chapter/$chapterId
/chapter/$chapterId/catalog/$nodeId
/point/$nodeId
```

The chapter page shows the selected chapter context and top-level catalog entries. A directory node opens another catalog page with breadcrumbs. A point node opens the video/detail page. A shortcut opens the target point detail while preserving source-aware return.

Alternative considered: keep `/point/$experimentId?pointKey=...`. Rejected because experiment id is no longer the parent identity.

### Decision 7: Point authoring separates student knowledge from teacher notes

Point-capable nodes have a small teacher-authored content model:
- `point_title`: the human-readable learning point name.
- `teacher_note`: teacher-only remarks, including non-experiment notes, operational hints, or authoring context.
- `point_knowledge`: principle mode plus principle equation or text, phenomenon explanation, and safety note.
- `related_links`: teacher-editable links to other point nodes, with generated defaults allowed from nearby catalog nodes.
- `video_bindings`: one or more media assets bound to the point node.

Student APIs expose point title, point knowledge, related links, videos, and assessment context. They must not expose `teacher_note`. Student ES documents must not index `teacher_note`, because it may contain private authoring remarks or non-student-facing material.

Alternative considered: store teacher remarks inside generic metadata. Rejected because it hides a product-critical privacy boundary and makes it too easy for remarks to leak into search, student pages, or generated prompts.

### Decision 8: Search documents are point-node documents

The video-library search index consumes published point nodes and student-facing teacher-authored content: point title, principle text/equation, phenomenon explanation, safety note, related link labels where student-facing, bound published video metadata, chapter path, catalog path, extracted formulae, aliases, and reaction features. Raw media assets remain teacher resources and are not indexed for student search unless bound to a published point node.

Alternative considered: index every uploaded video and filter at query time. Rejected because it would leak teacher storage semantics into the student learning library.

### Decision 9: ES/IK analyzer is a required chemistry search subsystem

The student video-library ES index must use a chemistry-aware analyzer stack:
- IK tokenizer for Chinese segmentation, with `ik_max_word` for indexing and an appropriate search analyzer such as `ik_smart`.
- Harbin Institute of Technology stopword list as the baseline Chinese stopword source, plus project-level chemistry stopwords.
- A maintained chemistry custom dictionary for formulas, reagent names, ions, element/family names, common lab terms, and curriculum-specific phrases.
- A maintained chemistry synonym dictionary for formula/name aliases, Chinese/English aliases, full-width/half-width variants, and common student search variants.
- Versioned dictionary files mounted or baked into the ES/IK container so compose, CI smoke, and production readiness can verify the same analyzer behavior.

The current code already has IK plugin installation and Python-side alias/stopword helpers, but this decision promotes the dictionary system into the ES deployment contract. Admin point edits must be able to trigger reindexing so changes to point title, point knowledge, related links, publication, or video binding affect student search.

Alternative considered: keep only Python-side query expansion and ES lowercase filtering. Rejected because it will not provide reliable Chinese chemistry tokenization, stopword filtering, or synonym matching at index time.

### Decision 10: AI chunks remain separate from student search documents

AI-generated point chunks/evidence remain an assistant/question-bank consumption path. They may be linked to point nodes for context, but they are not the authoritative student video-library search document and do not replace manually authored point content.

For the current question workbench, teacher point content can remain in context as `student_page_context_only`. Accepted question evidence continues to come from `experiment_video_point_evidence` and canonical/RAG source refs. This change only migrates point identity from legacy `(experiment_id, point_key)` to stable point-node ids; it does not require changing evidence retrieval into "search chunks from point knowledge."

Alternative considered: merge ES search documents and AI evidence chunks into one content object. Rejected because the user clarified they serve different consumers and have different provenance.

### Decision 11: Destructive migration, no compatibility layer

Implementation may remove old APIs, old UI flows, and old test fixtures once the new tree contracts are in place. Migration scripts must move existing useful content into the new tables, but application code should not keep parallel legacy paths.

Alternative considered: support both old experiment APIs and new catalog APIs. Rejected because it would prolong ambiguity and has repeatedly caused coupling problems.

## Risks / Trade-offs

- [Risk] Catalog depth and shortcuts can create confusing navigation or loops -> Mitigation: enforce acyclic parent relationships, reject shortcut-to-shortcut loops, cap rendered depth, and show breadcrumbs.
- [Risk] Migration can break question/assessment/analytics history -> Mitigation: create a deterministic legacy identity map from `(experiment_id, point_key)` to new point node ids and migrate historical metadata before deleting old write paths.
- [Risk] Teacher tree editing can become complex on the first pass -> Mitigation: implement reliable create/rename/move/publish/search/editor flows first, then refine shortcuts and bulk operations.
- [Risk] Student routes may lose source-aware return behavior -> Mitigation: keep TanStack route search source context and add E2E coverage for chapter -> directory -> point -> back.
- [Risk] ES documents can go stale after tree moves or content edits -> Mitigation: queue index state changes on node, content, publication, related-link, and media-binding mutations.
- [Risk] Teacher-only notes leak to students or ES -> Mitigation: model `teacher_note` as a separate field, exclude it from student serializers and ES builders, and add regression tests for both paths.
- [Risk] Search quality remains weak if dictionaries are only Python-side -> Mitigation: make HIT stopwords, custom chemistry dictionary, and synonym dictionary part of the ES/IK container contract and readiness checks.
- [Risk] Question generation behavior is accidentally changed while migrating identities -> Mitigation: preserve `student_page_context_only`, `experiment_video_point_evidence`, and source-ref roles in tests while changing only identity references.
- [Risk] Shortcuts can distort assessment context -> Mitigation: assessments bind to canonical point node id while preserving opening chapter/path as context metadata.
- [Risk] The prototype catalog is not final -> Mitigation: store the catalog as mutable data, not hardcoded frontend levels.

## Migration Plan

1. Add new catalog-tree tables and a legacy identity mapping table.
2. Backfill chapters, former formal experiments, and existing experiment video points into catalog nodes:
   - former formal experiment rows become directory or hybrid nodes depending on available point/content state;
   - former video points become point nodes under the migrated parent;
   - old `(experiment_id, point_key)` maps to the new point node id.
3. Migrate point content, related links, media bindings, search index state, question metadata, assessment metadata, assistant evidence references, analytics metadata, and feedback context to node ids.
4. Replace backend admin and student APIs with catalog-node APIs.
5. Replace admin experiments UI with the teacher catalog editor.
6. Replace student experiment group and point routes with catalog/point-node routes.
7. Rebuild ES index documents from published point nodes and student-facing point knowledge only.
8. Add ES/IK dictionary assets and deployment wiring for HIT stopwords, chemistry custom terms, and chemistry synonyms.
9. Update tests and seed data.
10. Run strict OpenSpec validation, backend tests, admin and student typecheck/test/build/e2e/mobile QA, ES/IK readiness, compose smoke, and full production readiness validation.
11. Remove dead legacy API/client/UI paths after validation passes.

Rollback is data-sensitive. Before destructive migration, create a database backup and keep the migration identity map reversible enough to inspect old-to-new point mapping. Code rollback without data rollback is not guaranteed because this is an intentional breaking change.

## Open Questions

- Should a hybrid node be visible as both a directory card and a playable point card, or should mobile H5 choose one primary action per node?
- What maximum visible catalog depth should the student UI support before forcing a compact breadcrumb/list treatment?
- Should teacher-created shortcuts be available in the first implementation pass or gated behind a feature flag until the main tree is stable?
- Should chapter roots be one tree per learning profile or one tree per theory chapter id when a profile and chapter are not identical?
