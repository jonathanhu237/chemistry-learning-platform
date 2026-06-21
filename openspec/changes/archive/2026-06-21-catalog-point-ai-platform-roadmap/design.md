## Context

The repository has completed several important migrations, but they now need to be treated as one connected product architecture:

- The experiment catalog is no longer a fixed experiment -> point model. The full chapter directory tree is the product model, with leaf catalog nodes representing experiment points and directories representing navigation/grouping.
- The current teacher point content schema still has `principle_mode`, a single `principle_equation`, `principle_text`, `phenomenon_explanation`, and `safety_note`. This is not rich enough for points that need multiple chemical reaction equations.
- Student ES search already consumes catalog point title, full path, principle, phenomenon explanation, safety note, formulae, aliases, reaction features, related links, and published video metadata. It intentionally excludes teacher-only notes and raw AI evidence chunks.
- The old point evidence system used `experiment_video_point_evidence` keyed by legacy `(experiment_id, point_key)`. That binding is invalid after the new catalog seed. Canonical `source_chunks` and embeddings remain valid candidate corpora, but point-to-chunk bindings must be regenerated against catalog node identities.
- The user clarified an important product invariant: static chunk binding is optional fallback/supplemental evidence, not the only AI consumption path. Even newly created points without static binding remain AI-consumable through generated queries plus dynamic RAG/BGE rerank.
- The current catalog-node evidence generator is only a stub that records the future contract: target catalog node id or seed key, include full catalog path in query context, and reject legacy point identity.
- ES indexing already follows an outbox/state style through `experiment_catalog_point_search_index_state`. Video processing already uses a worker. RAG evidence refresh should follow the same observable-job style rather than blocking teacher saves.
- `web-teacher`, `web-student`, and `web-admin` are being split. Product intent is that every teacher account has full teacher-console access, while `web-admin` exists only for operational teacher-account management.
- Recent UI research settled several teacher catalog editor decisions: chapter switch should live in the chapter/title area; the right workbench should use a title/info card plus tabbed content; tree drag/drop must behave like a modern online file tree; "管理摘要" and "老师备注" should become one teacher-only teaching note.

## Goals / Non-Goals

**Goals:**

- Preserve the complete context of the catalog, UI, AI/RAG, ES, question-bank, and permission discussions in a single OpenSpec roadmap.
- Define seven spec areas with explicit dependency order so later implementation can be split safely.
- Make catalog point node identity the shared contract for teacher authoring, ES search, dynamic RAG, static evidence bindings, and future question generation.
- Define frontend equation authoring as a teacher-friendly multi-equation input and preview problem, while assigning parsing, normalization, validation, and derived AI/ES/RAG fields to the backend.
- Define controlled jobs for ES and RAG evidence refresh, including automatic and manual triggers.
- Define teacher-visible AI context inspection without exposing raw RAG diagnostics to students.
- Define old question-bank reset and evidence-readiness gates before any new AI question generation.

**Non-Goals:**

- This roadmap does not implement the seven specs.
- This roadmap does not choose a final third-party chemistry parser or balancing engine. It sets product and backend ownership requirements so implementation can evaluate libraries in a focused spike.
- This roadmap does not require Redis, RabbitMQ, Celery, or RQ in the first implementation. Those remain future scale options.
- This roadmap does not publish raw source chunks or RAG diagnostics to student pages.
- This roadmap does not recreate the old experiment/point data model or preserve invalid legacy question/evidence seed bindings.

## Decisions

### Decision 1: Use one umbrella change with seven spec files

This work crosses data model, frontend authoring, backend jobs, AI/RAG, and question-bank gates. Creating one umbrella change keeps the dependency graph and cross-cutting terms in one place. Each capability has its own spec file so later chats can implement one phase at a time.

Alternative considered: create seven independent changes immediately. Rejected for this stage because the user explicitly asked not to lose the full chain of context; independent changes would repeat or omit critical assumptions about catalog-node identity, static-vs-dynamic evidence, and destructive legacy cleanup.

### Decision 2: Order the specs by data dependencies, not by UI visibility

The implementation order is:

1. `experiment-catalog-tree`: authoritative catalog identity, seed rules, legacy cleanup, and 30-sample mapping.
2. `teacher-experiment-catalog-editor`: teacher UI continuity around the stable catalog model.
3. `web-console-role-boundaries`: teacher/admin/student console boundary and universal teacher access.
4. `catalog-point-chemical-equation-authoring`: multi-equation authoring and backend-owned normalization.
5. `catalog-point-index-evidence-jobs`: ES and RAG evidence jobs using stable point content.
6. `catalog-point-ai-context-workbench`: teacher inspection of static evidence, dynamic RAG probes, query strategy, and runtime status.
7. `catalog-node-question-generation-gate`: question-bank reset and generation gates after evidence readiness.

Some phases can run in parallel after the catalog identity is stable. `teacher-experiment-catalog-editor` and `web-console-role-boundaries` are mostly independent. `catalog-point-ai-context-workbench` must not run ahead of evidence job contracts. `catalog-node-question-generation-gate` must remain last because it depends on point context and evidence readiness.

### Decision 3: Keep full directories and leaf-point semantics

The authoritative docs seed must preserve the full chapter catalog tree. Directories are not "empty points" and must not be dropped just because they have no student point content. Leaf nodes are experiment points. The 30 sample point file is a sample-data mapping problem, not a replacement for the full tree.

Alternative considered: seed only leaf points. Rejected because it destroys the directory structure the teacher workspace and student navigation are built around.

### Decision 4: Frontend equation editing is friendly input; backend owns meaning

Teachers need a simple way to enter one or more reaction equations. The frontend should provide multiple rows, helper buttons, autocomplete where useful, and mhchem/KaTeX preview. It should not be the source of truth for parsing or AI/ES structure.

Backend parsing must accept raw teacher strings and return normalized representations such as canonical mhchem, plain search text, species/formulae, reaction participants, validation warnings, and derived query hints. These derived fields become the trusted AI/ES/RAG input.

Alternative considered: embed Ketcher, MarvinJS, or ChemDoodle as the default editor. Rejected as the default path because those are structure/reaction drawing tools, heavier than the current high-school inorganic experiment need. They may remain future advanced editors for molecular structure diagrams.

### Decision 5: Static point evidence is fallback/supplemental, not the AI path itself

Each catalog point can be consumed by AI in two ways:

- Dynamic path: generate one or more retrieval queries from catalog path, point title, point content, equations, videos, and related context, then use RAG/BGE recall and rerank.
- Static path: store selected catalog-node chunk bindings as fallback/supplemental evidence when RAG is unavailable, slow, or needs trustworthy extra context.

The absence of a static binding must not mean the point is "not AI-consumable." It means fallback evidence is missing or stale, and the dynamic path remains available when RAG runtime is healthy.

### Decision 6: Use controlled jobs before adding a broker

ES updates can be quick, but RAG evidence refresh can require high-precision BGE rerank and may be slow or fail. Both need status, retry, and manual trigger controls.

The first implementation should use a Postgres-backed job/outbox model consistent with existing ES index state and video-worker patterns. A separate Redis/Rabbit/Celery/RQ stack should be introduced only when throughput, distributed scheduling, or operational requirements justify it.

### Decision 7: Question generation remains blocked until catalog-node evidence is ready

The old question bank and old point evidence are invalid after the new catalog seed. The safe baseline is an empty question bank. AI question generation must require target catalog node ids and a fresh evidence package marked compatible with catalog-node identity.

Teacher prompts may refine generated drafts, but publication remains explicit and machine-gradable objective question validation still applies.

## Risks / Trade-offs

- [Risk] One umbrella change is large. -> Mitigation: keep seven spec files and phase-ordered tasks so implementers can split actual work safely.
- [Risk] Existing completed changes already modified some behavior. -> Mitigation: this roadmap treats completed work as baseline and records only additional or stabilizing requirements.
- [Risk] Chemical equation parsing becomes too broad. -> Mitigation: first support teacher-friendly entry plus backend normalization/warnings; defer full balancing/perfect parser guarantees unless required.
- [Risk] RAG evidence jobs are slow on CPU BGE. -> Mitigation: make refresh asynchronous, observable, retryable, and manually triggerable; mark evidence stale instead of blocking saves.
- [Risk] Teachers confuse student display content with AI evidence. -> Mitigation: the AI context workbench must label static evidence, dynamic RAG probes, and student-facing content separately.
- [Risk] Legacy evidence or question data leaks into new generation. -> Mitigation: validation must fail if generated evidence packages use legacy `(experiment_id, point_key)` identity after reset.
- [Risk] Universal teacher access removes permission granularity. -> Mitigation: keep operational account management in `web-admin`, but do not hide teacher workflows from teacher accounts.

## Migration Plan

1. Stabilize the catalog seed contract: import full docs tree, preserve directories, identify leaves as points, map 30 samples to catalog nodes, and reject legacy-only identities.
2. Preserve or re-verify catalog editor UI behavior already completed so new point content fields do not regress the tree/workbench experience.
3. Stabilize web console split and teacher access so AI context and learning-assistant routes are visible to all teacher accounts.
4. Migrate point content from single `principle_equation` to a multi-equation model while keeping old values readable during migration.
5. Add backend reaction normalization APIs and store derived fields used by ES and AI/RAG.
6. Add controlled ES/RAG job APIs and worker behavior; wire save/publish/move/delete triggers to mark ES and evidence state pending/stale.
7. Add point AI context workbench once evidence/job contracts exist.
8. Keep question bank empty or inactive until catalog-node evidence readiness gates pass; then enable AI generation in teacher-reviewable drafts only.

Rollback should disable new job triggers, retain catalog point content, and keep question generation gated. It must not restore invalid legacy evidence/question-bank seeds as authoritative data.

## Implementation Landmarks

Use these current repository landmarks before implementing tasks. They are not exhaustive, but they prevent a new implementation pass from rediscovering the same context.

- Catalog point request/response schemas currently live in `server/app/catalog_tree_schemas.py`. The existing point content model still exposes a single `principle_equation`.
- Teacher point content UI currently lives under `apps/web-teacher/src/features/catalog-tree/`, especially `CatalogNodeContentPanel.tsx`, `CatalogTreeWorkspacePage.tsx`, `CatalogTreeNodeList.tsx`, `CatalogTreeRow.tsx`, and `catalogTreeMappers.ts`.
- Existing chemistry extraction for search is in `server/app/chemistry_search.py`. It extracts formulae, aliases, and reaction features from text; it is not yet a full multi-equation parser.
- Student ES search document construction for catalog points is in `server/app/domains/catalog_tree/search_documents.py`; it intentionally excludes teacher-only notes and raw AI evidence.
- ES sync state and diagnostics use `experiment_catalog_point_search_index_state`, created in `server/migrations/020_experiment_catalog_tree.sql`, with runtime helpers in `server/app/domains/video_library/index_client.py`.
- The current catalog-node evidence generator is `scripts/generate_catalog_node_default_evidence.py`; it is only a planning stub and must be expanded or replaced for real catalog-node evidence.
- The retired but useful GPU/BGE evidence strategy is in `scripts/generate_video_point_default_evidence.py`; reuse its retrieval/rerank ideas only after changing identity from legacy `(experiment_id, point_key)` to catalog node id or catalog seed key.
- Learning assistant fixed point evidence currently hydrates legacy `experiment_video_point_evidence` in `server/app/domains/assistant/agent.py` through `server/app/repositories.py`. This path must be migrated or bypassed for catalog-node evidence; do not treat legacy rows as valid after reset.
- Existing mhchem rendering support is already present in teacher/student markdown renderers and assistant output normalization. Multi-equation authoring should reuse mhchem preview/rendering where useful, while backend normalization remains authoritative.
- Docker Compose currently has separate `web-student`, `web-teacher`, `web-admin`, optional `bge-rag`, and `video-worker` services. The first job implementation should fit this stack before adding an external broker.
- Authoritative seed/sample inputs discussed in the research chain include `docs/实验目录_整理版.md` and `docs/30点位例子.txt`, plus generated files under `data/seed/experiment_catalog/`.

## Execution Guidance

- Do not attempt to revive `apps/admin-web` or `apps/student-web` as product targets. The active split is `apps/web-teacher`, `apps/web-student`, and `apps/web-admin`.
- Treat the worktree as possibly dirty from parallel work. Read files before editing and do not revert unrelated changes.
- Complete tasks in phase order unless the user explicitly scopes a smaller phase. In particular, do not start the AI context workbench before job/evidence state contracts exist, and do not enable question generation before evidence readiness gates exist.
- Destructive cleanup is allowed for old question-bank seed data, old point evidence seed data, and old video point reference relationships. It is not allowed for canonical `source_chunks`, canonical embeddings, source documents, or the new catalog seed.
- Static chunk binding is optional fallback/supplemental evidence. A newly created point with no static binding is still AI-consumable through structured point context plus dynamic RAG when runtime policy and health allow it.
- Frontend chemical equation editing must remain assistive. Backend preview/save responses are the only trusted source for normalized reaction records and derived AI/ES/RAG fields.
- Prefer focused tests at each phase: seed validation for phase 1, component/Playwright checks for phase 2, route/auth tests for phase 3, backend parser/API tests for phase 4, job/worker tests for phase 5, non-leakage/diagnostic tests for phase 6, and generation-gate tests for phase 7.

## Open Questions

- Which chemistry parser/balancer library, if any, should backend use after the initial normalization spike?
- Should equation validation block publishing or only warn when equations are parseable but not balanced?
- What exact high-precision BGE rerank limits should catalog-node evidence refresh use for CPU and GPU deployments?
- Should manual RAG probe query editing be allowed in the AI context workbench, or should teachers only choose from generated query variants?
- What minimum evidence readiness threshold is enough for question generation: at least one selected chunk, separate experiment/theory chunks, or score-based acceptance?
