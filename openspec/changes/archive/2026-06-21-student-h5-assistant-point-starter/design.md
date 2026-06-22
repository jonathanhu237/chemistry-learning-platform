## Context

This change builds directly on the completed `student-h5-assistant-mobile-starter` work.

Current student-side state after that work:

- `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx` owns the mobile chat panel, merged context header, starter surface, preview launch, stream messages, per-turn status, source summary, and composer.
- `apps/student-web/src/features/assistant/assistantStarter.ts` owns global and structured starter intents.
- `apps/student-web/src/features/assistant/assistantContext.ts` defines the default global `learning_home` context.
- The chat panel now uses the available height between the sticky app header and bottom navigation.
- The current UI still shows a bottom text status under the composer, such as `正在生成回答` or `学习助手已回答`; the user now considers this redundant because per-turn status chips already communicate running/done/error state.

Teacher-side reference:

- `apps/admin-web/src/features/learning-assistant/LearningAssistantPage.tsx` lets teachers choose an experiment, choose a point, choose an intent, preview the generated question, and launch.
- Teacher intent labels are valuable for students too: `观察什么`, `现象说明什么`, `背后原理`, `为什么这样设计`, `和其他点位对比`, `易错点`, and `我自己问`.
- Teacher-side diagnostics, RAG traces, point evidence grades, runtime chips, and admin controls must not be exposed to students.

Student-side available data:

- `getStudentLearningHome()` returns student-visible learning areas and experiment groups.
- `getStudentExperimentGroup(parentCode)` returns experiments inside a visible group.
- `getStudentExperimentDetail(experimentId)` returns concrete `video_candidates`, `videos`, `point_key`, and `point_title` data for a visible experiment.
- `LearningHomePanel`, `LearningExperimentsView`, `LearningPointGroupView`, `ExperimentGroupPanel`, and `ExperimentDetailPanel` already prove these APIs can construct student-visible point context.
- `ExperimentDetailPanel` already constructs a `learning_point` `AssistantContext` from experiment detail and point metadata.

The product opportunity is to let the `问答` tab itself support a teacher-like point starter without forcing students to navigate through `学习` or `实验` first.

## Goals / Non-Goals

**Goals:**

- Add an `实验点位` starter path in the student `问答` tab before the first chat turn.
- Let students choose a student-visible experiment group, concrete experiment/video point, and question template.
- Build a `learning_point` assistant context from existing student-visible API data.
- Keep broad `全局课程问答` as the default path; point selection must be optional.
- Preserve the existing assistant stream request shape.
- Remove the redundant bottom status copy under the composer while retaining per-turn message status.
- Keep all controls usable on 360px to 430px phone viewports.

**Non-Goals:**

- Do not port the teacher three-column desktop workbench directly.
- Do not add a backend starter-suggestions endpoint in the first pass.
- Do not expose teacher-only experiment objects, admin diagnostics, RAG traces, evidence review grades, policy codes, or runtime health details.
- Do not add video playback inside the assistant starter; video playback remains in the learning/experiment flows.
- Do not require point selection before students ask a global course question.
- Do not change backend guardrail, RAG, or policy-classification behavior.

## Decisions

### 1. Use A Two-Mode Starter Instead Of A Single Dense Starter

The assistant starter should offer two top-level modes before the first turn:

```text
┌─────────────────────────────┐
│ 当前内容                     │
│ AI 学习助手                 │
│ 全局课程问答                │
├─────────────────────────────┤
│ [课程问答] [实验点位]       │
│                             │
│ 课程问答模式:               │
│   复习顺序 / 实验现象 / ... │
│                             │
│ 实验点位模式:               │
│   选实验组 → 选点位 → 模板  │
└─────────────────────────────┘
```

Rationale:

- Students still need a quick broad-question path.
- The point path is more powerful but heavier; it should not dominate the first impression.
- This mirrors the teacher concept while adapting density for mobile.

Alternative considered: replace the global starter with a point selector. Rejected because it would make simple questions slower and contradict the current successful mobile starter.

### 2. Load Experiment Choices Progressively

The point starter should not block the global starter. Recommended data flow:

```text
student taps "实验点位"
        │
        ▼
getStudentLearningHome()
        │
        ▼
select parentCode / experiment group
        │
        ▼
getStudentExperimentGroup(parentCode)
        │
        ▼
select experiment
        │
        ▼
getStudentExperimentDetail(experimentId)
        │
        ▼
derive point options from videos and video_candidates
```

Rationale:

- First render remains fast.
- Failures in optional point data do not break normal assistant usage.
- The app stays within student-visible data boundaries.

Alternative considered: fetch all groups, all experiments, and all details on `问答` mount. Rejected because it could add unnecessary network work and make the mobile starter feel sluggish.

### 3. Derive Point Options From Student Detail Data

Point options should be created from `StudentExperimentDetailResponse`:

- Prefer `videos` with `point_key` or `point_title` because they represent published media resources.
- Fall back to `video_candidates` when published videos are missing.
- Use stable keys:
  - `video.point_key` when present.
  - `video.point_title` when present.
  - a deterministic candidate key such as `candidate:<index>:<title>` when only candidate text exists.

Each point option should include:

```ts
type StudentAssistantPointOption = {
  pointKey: string;
  pointTitle: string;
  pointIndex: number;
  mediaId?: string | null;
  hasPublishedVideo: boolean;
};
```

Rationale:

- This matches the teacher-side point-option idea without needing admin-only `Experiment` data.
- The assistant can still ask about a candidate point even when video is not published, as long as the UI labels it clearly.

Alternative considered: expose only published videos. Rejected because existing student detail pages already show `video_candidates`, and point context can still be meaningful without a playable video.

### 4. Build `AssistantContext` Locally From The Selected Point

When group, experiment, point, and intent are selected, construct:

```ts
{
  context_type: "learning_point",
  context_title: selectedPoint.pointTitle,
  context_summary: compactText([
    `实验组：${group.parent_title}`,
    `实验：${experiment.title}`,
    experiment.summary,
    `点位：${selectedPoint.pointTitle}`,
    selectedPoint.hasPublishedVideo ? "已有公开视频" : "暂无公开视频或仅有候选点位",
    detail.video_candidates.length ? `观察点：${detail.video_candidates.join("、")}` : null,
  ]),
  chapter_id: experiment.chapter_ids[0] || detail.chapter_ids[0] || null,
  experiment_id: experiment.id || detail.id,
  point_key: selectedPoint.pointKey,
  prompts: [...]
}
```

The resulting context should be sent through `streamStudentAssistantAsk()` exactly like existing context handoff.

Rationale:

- No backend schema change is required.
- Existing backend context-aware classification already understands `chapter_id`, `experiment_id`, and `point_key`.

Alternative considered: add new request fields such as `point_title` or `parent_code`. Rejected for this pass because `context_summary` can carry student-readable detail and backend policy already accepts the existing fields.

### 5. Keep Template Intents Shared But Point-Aware

The point starter should reuse the same conceptual intents as teacher and existing structured student starter:

- `观察什么`
- `现象说明什么`
- `背后原理`
- `为什么这样设计`
- `和其他点位对比`
- `易错点`
- `我自己问`

The question builder should use the selected point context, not just the current global assistant context.

Example generated question:

```text
我正在看「E17-02 氯水与溴化钾反应」的点位 2「CCl4 层颜色变化」。
这个点位主要要观察什么？请指出观察对象、现象和判断依据。
```

Rationale:

- This is the teacher pattern the user likes, translated into student-readable copy.
- Preview remains explicit and prevents accidental sends.

Alternative considered: keep only the current global intent grid and alter questions after a point is selected. Rejected because students need to see that point selection changes the question source.

### 6. Use Mobile Disclosure, Not Desktop Columns

On phone, the point starter should be staged:

```text
实验点位
1. 实验组       [卤素] [氨及铵盐] [...]
2. 实验/视频点  [氯水与溴化钾反应] [...]
3. 想问方向     [观察什么] [背后原理] [...]
准备提问        <preview>
```

Acceptable implementations:

- stacked sections with selected chips/cards,
- an accordion-like flow,
- a compact picker sheet for group/experiment/point when lists are long.

The first implementation should prefer stacked sections inside the existing chat panel unless lists become too tall.

Rationale:

- Mobile needs discoverability without horizontal overflow.
- The student should always understand which selection is currently active.

Alternative considered: bottom-sheet selector for every level. Rejected for first pass because it adds overlay coordination complexity; reserve sheets for long-list follow-up.

### 7. Remove Only The Bottom Status Bubble

The redundant status copy under the composer should be removed:

```tsx
<div className="ai-chat-status">{assistantStatusLabel(status, loading)}</div>
```

The following should remain:

- assistant message meta row,
- running/done/error chip inside the assistant turn,
- stream progress row,
- skeleton placeholder,
- compact source summary.

Rationale:

- The screenshots show the bottom status is visually noisy after the improved per-turn interaction.
- Removing it gives the composer and chat stream more breathing room.

Alternative considered: keep the bottom status but hide it only while streaming. Rejected because the message-level state is sufficient in all phases.

### 8. Testing Must Cover Both Global And Point Starters

Tests should prove:

- global starter still works,
- point starter loads optional data on demand,
- selecting a point generates a `learning_point` request,
- generated point question includes selected point context,
- bottom status copy is gone,
- per-turn status remains,
- 360x780, 390x844, and 430x932 viewport QA still has no horizontal overflow or blocked controls.

## Risks / Trade-offs

- [Risk] Optional data fetching slows the first assistant screen. → Only fetch point data when the student enters point mode; keep global starter interactive.
- [Risk] Long experiment names and point titles crowd the phone layout. → Clamp secondary text, wrap primary labels, and validate at 360px.
- [Risk] Students confuse candidate-only points with playable videos. → Label published video status in metadata copy, but do not block learning questions.
- [Risk] Reusing `context_summary` for point title means backend cannot query a dedicated `point_title` field. → Keep `point_key` as the structured field and include readable point title in summary/question text; add backend fields only in a later change if evidence lookup requires it.
- [Risk] Deep selector state becomes hard to reset after a send. → After first send, transition to normal chat; use selected context for the turn and follow-up prompts.
- [Risk] Existing dirty worktree changes touch assistant and learning files. → Implementation must read files before editing and avoid reverting unrelated changes.

## Migration Plan

1. Implement point starter as an additive frontend path behind existing assistant feature availability.
2. Preserve global starter behavior as the default.
3. Remove bottom status copy after per-turn status remains verified.
4. Reuse existing student APIs and assistant stream contract.
5. Update e2e and mobile QA.
6. Rollback path: hide/remove the point-mode tab or segmented control and restore global-only starter; no backend migration is required.

## Open Questions

- Should the point starter default to the recommended experiment group from `getStudentLearningHome()` or to the first group in display order? Recommended group is likely better if available.
- Should candidate-only points appear by default or be placed after published-video points? Published-video points should likely appear first.
- Should point starter state persist if the student leaves and reopens `问答` before sending? A simple first pass can reset unsent point selections on tab remount/context reset.
- Should a later change add a direct "去看视频" affordance from the point starter? This change keeps video playback out of assistant to avoid competing primary tasks.
