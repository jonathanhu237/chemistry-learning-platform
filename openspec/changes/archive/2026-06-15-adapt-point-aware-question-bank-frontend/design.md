## Context

The default bank has been replaced by a reviewed point-aware artifact: every published question has experiment point bindings, source references, source audit metadata, and single-choice option links where applicable. The current admin question bank page is still chapter-first and only shows point metadata in the question modal. The analytics backend already stores point-aware attempt metadata, but the class weak-point endpoint has an incomplete point aggregation query and the frontend still renders student detail as raw JSON.

## Goals / Non-Goals

**Goals:**
- Make the main question bank workspace reflect the production data model: experiment first, point aware, evidence visible.
- Keep the UI consistent with the current admin console: Ant Design tables, cards, tags, compact filters, and focused modal detail.
- Show useful teacher-facing diagnostics: primary point titles, evidence status, source refs, option diagnostic roles, and point weak analytics.
- Fix the weak-point analytics endpoint so the point-aware frontend has reliable data.

**Non-Goals:**
- Do not change imported question content or rebuilt artifact files.
- Do not add manual live editing, JSON import, or publish controls to the teacher question bank page.
- Do not introduce AI grading or free-form answer judging.
- Do not redesign unrelated admin pages.

## Decisions

1. Use existing `/api/admin/question-banks` and `/api/admin/question-banks/questions` for the primary question bank UI.
   - This keeps the UI experiment-oriented without a new migration.
   - The old chapter endpoints remain available for compatibility and assistant work.

2. Keep the two-pane question bank workspace, but make the left pane an experiment bank navigator instead of a chapter navigator.
   - This preserves the established admin interaction model while matching the imported bank.
   - Per-experiment counts are already available from `QuestionBankSummary`.

3. Derive point filters from returned question metadata in the selected experiment.
   - The imported bank stores `metadata.primary_points` and `metadata.primary_point_keys`.
   - This avoids adding a new endpoint before the product has a stable need for cross-experiment point search.

4. Display source refs and option links only inside the focused question detail modal.
   - The list stays scan-friendly.
   - Detailed evidence remains visible for audit without crowding the table.

5. Return both legacy KP weak items and point-aware weak items from the existing weak-point endpoint.
   - This keeps existing analytics behavior intact.
   - The frontend can prioritize `point_items` when available and still show legacy fallback.

## Risks / Trade-offs

- Point filter options are derived from the current experiment's loaded questions, so they do not show points with zero questions. This is acceptable for browsing imported questions; a later coverage dashboard can include zero-coverage points from the experiment framework inventory.
- The assistant preview remains chapter-scoped for now. The primary release path is read-only inspection and analytics; assistant rework should be handled as a separate change.
- Question detail source refs may be verbose. The modal will use compact tags and descriptions rather than permanently expanding every source line in the table.

## Migration Plan

1. Deploy the backend weak-point endpoint fix.
2. Deploy the admin web question bank UI changes.
3. Verify the imported default bank renders 77 experiments and 2,310 published questions.
4. If a frontend issue appears, the imported bank remains usable through the existing APIs and the UI can be rolled back independently.

## Open Questions

- Whether a later teacher workflow should let the assistant generate repairs scoped directly to an experiment point rather than a theory chapter.
