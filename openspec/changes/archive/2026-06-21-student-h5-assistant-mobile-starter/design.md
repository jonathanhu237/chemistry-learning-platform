## Context

The prior exploration compared the teacher learning assistant and the student H5 assistant.

Teacher-side reference:

- `apps/admin-web/src/features/learning-assistant/LearningAssistantPage.tsx` implements a full learning-assistant workbench.
- Its empty chat state is not just an empty message. It asks the teacher to choose an experiment, choose a point, choose an intent, preview a generated starter question, and launch from that question.
- Its intent set is especially useful for students too: `观察什么`, `现象说明什么`, `背后原理`, `为什么这样设计`, `和其他点位对比`, `易错点`, and `我自己问`.
- Its chat turns show user/assistant message metadata, running/done/error chips, streaming progress dots, skeleton fallback, current point context, composer character count, and source/diagnostic detail.

Student-side current state:

- `apps/student-web/src/app/StudentAppShell.tsx` owns the authenticated bottom tabs and renders `StudentAiChatTab` for `问答`.
- `apps/student-web/src/features/assistant/StudentAiChatTab.tsx` shows an intro card and a dismissible context cue when launched from learning, experiment group, or point context.
- `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx` owns the actual stream, message list, quick prompt buttons, single-line mobile input, status text, and compact source summary.
- `apps/student-web/src/features/assistant/assistantContext.ts` defines the default `learning_home` context and three global quick prompts.
- Learning and experiment pages already build richer contexts:
  - `LearningHomePanel.tsx` creates `learning_profile` contexts with chapter, selected element, property, and experiment point summaries.
  - `ExperimentGroupPanel.tsx` creates `experiment_group` contexts with group, area, and experiment list summaries.
  - `ExperimentDetailPanel.tsx` creates `learning_point` contexts with chapter, experiment, point, video candidates, and point key.
- `apps/student-web/src/shared/markdown/AiMarkdownBlock.tsx` and `apps/student-web/src/components/AiMarkdown.tsx` already provide richer student markdown, GFM, KaTeX, and `mhchem` support; the chat panel currently uses a local `MarkdownLite`.

The screenshot and code review show the main product gap: the student `问答` tab has the right destination, but the first screen feels passive and sparse. The student sees a large blank chat area, a short empty-state sentence, horizontal prompt chips that can overflow, a single-line input, and a coarse status line. The teacher side has a much better "how do I ask a useful question?" scaffold.

Constraints:

- This remains a phone-first H5 app, not a desktop student workbench.
- The `问答` tab must remain available through bottom navigation when assistant feature flags allow it.
- The backend student assistant request schema should remain stable unless implementation discovers a hard blocker.
- Student guardrails, assessment-answer protection, unsafe-experiment refusal, resource-grounding behavior, and feature-switch enforcement remain backend-owned.
- Teacher-only diagnostics, raw JSON traces, RAG internals, and admin inspection panels must not appear in the student UI.
- Existing dirty worktree changes in student frontend files must be treated as user work during implementation.

## Goals / Non-Goals

**Goals:**

- Make the student `问答` first screen actively guide students into useful course questions.
- Adapt the teacher starter pattern to a mobile flow: context summary, intent choices, question preview, and one clear launch action.
- Preserve simple free-form asking for students who already know what they want to ask.
- Make contextual handoff more legible: students should understand whether they are asking globally, within a chapter, within an experiment group, or about a specific point.
- Improve streaming and answer feedback so students see useful status, not just a blank assistant bubble.
- Reuse existing student context payloads and APIs where practical.
- Improve answer rendering by using the student markdown/chemistry renderer already present in the app.
- Keep prompt chips, the merged context header/card area, composer, and bottom navigation usable on 360px to 430px phone viewports.

**Non-Goals:**

- Do not redesign the whole student app shell or bottom navigation.
- Do not port teacher-side diagnostics, inspector panels, JSON traces, RAG timing, policy internals, or raw source debug detail.
- Do not add teacher controls such as `allow_rag_lookup`, `allow_progress_lookup`, runtime health chips, or student-id selectors to the student UI.
- Do not change backend policy classification or guardrail rules.
- Do not create a desktop-specific student assistant layout.
- Do not require students to pick an experiment before asking a global course question.

## Decisions

### 1. Use A Mobile Starter Sheet Inside The Existing `问答` Tab

The first screen should become a mobile starter surface inside `StudentAiChatTab` or a nearby feature module, not a separate route.

Suggested structure:

```text
StudentAiChatTab
├─ StudentAiChatPanel
│  ├─ MergedContextHeader
│  ├─ AssistantStarterSurface
│  ├─ IntentChipGrid
│  ├─ StarterQuestionPreview
│  └─ LaunchStarterButton
│  ├─ ChatStream
│  ├─ QuickFollowupPrompts
│  └─ Composer
```

The starter surface appears before the first message. After the first send, the chat stream becomes primary. A compact "新问题" or "换个提问方向" affordance can optionally reopen starter choices, but it should not dominate ongoing chat.

Alternative considered: port the teacher three-column starter grid. Rejected because it is too dense for mobile and would make the phone UI feel like a squeezed admin page.

### 2. Split Starter Intent Definitions From Context Construction

Create a small student-owned intent model near the assistant feature:

```ts
type StudentAssistantIntent = {
  id: "observe" | "phenomenon" | "principle" | "design" | "compare" | "mistake" | "custom";
  label: string;
  shortLabel?: string;
  description: string;
  buildQuestion?: (context: AssistantContext) => string;
};
```

The intent list can borrow teacher labels but simplify descriptions for students. The `buildQuestion` function should consume the existing `AssistantContext`; it should not require backend data beyond fields already sent to the assistant.

For `learning_home`, the UI can show global intent cards and either:

- send a generic starter question built from the selected intent, or
- prefill the composer with a preview for the student to edit.

For `learning_profile`, `experiment_group`, `experiment_detail`, and `learning_point`, the preview should reference the active `context_title`, `chapter_id`, `experiment_id`, or `point_key` only when available and student-readable.

Alternative considered: keep one static `prompts` array per context. Rejected because it preserves the current passive prompt-chip behavior and loses the teacher-side intent pattern the user wants.

### 3. Make Context A First-Class Mobile Header/Card Area, Not A Duplicate Card

The current intro card says whether context is active, and the chat panel header repeats "当前内容". The design should consolidate these into one visible context area near the top of the chat panel, rather than rendering two separate "当前内容 / 当前上下文" blocks:

```text
当前内容
AI 学习助手 / 卤族元素 / 氯水与溴化钾反应 / 点位 2
全局课程问答 / 实验组 / 点位
[切回全局]
```

Rules:

- Global context shows `AI 学习助手` and a short course-scope note.
- Context handoff shows the title and a concise subtitle derived from `context_type`.
- A clear action resets to `defaultAssistantContext()`.
- Resetting context must not require leaving the `问答` tab.
- The context area should not trap students; free-form input remains available.
- The chat panel should use the available phone height between the sticky app header and bottom navigation instead of ending midway down the screen with a large unused background area.

Alternative considered: keep context only in the outer intro card. Rejected because the useful context is too far from the first-send decision and composer, especially on the screenshot's tall blank chat card.

### 4. Prefer Intent Chips Over Horizontally Scrolling Long Prompts

The current quick prompt row scrolls horizontally and can cut off long Chinese text. On mobile, initial starter choices should use a 2-column wrap/grid where labels are short and descriptions are one or two lines.

Example:

```text
[观察什么]       [现象说明什么]
聚焦看哪里       把现象和结论连起来

[背后原理]       [易错点]
解释化学原因     找常见误解
```

After a conversation starts, follow-up quick prompts can remain horizontally scrollable if they are short, but the first-screen starter should avoid horizontal overflow.

Alternative considered: keep current prompt chips but shorten copy. Rejected because it improves copy but not the interaction model.

### 5. Add A Starter Preview And One Clear Launch Action

When an intent is selected, show a generated question preview:

```text
准备提问
请解释「氯气与溴化钾反应」这个点位背后的化学原理，并说明它和实验结论的关系。
[从这个问题开始]
```

Behavior:

- Tapping an intent updates preview.
- Tapping launch sends the preview as the user question.
- If intent is `custom`, the preview tells the student to type below while preserving current context.
- If the composer has typed content, launch should send the typed content or clearly separate "发送输入内容" from "从预览开始"; implementation should avoid ambiguous dual sources.

Alternative considered: auto-send immediately when a chip is tapped. Rejected because preview is part of the teacher-side interaction strength and reduces accidental sends on mobile.

### 6. Keep Backend Contract Stable

Continue using `streamStudentAssistantAsk` and `StudentAssistantAskRequest`:

```ts
{
  question,
  context_type,
  context_title,
  context_summary,
  chapter_id,
  experiment_id,
  point_key,
  knowledge_point_ids,
  conversation_history
}
```

The starter UI only changes how `question` is chosen. Context handoff fields already exist. If implementation wants global experiment-module choices inside `问答`, it can load existing student APIs:

- `getStudentLearningHome()` for module summaries.
- `getStudentExperimentGroup(parentCode)` for group details when selected.
- `getStudentExperimentDetail(experimentId)` only if point-level choices are needed.

This staged approach keeps the first implementation frontend-only from an API contract perspective.

Alternative considered: add a backend starter-suggestions endpoint. Rejected for now because deterministic starter questions are enough and avoid adding new backend surface.

### 7. Reuse Student Markdown Rendering For Chat Answers

Replace or wrap `MarkdownLite` with the existing `AiMarkdownBlock`/`AiMarkdown` path so chat answers can render:

- GFM lists.
- Inline and block math.
- Chemical notation through KaTeX and `mhchem`.
- Code spans and simple structured output.

Keep `AssistantSourceSummary` compact and student-readable. Do not expose raw source debug metadata.

Alternative considered: expand `MarkdownLite`. Rejected because a richer renderer already exists and is used by assessment summary/mistake explanations.

### 8. Improve Chat Turn Status Without Adding Admin Diagnostics

Student chat should borrow teacher-side status language and visual feedback, but in compressed form:

- Running status pill: "正在判断问题范围", "正在检索课程资料", "正在生成回答", or a safe fallback "正在生成".
- Assistant skeleton while no answer text has streamed.
- Done/error visual state on the assistant message.
- Compact turn metadata, optional: "学习助手" and "刚刚" or a short status chip.
- Source summary after final response, already present, kept at up to three student-readable chips.

Do not show:

- policy decision codes,
- guardrail arrays,
- RAG timings,
- rerank scores,
- raw JSON,
- runtime health.

Alternative considered: keep only the bottom `ai-chat-status` line. Rejected because status is disconnected from the active answer and is easy to miss below the composer.

### 9. Make Composer Keyboard-Safe And More Useful

The current composer is a single-line `MobileField`. The implementation should consider a mobile textarea-style composer with:

- 1 to 4 rows auto-grow.
- fixed send icon button.
- optional character count only when near the limit.
- safe-area and keyboard-aware layout.
- no overlap with the bottom navigation.

If switching to textarea is too much for the first pass, at minimum preserve the single-line composer but ensure the starter preview carries the longer question so students do not need to type a long structured prompt manually.

Alternative considered: port teacher `Input.TextArea` styling directly. Rejected because the student app does not use Ant Design and needs mobile primitives.

### 10. Test Against The Actual Phone Sizes And Current Screenshot Failure Mode

QA should explicitly cover:

- 360x780, 390x844, and 430x932 CSS-pixel viewports.
- The initial global `问答` tab.
- A context handoff from a learning chapter.
- A context handoff from an experiment point.
- No horizontal overflow from starter chips or prompt rows.
- Composer reachable with bottom navigation present.
- Long Chinese labels do not clip or overlap.
- Starter launch sends a question and transitions into normal chat.
- Assistant-disabled feature config hides or redirects away from `问答`.

## Risks / Trade-offs

- [Risk] Starter UI becomes too tall and pushes composer below the fold on 360px phones. → Use compact cards, 2-column intent grid, collapsible preview copy, and viewport QA.
- [Risk] Students confuse preview text with already-sent chat. → Label preview clearly as `准备提问` and keep launch action visually distinct.
- [Risk] Context reset clears useful conversation. → Either preserve messages when context resets or explicitly treat reset as a new starter context; tests should document the chosen behavior.
- [Risk] Existing worktree changes touch assistant files. → Implementation must inspect current file contents before editing and preserve unrelated user changes.
- [Risk] Using richer markdown changes answer layout. → Reuse existing student markdown styles and add chat-specific regression coverage for math/list rendering.
- [Risk] Loading experiment data inside `问答` could slow the first screen. → Make the first pass work without network starter data; only load optional experiment-module choices progressively.

## Migration Plan

1. Add the starter model and rendering in the student assistant feature behind existing assistant feature availability.
2. Keep `streamStudentAssistantAsk` payload shape unchanged.
3. Replace the current empty bubble with the starter surface when there are no messages.
4. Preserve current quick prompt submission behavior as a fallback or follow-up behavior.
5. Swap assistant answer rendering to the shared student markdown renderer.
6. Update mobile CSS and QA to cover starter layout and composer reachability.
7. If rollout needs rollback, revert to the current empty bubble and quick prompt row without backend migration.

## Open Questions

- Should a context reset preserve existing chat turns or clear them? Current implementation clears messages when context changes. The new UX should make this behavior explicit.
- Should global `问答` load experiment modules on first render, or only after the student taps an "按实验提问" starter? Progressive loading is likely safer.
- Should starter launch always send immediately, or should it prefill the composer first? The proposal favors preview + explicit launch; implementation can choose whether typed custom text overrides preview.
