## 1. Authoritative Catalog Tree And Legacy Reset

- [x] 1.1 Audit current catalog seed docs, generated seed files, and import reports to identify the authoritative input path for the updated experiment catalog.
- [x] 1.2 Update or verify catalog seed generation so it preserves the full chapter directory hierarchy and only marks leaf experiment items as point nodes.
- [x] 1.3 Add validation that directory nodes remain first-class tree nodes and are not collapsed into point-only flat lists.
- [x] 1.4 Treat placeholder content such as no corresponding experiment content as empty content during import.
- [x] 1.5 Remove or retire legacy point-to-chunk evidence seed rows keyed only by `(experiment_id, point_key)` while preserving canonical `source_chunks` and embeddings.
- [x] 1.6 Remove or deactivate old question-bank seed rows that depend on invalid legacy point identity.
- [x] 1.7 Implement or verify validation that active point evidence and question seed data target catalog node id or stable catalog seed key.
- [x] 1.8 Map the 30 sample point examples to concrete catalog point nodes using semantic title/path/reagent matching.
- [x] 1.9 Add explicit override/reporting support for ambiguous 30-sample mappings.
- [x] 1.10 Ensure known sample wording corrections such as `NaClO + 品红溶液` are represented in mapping reports and tests.
- [x] 1.11 Add tests covering full-tree import, leaf-point semantics, placeholder handling, legacy cleanup, and sample mapping failures.
- [x] 1.12 Update seed/operations documentation with the new source-of-truth and destructive reset rules.

## 2. Teacher Catalog Editor Continuity

- [x] 2.1 Audit the current `web-teacher` catalog editor against the title-card, tabbed workbench, and modern tree behavior requirements.
- [x] 2.2 Move chapter switching into the chapter/title area and remove any redundant left-sidebar chapter dropdown.
- [x] 2.3 Ensure chapter switching refreshes tree, selection, validation summary, and right workspace without stale actionable node details.
- [x] 2.4 Verify directory and point title cards show identity, path/status summary, and actions without duplicated label-style tags.
- [x] 2.5 Polish the no-selection empty state so it visually belongs to the current workbench surface.
- [x] 2.6 Ensure point and directory panels remain inside a coherent tabbed workbench below the title card.
- [x] 2.7 Verify drag preview, drop hover feedback, invalid-drop feedback, and collapse/expand behavior for tree moves.
- [x] 2.8 Ensure hovering over a collapsed directory during drag can expand the target without losing drop intent.
- [x] 2.9 Ensure successful move/reorder operations refresh or patch local tree state and keep the moved node visible when possible.
- [x] 2.10 Fix tree connector geometry so first-level and deeper rows use short aligned horizontal branches without overlapping expand controls.
- [x] 2.11 Rename overlapping management-summary/teacher-note concepts to one teacher-only teaching note across create and edit flows.
- [x] 2.12 Add component/unit tests and Playwright screenshots for chapter switching, drag/drop, connector geometry, empty state, and teaching-note wording.

## 3. Web Console Role Boundaries

- [x] 3.1 Audit current `web-admin`, `web-teacher`, and `web-student` routes, menus, API clients, and auth guards after the frontend split.
- [x] 3.2 Ensure `web-admin` exposes only operational teacher-account management workflows.
- [x] 3.3 Ensure `web-teacher` exposes all teacher workflows to every authenticated teacher account without per-feature permission hiding.
- [x] 3.4 Ensure `web-student` exposes no teacher diagnostics, account operations, raw RAG traces, or teacher-only notes.
- [x] 3.5 Restore any learning-assistant or AI access/test teacher page that was hidden or removed during route/permission refactors.
- [x] 3.6 Rebuild restored AI/learning-assistant pages through current `web-teacher` feature modules and typed API clients rather than deleted `admin-web` code.
- [x] 3.7 Implement or verify `web-admin` teacher-account create, disable, enable, rename, delete, and password reset flows.
- [x] 3.8 Update backend authorization so teacher-console APIs authorize all teacher accounts consistently.
- [x] 3.9 Add route/menu tests proving all teachers see teacher workflows and students/operators do not see the wrong console features.
- [x] 3.10 Verify Docker/frontend build targets and local ports for all three web consoles.

## 4. Multi-Equation Point Authoring

- [x] 4.1 Design the database/API migration from single `principle_equation` to a multi-equation point content model.
- [x] 4.2 Preserve existing single-equation values by migrating each non-empty value into one reaction equation row.
- [x] 4.3 Add backend request/response schemas for raw equation rows, normalized records, validation warnings, and derived chemistry fields.
- [x] 4.4 Add a backend preview/normalize endpoint that can parse submitted raw equation rows before final save.
- [x] 4.5 Implement backend normalization for canonical display text, canonical mhchem when available, plain search text, formulae, aliases, participants, and reaction features.
- [x] 4.6 Add backend validation behavior for unsupported notation, parse uncertainty, invalid rows, and suspected imbalance.
- [x] 4.7 Ensure invalid equation rows do not produce misleading ES/RAG/AI derived fields.
- [x] 4.8 Build a teacher-friendly multi-equation editor in `web-teacher` with add, edit, reorder, delete, helper controls, and preview.
- [x] 4.9 Keep frontend preview assistive only; saved meaning must come from backend normalization responses.
- [x] 4.10 Update frontend mappers, form defaults, and tests for equation mode versus text mode.
- [x] 4.11 Update ES document construction to consume backend-derived normalized equation fields.
- [x] 4.12 Update AI/RAG point context construction to include normalized equation records and raw fallback text.
- [x] 4.13 Add regression tests for migrated single equations, multiple equations, invalid equations, text-principle mode, and mhchem rendering.

## 5. Catalog Point ES And RAG Evidence Jobs

- [x] 5.1 Design a Postgres-backed job/outbox model for catalog point job type, node id, trigger source, status, attempts, payload, result, errors, and timestamps.
- [x] 5.2 Add backend job creation helpers with idempotency for repeated equivalent ES and RAG evidence requests.
- [x] 5.3 Expose API endpoints to read point ES state, evidence state, and recent jobs.
- [x] 5.4 Expose API endpoints to manually trigger ES refresh, ES delete/disable, RAG evidence refresh, retry, and delete where appropriate.
- [x] 5.5 Connect publish, unpublish, archive, delete, move, and student-searchable content edits to ES upsert/delete jobs.
- [x] 5.6 Connect point context edits to evidence stale marking or automatic RAG refresh according to configured trigger policy.
- [x] 5.7 Implement worker claiming with database locking or equivalent safeguards so jobs are not executed concurrently by multiple workers.
- [x] 5.8 Reuse existing ES document builder so ES jobs index backend-owned normalized point content.
- [x] 5.9 Adapt the retired GPU/BGE rerank strategy to catalog-node evidence refresh using catalog node id or stable seed key.
- [x] 5.10 Ensure BGE unavailable/timeout failures leave teacher saves intact and record diagnostic job errors.
- [x] 5.11 Add job status display hooks for pending, running, succeeded, failed, stale, disabled, and unavailable states.
- [x] 5.12 Add tests for idempotent job creation, worker claiming, ES upsert/delete, stale evidence marking, manual retry, and BGE failure diagnostics.
- [x] 5.13 Document why the first implementation uses Postgres-backed jobs and what conditions would justify Redis/Rabbit/Celery/RQ later.

## 6. Point AI Context Workbench

- [x] 6.1 Add backend API to return teacher-only AI context summary for a selected catalog point.
- [x] 6.2 Include node id, full catalog path, point title, normalized equations, phenomenon explanation, safety note, related points, videos, publication state, and content freshness in the context summary.
- [x] 6.3 Add static catalog-node evidence binding lookup and display payload with chunk ids, source metadata, roles, review/selection status, and freshness.
- [x] 6.4 Mark missing static evidence as missing fallback evidence rather than "not AI-consumable".
- [x] 6.5 Add dynamic RAG probe API that generates point-context queries and returns recall/rerank diagnostics.
- [x] 6.6 Show generated query variants, fallback query reasons, candidate counts, final evidence, rerank scores, and runtime health in teacher diagnostics.
- [x] 6.7 Add teacher UI tab/panel for AI context in the catalog point workbench.
- [x] 6.8 Show ES and RAG job state with refresh/retry actions where allowed.
- [x] 6.9 Ensure static evidence, dynamic RAG evidence, student-facing content, and teacher-only teaching notes are visually separated.
- [x] 6.10 Ensure student APIs and pages do not expose chunk ids, rerank scores, generated queries, job payloads, or teacher-only diagnostics.
- [x] 6.11 Align learning-assistant point context diagnostics with the same fixed/static evidence versus supplemental dynamic RAG distinction.
- [x] 6.12 Add tests for missing binding, stale binding, successful RAG probe, RAG failure, student non-leakage, and teacher UI rendering.

## 7. Question Bank Reset And Generation Gate

- [x] 7.1 Verify old question-bank seed data is absent or inactive after the catalog reset.
- [x] 7.2 Add teacher question-bank empty/pending-regeneration state when no fresh catalog-node bank exists.
- [x] 7.3 Implement generation readiness checks for target catalog point node ids.
- [x] 7.4 Reject generation when evidence is missing, stale, legacy-keyed, or incompatible with the requested catalog node ids.
- [x] 7.5 Allow dynamic RAG evidence as a recorded generation source when runtime policy permits and static binding is absent.
- [x] 7.6 Build generation prompts from structured catalog point context, normalized equations, videos, related points, and compatible evidence sources.
- [x] 7.7 Preserve separate identity/evidence context for multi-point generation requests.
- [x] 7.8 Store generated questions as teacher-reviewable drafts rather than publishing them directly.
- [x] 7.9 Validate generated candidates for objective type, deterministic answer shape, point node ids, source audit, and evidence lineage.
- [x] 7.10 Block publication of candidates without compatible catalog-node evidence lineage.
- [x] 7.11 Add regeneration coverage/audit reports by chapter, directory, point node, question type, evidence source, accepted drafts, rejected drafts, and unresolved points.
- [x] 7.12 Update question-bank UI to show linked catalog point titles, evidence status, deterministic answer data, and generation lineage without legacy point keys as authoritative metadata.
- [x] 7.13 Add tests for empty baseline, readiness gate failures, dynamic evidence generation, draft validation, publication blocking, and coverage audit output.
