## Context

The previous catalog-tree change successfully replaced `chapter -> experiment -> point` with a recursive catalog model, but it intentionally allowed four node kinds: `directory`, `point`, `hybrid`, and `shortcut`. The updated product direction is stricter: chapters are roots, directories are navigation/category/card nodes, and points are video learning leaves. Hybrid and shortcut nodes create ambiguous UI, ambiguous indexing, and unnecessary implementation branches.

The current implementation also concentrates catalog tree behavior in `server/app/domains/catalog_tree/tree.py`: tree CRUD, validation, point content, media binding, related links, search preview, student catalog read models, student point detail, and media file resolution. Adding the new product semantics inside that module would make the tree service harder to maintain. This change therefore treats the product correction and service split as one unit of work.

The admin UI currently exposes always-visible up/down controls on every row and mixes node editing, move controls, point forms, related links, and video upload/binding in one editor component. The updated UI should feel closer to a professional document/file tree: clear folder-vs-point identity, low-noise row actions, drag-and-drop movement, and a focused editor for the selected node.

## Goals / Non-Goals

**Goals:**
- Replace catalog node semantics with exactly two node kinds: `directory` and `point`.
- Make directory nodes student-facing navigation/category/card nodes, not searchable learning results.
- Make point nodes the only stable point identity for video detail, ES search, questions, assessments, AI context, analytics, feedback, media bindings, and related links.
- Remove shortcut and hybrid behavior from database constraints, API schemas, backend services, frontend types, student routes, and OpenSpec requirements.
- Add directory card presentation metadata and limited point card presentation overrides.
- Remove video upload from the catalog editor while keeping existing-media binding and binding publication.
- Replace noisy up/down row controls with a draggable, visually polished tree interaction.
- Split the catalog tree backend into clear service modules and keep admin/student routers thin.
- Keep student H5 recursive catalog navigation and point detail behavior intact while removing shortcut assumptions.

**Non-Goals:**
- This change does not redesign the video upload/media library page.
- This change does not introduce multi-parent point reuse or shortcut/reference behavior.
- This change does not change the evidence-chain semantics for question generation or RAG. Teacher point content remains page context only unless a separate evidence workflow promotes it.
- This change does not add a free-form visual card designer. Card presentation is structured and constrained.
- This change does not rework unrelated large admin pages outside the catalog editor.

## Decisions

### Decision 1: Two node kinds only

Catalog nodes will use `node_kind IN ('directory', 'point')`.

- `directory` may have child directories and child points.
- `point` is a learning leaf and MUST NOT have children.
- Existing `hybrid` records migrate to either:
  - `point` when the node has point content or point bindings and no required child-navigation semantics; or
  - a directory plus a child point when both child navigation and point content must be preserved.
- Existing `shortcut` records are removed from live semantics. If a shortcut targets a point, it migrates to a normal point placement only when product/data owners choose to materialize it; otherwise it is archived with metadata for audit.

Alternative considered: keep hidden `hybrid/shortcut` server support and hide it from the UI. Rejected because the product model intentionally removes these semantics, and hidden compatibility would continue to leak into search, routes, validation, and tests.

### Decision 2: Directories are category/card nodes

Directory fields are:
- `title`
- teacher-only note
- student-visible description
- optional card image reference
- optional card icon key
- optional accent/theme token
- optional display metadata such as layout variant
- publication/status/order/tree metadata

Directory text contributes to descendant point documents as category/path context. Directory nodes do not produce independent ES documents and do not appear as standalone video-library search results.

Alternative considered: index directories as results that open directory pages. Rejected because the student video library searches videos/learning points; directory matches should lead to concrete point results.

### Decision 3: Points own learning identity and bounded card presentation

Point nodes retain the stable `node_id`/`point_id` identity. Point fields remain:
- point title
- teacher-only note
- principle mode and principle content
- phenomenon explanation
- safety note
- bound videos
- related point links
- optional card presentation override

Point card presentation is intentionally smaller than directory card presentation. It may override thumbnail/image, short display description, icon/accent, or list emphasis, but it MUST NOT allow arbitrary layout divergence. A point card should still read as a point entry across chapter pages, directory pages, search results, and related links.

### Decision 4: Upload belongs to media, binding belongs to catalog

The catalog editor will bind existing media assets to point nodes, change binding status, unbind/archive bindings, and preview bound media. It will not create new media assets or include a local file upload control. Upload remains owned by the media/video page and its processing lifecycle.

Alternative considered: keep upload-and-bind as a convenience action. Rejected because the product ownership is clear and mixed upload/bind UI makes the catalog editor too broad.

### Decision 5: Drag tree replaces always-visible reorder buttons

The admin tree will use a mature tree/drag interaction. The implementation spike should prefer one of:
- Ant Design `Tree` with `draggable`, custom icons, controlled expansion/selection, and custom row rendering, because the admin app already uses Ant Design.
- `react-arborist` if Ant Design Tree cannot support the desired polished Finder/VS Code/Figma-layers style without excessive custom code.

The tree row design should:
- show disclosure affordance only for directories with children;
- use distinct directory and point icons;
- hide destructive/additional actions until hover or selection;
- use a compact inline status indicator;
- show a drag handle and drop indicator for move/reorder;
- validate drops so points cannot receive children and cross-chapter moves are explicit or rejected;
- support keyboard-accessible fallback actions through a row menu or selected-node actions.

### Decision 6: Backend catalog service split

`server/app/domains/catalog_tree/tree.py` should be decomposed into focused modules. Target ownership:

- `nodes.py`: node lookup, create/update/move/reorder/status, parent/cycle validation.
- `directories.py`: directory metadata, card presentation, directory validation, directory student card shaping.
- `points.py`: point content, publication validation, point card overrides, point student detail shaping.
- `media_bindings.py`: binding existing media, binding status, bound media read models.
- `related_links.py`: manual and generated related point links.
- `search_documents.py`: student-visible search document construction and index queueing.
- `student_read_models.py`: chapter catalog, directory detail, point detail orchestration.
- `files.py`: media/thumbnail file response resolution when it remains catalog-specific.

Routers should import orchestration functions from these modules and keep request/response concerns at the API layer. Shared helpers should be moved only when there is a clear owner; avoid creating a new generic utility dumping ground.

### Decision 7: Migration and validation are explicit

Because this is a breaking semantic correction shortly after the previous catalog-tree migration, implementation should include a new migration that:
- tightens `node_kind` constraints;
- removes or ignores shortcut target semantics from live paths;
- adds directory/card presentation storage;
- normalizes any existing `hybrid` or `shortcut` data from local/dev/prod-like databases;
- ensures point identity remains stable for existing point rows.

Validation must include a repository search or architecture script check that prevents reintroducing `hybrid`, `shortcut`, and upload-from-catalog live paths.

## Risks / Trade-offs

- [Risk] Migrating existing `hybrid` nodes can lose intent when a node has both children and point content. -> Mitigation: produce a deterministic migration report and either split into directory + child point or archive the ambiguous point capability with audit metadata.
- [Risk] Removing shortcuts removes multi-path reuse. -> Mitigation: explicitly defer multi-path appearance to a later product design; related links and search can still surface points across directories.
- [Risk] Drag-and-drop tree interactions can be inaccessible if mouse-only. -> Mitigation: keep selected-node move controls or row menu fallback and validate keyboard/screen-reader basics.
- [Risk] Adding a third-party tree dependency may increase bundle size. -> Mitigation: prefer Ant Design Tree first; if using `react-arborist`, lazy-load the catalog editor route and include build-report validation.
- [Risk] Service split can become a mechanical file shuffle. -> Mitigation: tasks must require ownership-based modules and updated architecture tests, not only line-count reduction.
- [Risk] Directory text boosting descendant points may make broad category searches noisy. -> Mitigation: index ancestor directory text as lower-weight category/path fields and validate smoke queries against point results.

## Migration Plan

1. Add a migration that introduces directory card presentation fields/metadata and normalizes node kinds.
2. Migrate or archive `hybrid` and `shortcut` records deterministically, preserving audit metadata.
3. Update backend schemas and services to reject `hybrid`, `shortcut`, point children, directory point content, and catalog upload actions.
4. Split catalog tree domain modules before adding new directory/point behavior.
5. Update admin UI tree and editor panels.
6. Update student catalog and search behavior.
7. Run backend tests, frontend checks, mobile QA, ES/IK smoke, OpenSpec strict validation, and production readiness.

Rollback for application code is normal git rollback. Database rollback is data-sensitive because node kind normalization is destructive; the migration should preserve audit metadata for ambiguous records rather than silently deleting it.

## Open Questions

- Should directory card image use an existing media asset id, a separate lightweight image asset table, or metadata pointing to protected static/media resources?
- Should point card override image be allowed to reference the bound video's thumbnail automatically, or only choose an explicit asset?
- Should cross-chapter drag moves be disallowed in the first implementation, or allowed through an explicit confirmation flow?
- How should existing local shortcut records, if any, be handled when they point to a target that is already visible elsewhere?
