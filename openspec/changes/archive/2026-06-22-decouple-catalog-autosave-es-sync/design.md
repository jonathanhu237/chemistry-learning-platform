## Context

The teacher catalog editor now behaves like an online document editor: teachers edit content directly and the frontend autosaves routine changes without a manual save button. The current backend write path does not yet match that product model. `save_point_content` currently sets point content to `draft` on every save and queues ES delete work for every active placement, even when the point was already published and the teacher only changed one field.

That creates three problems:

- Publication visibility, editor persistence, and downstream ES/RAG consumption are coupled.
- Autosave can generate many expensive and semantically noisy ES/RAG jobs.
- Editing a published point can incorrectly make the search/student projection behave as if the content were withdrawn.

The catalog model also has shared canonical point content with multiple point placements. ES documents are placement-scoped because directory context matters, while point content may be canonical/shared. Any sync policy must therefore fan out to affected active placements without treating a directory or canonical point as the final student search hit.

## Goals / Non-Goals

**Goals:**

- Preserve the teacher UX of direct autosave for point content, directory note/title edits, and point title edits.
- Preserve publication state when a teacher edits already published content.
- Separate "saved to backend" from "consumed by ES/RAG".
- Reduce ES/RAG job churn by coalescing soft edits on the backend.
- Use a 30 second quiet window and a 3 minute maximum wait window for autosave-driven ES updates.
- Keep hard visibility changes immediate and auditable.
- Avoid ES writes when the resulting student-search document hash has not changed.
- Keep teacher-only notes out of student search and out of ES-trigger decisions when no indexed field changes.
- Surface downstream sync state in diagnostics rather than as the primary content/video readiness state.

**Non-Goals:**

- Introduce a new external queue broker such as Redis, RabbitMQ, Celery, or RQ.
- Add a separate "republish" product concept for already published content.
- Add separate draft/published snapshots in this change.
- Change ES analyzer, chemistry synonym, or ranking semantics beyond sync timing and no-op detection.
- Make RAG refresh block teacher editing or publishing.
- Move upload or media processing responsibilities into the catalog editor.

## Decisions

### Decision 1: Publication state remains independent from autosave

Published content edits SHALL not change `content_status` or node `status` from `published` to `draft`. Autosave is a persistence operation. Explicit visibility actions such as unpublish, archive, delete, hide, or path publication changes remain the only operations that remove student visibility or queue ES delete work.

Alternative considered: create a separate draft/published snapshot model. That would be appropriate for a "republish" workflow, but the current product semantics are closer to an online document: the object remains published while its saved content changes.

### Decision 2: Backend owns ES trigger decisions

The frontend SHOULD send routine autosave updates normally, but it MUST not be responsible for deciding whether ES should run. The backend has the canonical context needed to decide whether a change affects student-searchable fields, directory paths, video readiness, or related-point text.

The backend will rebuild or project the student-search document candidate and compare a deterministic hash with the last indexed hash. If the hash is unchanged, no ES write is required.

Alternative considered: frontend field-level trigger lists. This would be fragile because frontend previews do not own normalized equations, directory path context, related link resolution, or placement fanout.

### Decision 3: Soft edits use coalesced delayed jobs

Soft edits include autosaved point content, point title edits, directory title/note edits that affect descendants, related-link edits, and video binding changes that rebuild search documents but do not immediately remove visibility.

For soft edits:

- the affected placement index state is marked stale or pending;
- an `es_upsert` job is inserted or updated with an idempotency key per placement/action;
- `run_after` is set to at least `now + 30 seconds`;
- repeated soft edits update the existing open job instead of creating new work;
- each open job tracks a first-seen timestamp or equivalent payload so continuous edits cannot postpone sync beyond 3 minutes.

Worker claim logic already honors `run_after`, so this can be implemented with the existing Postgres-backed job table by extending enqueue behavior rather than adding a new queue.

Alternative considered: frontend debounce only. This is insufficient because multiple browser tabs, API clients, AI actions, imports, and backend-side mutations can bypass frontend timing.

### Decision 4: Hard changes run immediately

Hard changes are visibility or operator actions where stale ES results are unsafe or teacher/operator intent is explicit:

- unpublish;
- archive;
- delete;
- path becomes unpublished;
- manual ES refresh/delete;
- retry;
- destructive rebuild;
- bulk import finalization when the intended result is immediate indexing.

Hard changes use `run_after = now()` and keep existing audit fields and trigger sources.

### Decision 5: ES worker rechecks the final document

When an ES job runs, it SHALL rebuild the current student-search document from backend data instead of trusting stale payload text. It then recomputes the document hash:

- if the action is upsert and the hash matches the indexed hash, mark the state synced without writing ES;
- if the hash differs, write the current document and update `document_hash` and `indexed_at`;
- if the point is no longer student-searchable, perform or keep the correct delete/disable action.

This protects against stale queued payloads and collapses many autosave events into the latest projection.

### Decision 6: RAG evidence freshness is separate from ES

RAG evidence state remains its own state machine. Content/path/video/related changes may mark evidence stale and optionally schedule refresh according to existing configuration. The autosave UI must not wait for RAG, and ES success must not imply RAG freshness.

### Decision 7: Teacher UI labels separate save and sync

The content panel autosave indicator describes only backend persistence:

- `正在保存`
- `已保存`
- `保存失败`

The sync diagnostics describe downstream consumption:

- `ES 已同步`
- `ES 待同步`
- `ES 同步中`
- `ES 同步失败`
- analogous RAG evidence states.

Teacher-facing helper copy must explain the expected delay: after routine edits, search indexing normally updates after about 30 seconds without further edits; during continuous editing, the backend still synchronizes at least once within about 3 minutes.

## Risks / Trade-offs

[Risk] Published content edits become visible to student detail before ES catches up, so search results can lag behind detail content.  
Mitigation: show ES/RAG sync state in diagnostics and document the 30 second/3 minute policy; keep student detail reading from the authoritative database rather than ES.

[Risk] Coalesced jobs might be delayed forever if run-after is repeatedly pushed.  
Mitigation: store or preserve the first soft-change timestamp and cap postponement at 3 minutes.

[Risk] Directory edits can fan out to many descendant placements.  
Mitigation: coalesce per placement/action, batch writes, and keep manual subtree rebuild available for operators.

[Risk] Hash comparison could miss a field that should affect search.  
Mitigation: define the search-document projection as the single hash source and add tests for title, path, principle, reaction equations, phenomenon, safety, related links, and video readiness.

[Risk] RAG auto-refresh may still create excessive work if enabled for each autosave.  
Mitigation: use the same stale/coalesce principle for evidence refresh or leave evidence stale until manual/policy refresh, depending on configured trigger policy.

## Migration Plan

1. Update backend save semantics so published point content remains published after routine edits.
2. Extend job enqueue helpers to accept delayed soft-sync scheduling and preserve/update `run_after` on open idempotent jobs.
3. Add a way to mark index state stale/pending without immediate delete for published routine edits.
4. Add or reuse payload metadata for soft-sync first-seen time so 3 minute maximum wait can be enforced.
5. Update ES worker no-op behavior to recompute the current document hash before writing.
6. Update frontend copy and autosave status documentation to separate backend save state from downstream sync state.
7. Add regression tests before deployment.

Rollback is straightforward for frontend UX copy. Backend rollback must avoid returning to the old behavior where published edits queue ES delete; if rollback is required, disable delayed jobs by setting the soft window to zero rather than coupling autosave to unpublish semantics again.

## Open Questions

- Should the 30 second quiet window and 3 minute maximum wait be configurable through settings, or fixed constants for the first implementation?
- Should RAG evidence refresh use the same 30 second/3 minute coalescing immediately, or should this change only mark evidence stale unless manual refresh is requested?
- Should directory teacher-only note edits ever affect descendant ES/RAG, or should only directory title/path/visibility changes fan out?
