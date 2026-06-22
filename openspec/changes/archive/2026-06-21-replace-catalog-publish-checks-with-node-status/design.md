## Context

The chapter catalog workbench currently mixes several different kinds of state:

- catalog tree state: directory/point kind, hierarchy, placement publication, archive state, ordering, and child counts;
- point authoring state: whether the point has the three required learning fields and its experiment video;
- shared canonical point state: whether the shared experiment content is saved/published and reused by other placements;
- downstream consumption state: ES search document sync and AI/RAG evidence freshness/jobs.

This makes the left tree feel heavier than the product model. A single warning icon can currently mean missing content, unpublished content, missing video, validation warning, ES pending, ES failed, RAG stale, RAG failed, or some combination. The `发布检查` panel also reinforces the wrong mental model: it sounds like a publishing-only gate, but the user needs a broader node-status surface that explains authoring readiness, student visibility, and asynchronous downstream consumption without making all of them primary tree states.

The product primitive for a point is intentionally simple:

```text
one point = three learning fields + one experiment video
```

The implementation may still have media binding tables or historical multiple-binding support, but the teacher-facing status model must treat video as binary: `有视频` or `无视频`.

The current canonical point / placement architecture remains valid:

```text
placement node
  owns: path, parent directory, display order, placement visibility, placement card overrides

canonical experiment point
  owns: point content, experiment video, related experiments, AI/RAG evidence, question/assessment identity
```

The new work is therefore an information-architecture and status-contract correction, not a catalog tree data-model replacement.

## Goals / Non-Goals

**Goals:**

- Replace the teacher-facing `发布检查` surface with `节点状态`.
- Define a normalized status model that separates core point readiness, student visibility, and asynchronous ES/RAG consumption.
- Keep the left tree lightweight and scannable: one primary status marker per row, plus simple directory aggregation.
- Make point video state binary in product language: `有视频 / 无视频`.
- Provide teacher-readable Chinese copy for status reasons and repair actions.
- Keep ES and RAG outbox states observable without letting them redefine core node readiness.
- Preserve placement/canonical context so teachers understand when edits affect every reused experiment location.

**Non-Goals:**

- This change does not redesign the catalog data model, canonical point grouping, or placement identity.
- This change does not add true multi-parent catalog nodes.
- This change does not change student H5 routing semantics.
- This change does not make ES/RAG jobs synchronous publishing blockers by default.
- This change does not introduce a full monitoring dashboard for all async jobs.
- This change does not expose multi-video authoring as a product capability.

## Decisions

### Decision 1: Model node status as grouped conditions plus one primary state

Each selected node should have a computed status summary with grouped conditions:

```text
node_status
  primary_state: archived | blocked | needs_content | needs_video | draft | ready | published | sync_attention
  primary_reason: teacher-readable short phrase
  core_readiness:
    content_fields: complete | missing
    video: present | absent
  visibility:
    placement: draft | published | archived
    shared_content: missing | draft | published | archived
    student_available: true | false
  async_consumption:
    search_index: idle | pending | running | synced | stale | failed | disabled | unavailable
    ai_evidence: idle | pending | running | available | stale | failed | disabled | unavailable
  conditions:
    - key, group, severity, status, reason, message, action
```

The UI may not need to render this exact shape immediately, but the implementation should behave as if these concepts are distinct. This prevents frontends from reinterpreting raw validation arrays or job enum fields differently in different panels.

Alternative considered: keep `validation.errors/warnings` as the only status source and improve copy. Rejected because validation arrays do not express status groups, priority, or async-vs-core boundaries.

### Decision 2: Core point readiness outranks downstream async state

For point nodes, primary state is derived in this order:

1. `archived`: placement or canonical point is archived.
2. `blocked`: the point has a structural/catalog identity problem, such as an invalid node kind or missing canonical experiment identity. Normal empty learning content is not blocked. Teacher-facing UI labels this state as `异常` and uses the red error treatment.
3. `needs_content`: the shared learning content is absent or one or more of the three learning fields is missing. This outranks video.
4. `needs_video`: the three learning fields are complete and the point has no experiment video.
5. `draft`: the directory itself is not published, or a non-point node is still draft.
6. `ready`: a point is core-complete and can be published, but its placement is not yet student-visible.
7. `published`: the placement is student-visible and no higher-priority authoring or sync state is active.
8. `sync_attention`: only for published, core-complete points whose ES/RAG derived consumption has a failed/unavailable state that needs teacher/operator attention.

ES/RAG `pending`, `running`, or `stale` should not replace a core status in the default tree. They belong in the selected-node `节点状态` panel and advanced diagnostics. Only failed/unavailable async states on already-published points may escalate to a secondary attention signal.

Alternative considered: show separate status dots for content, video, publication, ES, and RAG in every tree row. Rejected because the tree would become a monitoring dashboard rather than a navigation surface.

### Decision 3: Directory rows aggregate child actionability, not child implementation details

Directory rows should not show ES/RAG details. A directory status should answer:

- Is the directory itself archived/draft/published?
- How many descendant points need teacher action?
- Is any descendant structurally blocked, shown to teachers as an `异常` count rather than a normal authoring warning?

Directory aggregation should group descendant problems into compact counts:

```text
待处理 3
  缺内容 1
  缺视频 2
```

The default row should show at most one aggregate marker and one count. Detailed breakdown appears in tooltip, selected-node status panel, or optional filters.

Alternative considered: roll every descendant condition into a colored directory badge. Rejected because deep chapters would become visually noisy and the teacher could not tell what the color means without opening the node anyway.

### Decision 4: Rename `发布检查` to `节点状态`

The right-side tab/surface should be `节点状态`. It is not only a publish gate. It should contain three sections:

1. `核心完整性`
   - Three learning fields: complete/missing with missing-field names.
   - Experiment video: `有视频` or `无视频`.
2. `学生可见性`
   - Placement/node publication state.
   - Shared point-content publication state.
   - Whether the student can currently open this point detail.
3. `同步诊断`
   - ES search consumption state.
   - AI/RAG evidence consumption state.
   - Manual retry/refresh actions where already supported.

The first two sections are product-level status. The third section is downstream/operational status and should use secondary visual weight.

Alternative considered: keep `发布检查` but add more sections. Rejected because the name itself keeps the old misconception that this is only a publishing gate.

### Decision 5: Tree decoration is a pointer, not the explanation

The left tree row should show:

```text
[kind icon] title                         [count] [primary status marker] [actions]
```

Rules:

- At most one primary status marker is visible by default.
- Normal/healthy published states may use no marker or a subtle neutral/success marker.
- Warning/error markers must have clear accessible labels and tooltips.
- Row text, icon color, and background must not all change for status; selection and hierarchy need visual stability.
- Hover/focus can reveal a concise tooltip such as `缺视频：无视频`; student visibility remains a separate detail in `节点状态`.
- Detailed reason lists belong in `节点状态`, not in the tree row.

This follows the same pattern used by professional file trees and operations trees: tree nodes remain navigable; status details are available on selection or hover.

### Decision 6: Filters and views carry complexity when teachers need it

The workbench should support a lightweight default tree and optional focus modes:

- `全部`
- `待处理`
- `缺内容`
- `缺视频`
- `已发布`
- `同步异常`

These filters are more useful than rendering every status dimension in every row. `同步异常` should include ES/RAG failed/unavailable, while `待处理` should focus on core readiness and visibility work.

Alternative considered: always display every state dimension in trailing row badges. Rejected because it helps debugging but hurts routine authoring.

### Decision 7: Backend owns status derivation

The backend should provide or prepare a stable node-status read model so the teacher frontend does not locally infer status from scattered fields:

- node kind/status;
- validation errors/warnings;
- canonical point content status;
- required content fields;
- binary experiment video presence;
- placement/canonical availability;
- ES index state;
- RAG evidence state.

The existing validation endpoints can remain, but they should become implementation inputs to node status rather than the teacher-facing concept. Existing API consumers can bridge from `validation` to `node_status` during migration.

Alternative considered: derive status entirely in React mappers. Rejected because tree, header, status panel, tests, and future student/admin surfaces would drift.

### Decision 8: Product copy replaces internal diagnostic strings

Teacher-facing status messages must not expose internal English backend strings such as:

- `Canonical point content must be saved before publishing`
- `Canonical point content has not been saved`

The UI should translate these into action-oriented copy:

- `共享实验内容尚未保存`
- `请先在「内容」中补齐原理、现象解释和安全提示`
- `请为此点位添加实验视频`
- `当前目录位置已发布，但学生仍无法打开点位详情`

Advanced/debug panels may retain raw ids and raw backend messages only when they help developer/operator diagnosis.

### Decision 9: Related experiments are an ordered learning list with defaults and overrides

Teacher-facing language must separate two concepts that were previously easy to confuse:

- `多目录共享实验`: the canonical experiment identity whose title, learning content, video, AI evidence, and related-experiment list can be reused by one or more catalog placements.
- `相关实验`: the ordered list of other experiment points shown to students and consumed by search/RAG as learning context.

The default related-experiment list is generated from other point nodes under the same direct parent directory. This keeps defaults predictable and scoped to the current directory group. The default MUST NOT silently pull points from sibling directories into student/search/RAG context.

Sibling directories should be treated as optional candidate groups, not default consumption. The editor should let teachers search or browse candidate experiments and add them manually. Once a teacher reorders, removes, labels, or adds items, the list becomes a teacher override. A teacher must be able to reset to the same-parent default.

The editor should present related experiments as a reorderable list:

```text
Current related experiments
  [drag handle] 1. Same-parent default item      [optional display name] [remove]
  [drag handle] 2. Manually added item           [optional display name] [remove]

Candidate experiments
  Search / same-level groups / sibling-directory groups

Actions
  Save related experiments
  Reset to same-parent default
```

The editor MUST NOT expose raw `target_node_id`, `relation_type`, or `sort_order` as the primary authoring surface. Those are payload/debug concepts.

## Risks / Trade-offs

- [Risk] Moving ES/RAG out of the primary tree marker may hide operational failures. -> Mitigation: escalate failed/unavailable async states for already-published points to `sync_attention`, add a `同步异常` filter, and keep diagnostics visible in `节点状态`.
- [Risk] Backend node-status derivation adds another contract beside validation. -> Mitigation: treat validation as a lower-level input and migrate UI surfaces incrementally.
- [Risk] Binary video language may conflict with current multiple media-binding storage. -> Mitigation: define teacher product status as `has experiment video`, while advanced diagnostics may still reveal binding count if needed.
- [Risk] Directory aggregation can obscure which descendant has the problem. -> Mitigation: selected directory `节点状态` shows descendant issue groups and provides filtered tree/search links.
- [Risk] Existing tests and visual QA expect `发布检查`. -> Mitigation: update tests to assert `节点状态`, core/visibility/sync grouping, and the absence of multi-status row clutter.

- [Risk] Automatically including sibling-directory points in defaults would broaden student/search/RAG context without an explicit teacher decision. -> Mitigation: keep defaults to same direct parent points and expose sibling-directory points as manually addable candidates.

## Migration Plan

1. Add node-status mapper/server read model using current validation, content, media, and job state fields.
2. Update teacher API types to expose node status while keeping validation for compatibility.
3. Replace visible `发布检查` labels with `节点状态`.
4. Rebuild the selected-node status panel into `核心完整性`, `学生可见性`, and `同步诊断`.
5. Simplify left-tree row status rendering to one primary marker plus directory issue aggregation.
6. Update point video UI/status copy from multi-binding/count language to binary experiment-video presence where teacher-facing.
7. Add optional filters for `待处理`, `缺内容`, `缺视频`, `已发布`, and `同步异常`.
8. Update backend/frontend tests and visual QA.
9. Keep raw validation/job diagnostics in advanced surfaces for operators.

Rollback is normal application rollback. If the backend adds a new `node_status` field, old clients should keep working from existing `validation`, `status`, and job-state fields until the UI migration is complete.

## Open Questions

- Should a published point with ES synced but RAG stale show any tree attention marker, or only appear in `同步诊断`?
- Should directory row aggregation count only direct children or all descendants? The design recommends descendant aggregation, but visual copy should make that clear.
- Should `ready` and `published` both be visible states, or should `ready` only appear in the status panel while tree stays quiet?
- If multiple video bindings exist in legacy data, should the status choose the first published binding, the newest published binding, or report an advanced data-cleanup warning?
