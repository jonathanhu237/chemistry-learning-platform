## Context

The teacher catalog workbench uses several related but currently divergent status views:

- Chapter summary counts are computed from each point card's `node_status.primary_state`.
- Directory rows carry `core_readiness.descendant_status_counts`, but those counts currently do not cover every filterable state and do not represent missing content by field.
- The frontend filter matcher uses `primary_state` for direct nodes and directory descendant counts for ancestor inclusion.
- Point content editing treats experiment principle as a section separate from `学生可见内容`, even though the student-facing learning content contract is really `实验原理`, `现象解释`, and `安全提示`.
- Principle mode switching writes form values, schedules autosave, and then triggers query invalidation. Refetched detail can hydrate the form while a mode switch is pending, which can visually revert the selected mode.

The latest observed filter bug follows from this split: `待发布` and `已发布` counts can be non-zero in the summary, while the tree filter returns empty because the directory aggregate does not expose matching descendant `ready` or `published` state in the same form used by `matchesCatalogNodeStatusFilter`.

## Goals / Non-Goals

**Goals:**

- Make the status count, filter, row visibility, and directory aggregate contracts share the same point-state vocabulary.
- Keep `缺内容` as a coarse teacher workflow state while adding structured missing-field keys for `实验原理`, `现象解释`, and `安全提示`.
- Keep top summary chips compact and avoid turning every missing sub-field into a high-emphasis colored status.
- Present the content editor with `学生可见内容` as the home for the three required student-visible fields.
- Ensure principle mode switching is stable under autosave and stale query hydration.
- Preserve existing equation preview, AI assist, save payload normalization, and publication blocking semantics.

**Non-Goals:**

- Do not change the one-video-per-point design.
- Do not change student H5 rendering beyond consuming the same saved learning fields.
- Do not require a new form library, query library, or UI dependency.
- Do not make missing sub-field filters replace the coarse `缺内容` filter.
- Do not make autosave publish or unpublish content.

## Decisions

### Decision 1: Add stable missing-field keys alongside labels

Point status should expose machine-readable missing field keys such as `principle`, `phenomenon`, and `safety`, plus teacher-readable labels such as `实验原理`, `现象解释`, and `安全提示`.

The backend can keep a compatibility label list if useful, but frontend filtering and field targeting must use stable keys. This prevents localized copy changes from breaking filters and tests.

Alternative considered: parse Chinese `missing_fields` strings in the frontend. Rejected because it repeats the current fragility: presentation text becomes filter logic.

### Decision 2: Keep coarse status chips, add low-emphasis focused filters

The high-level overview should remain compact: `目录`, `点位`, `已发布`, `待处理`, plus the existing coarse status chips. Focused missing-field filters belong in the selectable filter-chip area as lower-emphasis choices:

- `缺内容：实验原理`
- `缺内容：现象解释`
- `缺内容：安全提示`

This follows the same pattern as Material-style filter chips: chips refine a data set, while inline form feedback explains what to fix. The UI should not add three more colored warning tags to the overview row.

Alternative considered: split the top `缺内容` statistic into three colored tags. Rejected because it makes the summary visually noisy and overstates sub-field details before the teacher chooses that workflow.

### Decision 3: Directory aggregates cover every filterable state

Directory `node_status.core_readiness.descendant_status_counts` must cover the same status buckets that the filter bar offers, including `ready`, `draft`, and `published`. A filter should never be able to show a non-zero chapter count while hiding all ancestor paths solely because a directory aggregate lacks that state.

Missing-field counts should be a separate map, for example `descendant_missing_field_counts`, so `needs_content` remains a status bucket and `principle/phenomenon/safety` remain field-facet counts.

Alternative considered: make the frontend fetch a separate flat search every time a status filter changes. Rejected for this change because the existing tree can stay lightweight if directory aggregates are complete and aligned.

### Decision 4: Filter matching uses one source of truth

Frontend filter matching should use:

- Direct point: `resolveCatalogNodeStatus(point).primary_state` and missing-field keys.
- Directory: `descendant_status_counts` and `descendant_missing_field_counts`.
- Chapter chip counts: `point_status_counts` and `point_missing_field_counts`.

The frontend must not infer unpublished or published descendants from placement status, content status, or ad hoc media/content conditions that duplicate backend priority rules.

Alternative considered: duplicate the backend's SQL condition logic in TypeScript. Rejected because the current bug is exactly the result of split logic.

### Decision 5: Rehome experiment principle into student-visible content

The point content editor should render:

1. `教学备注`, teacher only.
2. `学生可见内容`, containing required peer fields:
   - `实验原理`, with `化学方程式 / 文字描述` as its input mode selector.
   - `现象解释`.
   - `安全提示`.

`输入反应式` remains the equation-mode input label, not a top-level learning-content category.

Alternative considered: keep `实验原理` as a separate section and only change copy. Rejected because it preserves the semantic split that caused the current status and user expectation mismatch.

### Decision 6: Missing content guidance is inline and targetable

When a selected point is missing fields, the editor should show a compact amber inline summary near `学生可见内容`, such as `还缺 2 项：实验原理、现象解释`. Each missing field name can act as a text-link control that focuses the relevant field. Individual fields should also expose local required/error state.

Alternative considered: show a large blocking warning card. Rejected because the page is an editor; missing content is the work to do, not a reason to disable the page.

### Decision 7: Principle mode switching is an autosave-safe transition

Switching between equation and text principle modes should be treated as a local transition with its own sequence. After confirmation, the selected mode should remain visible immediately and stale detail hydration must not overwrite it while that switch is pending.

The backend already allows saving incomplete draft content; publication remains the place where missing principle content blocks visibility. Therefore an empty newly selected mode should save as draft and report `缺少实验原理`, not bounce back to the previous mode.

Alternative considered: block mode switching until the new mode is filled. Rejected because teachers often choose the input mode before entering content.

## Risks / Trade-offs

- [Risk] Adding structured status fields can create temporary frontend/backend type drift. -> Mitigation: add fields additively and keep existing label arrays during migration.
- [Risk] Directory aggregate SQL can become harder to maintain if it repeats state logic. -> Mitigation: centralize bucket naming and add contract tests for every filterable state.
- [Risk] Focused missing-field chips can crowd the filter area on narrow widths. -> Mitigation: wrap chips into a second row and keep them lower-emphasis than coarse filters.
- [Risk] Hydration guards can leave stale form data if a different node is selected. -> Mitigation: scope pending autosave/mode-switch guards by node id and reset them on node changes.
- [Risk] Rehoming principle layout can accidentally affect equation preview or AI assist. -> Mitigation: move markup and section hierarchy only; keep existing handlers and payload builders intact.

## Migration Plan

1. Extend backend status helpers to produce stable missing-field keys and labels.
2. Extend directory and chapter summaries with complete descendant status counts and missing-field counts.
3. Update API TypeScript types and frontend filter mappers to use the new structured maps.
4. Rework the point content editor layout so `学生可见内容` contains `实验原理`, `现象解释`, and `安全提示`.
5. Add inline missing-field guidance and field focus targets.
6. Guard principle mode switching against stale autosave or detail hydration.
7. Add backend and frontend contract tests for:
   - missing one, two, or three learning fields
   - `缺内容` and `缺内容：...` filters
   - `待发布` and `已发布` filters with descendants under directories
   - mode switching to an empty mode without reverting
8. Run OpenSpec validation, focused catalog tests, and frontend typecheck.

Rollback is additive for backend payloads. The frontend can fall back to the coarse `missing_fields` labels and existing filters if needed, but the filter bug fix should remain tied to complete descendant status counts.

## Open Questions

None. The product direction is clear: preserve coarse workflow states, add precise missing-field facets where teachers need to act, and align all filterable counts with the same status model.
