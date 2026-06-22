## 1. Backend Node Status Model

- [x] 1.1 Inventory current catalog validation, publication, canonical content, media binding, ES job, and RAG evidence fields used by the teacher workbench.
- [x] 1.2 Define backend node-status response types for `primary_state`, `primary_reason`, `core_readiness`, `visibility`, `async_consumption`, and grouped `conditions`.
- [x] 1.3 Implement point status derivation with priority `archived`, `blocked`, `needs_content`, `needs_video`, `draft`, `ready`, `published`, `sync_attention`.
- [x] 1.4 Implement core readiness checks for the three learning fields plus binary experiment video presence.
- [x] 1.5 Implement placement/canonical visibility derivation so `student_available` reflects published path visibility while content/video gaps remain quality states.
- [x] 1.6 Implement directory status aggregation from descendant point actionability and directory publication/archive state.
- [x] 1.7 Convert existing validation errors and warnings into stable node-status condition keys with Chinese teacher-facing messages and repair actions.
- [x] 1.8 Keep raw validation/job messages available only for advanced diagnostics while preventing them from becoming primary status copy.

## 2. API And Frontend Types

- [x] 2.1 Expose node status on catalog tree card, selected node detail, child-list, and search-result payloads used by `web-teacher`.
- [x] 2.2 Preserve existing validation fields during migration so old callers do not break while the teacher UI switches to node status.
- [x] 2.3 Update `apps/web-teacher` catalog API types, mappers, hooks, and test fixtures to consume `node_status`.
- [x] 2.4 Add type guards or fallback mapping so partially migrated backend responses still render controlled unknown-status states.

## 3. Lightweight Tree Status UI

- [x] 3.1 Replace default tree-row warning rendering with one primary node-status marker per row.
- [x] 3.2 Render directory descendant action counts as compact aggregate metadata rather than per-condition badges.
- [x] 3.3 Render point rows with stable icon/title/action layout and binary video status only where it is the selected primary reason or tooltip detail.
- [x] 3.4 Add Chinese accessible labels and concise tooltips for `缺内容`, `缺视频`, `草稿`, `已发布`, `同步异常`, and `已归档`.
- [x] 3.5 Add focused status filters for `全部`, `待处理`, `缺内容`, `缺视频`, `已发布`, and `同步异常`.
- [x] 3.6 Verify long titles, hover actions, trailing counts, and status markers do not overlap at common admin widths.

## 4. Selected Node Status Panel

- [x] 4.1 Rename the visible `发布检查` tab/panel to `节点状态` throughout the teacher catalog workspace.
- [x] 4.2 Rebuild the panel into `核心完整性`, `学生可见性`, and `同步诊断` sections.
- [x] 4.3 Show missing learning fields and binary video state in `核心完整性`.
- [x] 4.4 Show placement state, shared canonical content state, and `student_available` in `学生可见性`.
- [x] 4.5 Show ES search state, AI/RAG evidence state, freshness, last error summary, and retry/refresh actions in `同步诊断`.
- [x] 4.6 Show placement node id and shared canonical point id together when they help teachers understand reused content.
- [x] 4.7 Move raw ids, raw backend validation messages, job payloads, and low-level enum details into advanced/debug surfaces only.

## 5. Video Binding Semantics

- [x] 5.1 Update teacher-facing video readiness copy to `有视频` or `无视频`.
- [x] 5.2 Remove wording that says or implies "at least one publishable video" from tree, header, panel, tooltip, and tests.
- [x] 5.3 Keep the catalog video panel binding-only and preserve navigation to the separate media/video upload workflow.
- [x] 5.4 Handle legacy multiple video bindings as advanced diagnostics while keeping primary point status binary.
- [x] 5.5 Add tests proving binding, unbinding, publishing, and unpublishing update binary node status correctly.
- [x] 5.6 Prevent new video binding until the three learning fields are complete, while leaving existing bindings manageable.

## 6. ES/RAG Async Consumption Boundary

- [x] 6.1 Map ES pending/running/succeeded/failed/stale/disabled/unavailable states into `async_consumption.search_index`.
- [x] 6.2 Map RAG evidence pending/running/available/failed/stale/disabled/unavailable states into `async_consumption.ai_evidence`.
- [x] 6.3 Ensure pending, running, and stale async states do not override missing content, missing video, draft, ready, or published primary states.
- [x] 6.4 Ensure failed or unavailable async state on an otherwise published point escalates to `sync_attention`.
- [x] 6.5 Ensure async retry/refresh actions live in sync diagnostics rather than the default point content form.

## 7. Tests And Visual QA

- [x] 7.1 Add backend unit tests for point status priority, content completeness, binary video presence, placement/canonical visibility, directory aggregation, and async sync attention.
- [x] 7.2 Add backend API tests proving node status appears on tree cards, detail payloads, child payloads, and search results.
- [x] 7.3 Add frontend unit tests for status mappers, tree row markers, directory aggregation, filters, and node-status panel grouping.
- [x] 7.4 Add regression tests proving raw English messages such as `Canonical point content has not been saved` do not appear in primary teacher-facing UI.
- [x] 7.5 Run Playwright or equivalent visual checks for expanded directory, collapsed directory, selected point, missing content, missing video, sync attention, long title, hover/focus row actions, and narrow admin width.
- [x] 7.6 Run `openspec validate replace-catalog-publish-checks-with-node-status --strict` and relevant backend/frontend test commands before marking implementation complete.

## 8. Migration And Cleanup

- [x] 8.1 Keep compatibility adapters from legacy validation payloads to node status until all teacher surfaces consume `node_status`.
- [x] 8.2 Remove obsolete `CatalogPublishChecksPanel` naming or wrap it with a new `CatalogNodeStatusPanel` during migration.
- [x] 8.3 Update teacher-facing copy snapshots, fixtures, and documentation to use `节点状态`.
- [x] 8.4 Audit student APIs to confirm node status changes do not expose teacher-only diagnostics or raw job details.
- [x] 8.5 Document the final status taxonomy and priority rules for future catalog, search, and AI workbench changes.

## 9. Related Experiment Semantics And Editor UX

- [x] 9.1 Rename teacher-facing canonical reuse wording from ambiguous `共享实验内容` to `多目录共享实验` / `共享目录` where it would otherwise be confused with related experiments.
- [x] 9.2 Change generated related-experiment defaults to all other point nodes under the same direct parent directory, preserving display order and excluding archived/self-canonical targets.
- [x] 9.3 Redesign the related experiments panel as a readable ordered list with drag handles, up/down fallback controls, optional display names, and readable source labels.
- [x] 9.4 Add reset-to-default behavior that clears stored manual/default-override rows so same-parent generated defaults are returned.
- [x] 9.5 Keep sibling-directory experiments as manually addable/searchable candidates rather than automatic defaults consumed by student/search/RAG.
