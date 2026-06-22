## Why

The teacher catalog workbench now has a Google-Docs-like autosave experience, but backend point saves still treat every edit as a publication-state change and immediately enqueue ES/RAG work. This incorrectly mixes three concerns: publication visibility, editor persistence, and downstream search/evidence synchronization.

This change preserves the good authoring UX while making ES/RAG updates controlled, coalesced, observable, and faithful to the product model: an already published point remains published while teachers edit it, and derived search/evidence state catches up asynchronously.

## What Changes

- Keep published catalog points published when teachers edit title, point content, equations, related links, or video bindings unless the teacher explicitly unpublishes, archives, hides, or deletes the node.
- Treat autosave as content persistence, not as publication withdrawal or immediate ES execution.
- Introduce backend-side coalescing for ES sync:
  - soft edits mark affected point-placement documents as stale or pending;
  - equivalent ES upsert jobs are merged per placement/action;
  - soft-edit jobs use a 30 second quiet window;
  - continuous edits must still sync at least once within a 3 minute maximum wait window.
- Preserve immediate ES delete/update behavior for hard visibility changes such as unpublish, archive, delete, manual refresh, manual delete, retry, and bulk rebuild.
- Use document hashes to avoid indexing when the student-search document did not materially change.
- Ensure teacher-only notes and other non-searchable fields do not trigger ES jobs when no indexed document field changes.
- Keep RAG evidence freshness separate from ES sync; content edits may mark evidence stale or schedule refresh according to policy, but teacher saves must not block on RAG.
- Update the teacher autosave copy/state model so `已保存` means "saved to backend", while ES/RAG state is shown as downstream `已同步 / 待同步 / 同步中 / 失败` diagnostics.
- Update tests to cover published-content edits, autosave coalescing, hard visibility changes, hash no-op behavior, and diagnostics visibility.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `experiment-catalog-tree`: Clarify that editing already published catalog point content or titles preserves publication visibility; only explicit visibility actions change publication state.
- `teacher-experiment-catalog-editor`: Define autosave as backend persistence with a visible save-state indicator, no manual save button for routine content edits, and no implication that ES/RAG has already consumed the change.
- `catalog-point-index-evidence-jobs`: Define stale/pending derived-sync semantics, 30 second quiet-window coalescing, 3 minute maximum-wait sync, hash-based no-op behavior, and hard-change immediate job behavior.

## Impact

- Backend catalog point content save, node update, related-link, media-binding, publication, archive/delete, and move paths.
- Postgres-backed `experiment_catalog_point_search_index_state` and `experiment_catalog_point_jobs` orchestration, especially idempotency keys, `run_after`, and document hash handling.
- ES search document builders and student video-library indexing diagnostics.
- RAG evidence stale/refresh policy for catalog point context.
- Teacher catalog editor autosave state, content form behavior, and diagnostics wording.
- Tests for catalog content save semantics, job coalescing, ES worker no-op, student read models, and frontend autosave UX.
