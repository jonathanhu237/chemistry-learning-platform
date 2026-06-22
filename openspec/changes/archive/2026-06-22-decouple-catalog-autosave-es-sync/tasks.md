## 1. Backend Publication Semantics

- [x] 1.1 Update point content save logic so autosaving an already published point preserves `content_status = published` and does not queue ES delete solely because content was edited.
- [x] 1.2 Keep unpublished or incomplete point saves non-searchable without creating an ES upsert until an explicit publish action makes the point visible.
- [x] 1.3 Update point title and catalog node title save paths so published nodes remain published after inline title edits.
- [x] 1.4 Ensure teacher-only notes persist without affecting student search documents, publication visibility, or ES trigger decisions when no indexed field changes.

## 2. ES Soft-Sync Coalescing

- [x] 2.1 Add backend constants or settings for autosave-derived ES sync timing: 30 second quiet window and 3 minute maximum wait.
- [x] 2.2 Extend point job enqueue helpers to accept delayed `run_after` scheduling for soft edits while preserving immediate scheduling for hard visibility/manual actions.
- [x] 2.3 Update idempotent open-job conflict handling so repeated soft edits merge into one placement/action job and push `run_after` forward without exceeding the 3 minute maximum wait from the first unsynced soft edit.
- [x] 2.4 Add a soft ES queue path that marks affected placement index state pending/stale and schedules coalesced `es_upsert` jobs for content, path, related-link, and video-readiness edits.
- [x] 2.5 Keep hard actions such as unpublish, archive, delete, manual refresh/delete, retry, and destructive rebuild on immediate ES jobs.

## 3. Search Document Hashing

- [x] 3.1 Define the deterministic student-search document projection used for hash comparison, including title, chapter/path, point knowledge, normalized reactions, related text, formulae/features, and video readiness.
- [x] 3.2 Update ES worker execution to rebuild the current document at run time instead of trusting queued payload text.
- [x] 3.3 Skip ES writes and mark the placement synced when the rebuilt document hash matches the last indexed hash.
- [x] 3.4 Update successful ES writes to persist document hash, analyzer version where available, indexed timestamp, attempts, and error state.

## 4. RAG Evidence Separation

- [x] 4.1 Ensure autosaved content/context changes mark evidence stale or schedule evidence refresh according to the existing trigger policy without blocking save responses.
- [x] 4.2 Prevent ES success from changing RAG evidence state, and keep diagnostics reporting ES and RAG independently.
- [x] 4.3 Confirm RAG refresh inputs continue to exclude teacher-only video titles, media file names, and teacher-only notes.

## 5. Teacher Autosave UX

- [x] 5.1 Update teacher catalog autosave helper copy to explain that content saves immediately while ES/RAG consumption is asynchronous.
- [x] 5.2 Add visible or discoverable wording for the ES timing policy: normally after about 30 seconds without further edits, and at least once within about 3 minutes during continuous editing.
- [x] 5.3 Keep autosave status labels scoped to backend persistence (`正在保存`, `已保存`, `保存失败`) and keep ES/RAG states in diagnostics or secondary status surfaces.
- [x] 5.4 Verify routine content and directory editing no longer shows persistent manual save buttons for autosaved fields.

## 6. Tests and Validation

- [x] 6.1 Add backend tests proving published content autosave preserves published state and schedules delayed upsert rather than delete.
- [x] 6.2 Add backend tests proving unpublished/draft content saves do not become student-searchable until explicit publish.
- [x] 6.3 Add job tests for soft-edit coalescing, 30 second quiet-window scheduling, 3 minute maximum-wait behavior, and hard-change immediate scheduling.
- [x] 6.4 Add ES worker tests for current-document rebuild, hash no-op, hash change upsert, and delete behavior when visibility is removed.
- [x] 6.5 Add frontend tests or contract checks for autosave labels, removal of manual save buttons, and the 30 second/3 minute sync explanation.
- [x] 6.6 Run focused backend pytest, teacher frontend typecheck/tests, and `openspec validate decouple-catalog-autosave-es-sync --strict`.
- [x] 6.7 Run real Docker e2e against backend, Postgres, and Elasticsearch with a temporary published catalog point; verify soft autosave upsert scheduling, 30 second quiet window, 3 minute coalescing bound, teacher-note-only no-op, ES worker success, and zero leftover temporary DB/ES resources after cleanup.
