## Context

The student app has five root tabs. The AI root (`/ai`) currently renders an AI center card with a new-chat action and suggested prompts. Actual chat happens in `/ai/chat`, which is treated as a second-level detail route and receives optional context through `sessionStorage`.

The teacher learning assistant already has a strong chat implementation: turn list, streaming status, skeleton output, source summary, composer, clear action, and multi-turn history construction. Its desktop workbench, point selector, runtime diagnostics, model controls, and inspector are not student-appropriate. The student version should borrow the chat shell behavior, not the teacher admin workflow.

The requested first round is deliberately narrow:

- `/ai` should feel like opening a mobile chat app for the course assistant.
- Other pages that call AI should still open a separate second-level contextual chat page.
- Unsupported generic AI app features are omitted: attachments, model selection, and voice input.
- Starter prompts and point-selection flows are a later/secondary concern, not the first-screen focus.

## Goals / Non-Goals

**Goals:**

- Make `/ai` a direct mobile chat shell with a visible composer on the first screen.
- Add a right-top history entry on `/ai`.
- Keep contextual AI from learning/point/assessment pages on `/ai/chat` with detail-page chrome and source-aware return.
- Reuse one underlying student chat stream component for both root and contextual chat.
- Preserve current student backend guardrails, streaming endpoint, markdown rendering, source summaries, and feature-switch behavior.
- Keep the UI course-oriented: chemistry learning language, course assistant identity, restrained visual atmosphere, and no generic model/tool affordances.
- Provide first-round chat history through client-side storage so the root history entry is functional without backend migration.

**Non-Goals:**

- No server-side chat session tables or cross-device chat sync in this change.
- No attachment upload, file picker, camera, voice input, or model selector.
- No teacher diagnostics, RAG trace inspection, runtime health chips, policy codes, or raw source details in the student UI.
- No redesign of home, learning, assessment, profile, or the bottom navigation.
- No mandatory point-selection starter in the AI root first screen.

## Decisions

### 1. Split Page Chrome From Chat Behavior

Create or refactor toward a shared student chat shell that can run in two variants:

```text
/ai root
  StudentAiChatShell variant="root"
  - root top bar: title + history button
  - bottom navigation remains visible
  - default context: learning_home

/ai/chat detail
  DetailPageFrame title="AI 对话"
    StudentAiChatShell variant="detail"
    - no history button
    - optional context from source page
    - bottom navigation hidden by route role
```

Rationale: the chat stream, composer, streaming states, and markdown answer rendering should not fork, but the page shell and route semantics must be distinct. This directly supports "AI root is the chat app" and "other AI calls are second-level context chat".

Alternative considered: move all AI traffic to `/ai` and pass context through search params. Rejected because source-aware back behavior from point/report pages would become muddy and would conflict with existing route-level semantics.

### 2. Make The Root First Screen Composer-First

When `/ai` has no messages, it should still look like a chat page:

```text
┌────────────────────────────┐
│ AI 学习助手        历史记录 │
│                            │
│       subtle course empty   │
│       state / recent chips  │
│                            │
│ ┌────────────────────────┐ │
│ │ 问一个实验现象、原理... │ │
│ │                    发送 │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

The empty state may use a subtle course grid, small chemistry-learning copy, and recent conversation chips. It must not render the old intro card + "新对话" gate, and it must not require selecting a starter prompt before typing.

Rationale: the user asked for a Grok-like direct chat feel, but adapted to the course product. The key affordance is immediately asking a question, not choosing a tool.

Alternative considered: keep `/ai` as a center and restyle it. Rejected because it would preserve the extra step the user wants removed.

### 3. Keep Contextual Chat Detail Focused

`/ai/chat` keeps `DetailPageFrame` and should show a compact context cue when launched from a point, chapter, video search, or assessment report. It must not show the root history button. It may share the same composer and message rendering.

Context reset remains available only when a non-global context is active. Resetting starts a global context inside the detail page without changing the route.

Rationale: contextual chat is a task continuation from another page, not the main AI app surface.

Alternative considered: put history and root-level app controls on `/ai/chat` too. Rejected because it blurs the required distinction and makes source-page AI feel heavier than a contextual helper.

### 4. Use First-Round Client-Side Chat History

Implement a small student-side chat history store in browser storage:

```ts
type StudentAiHistoryEntry = {
  id: string;
  title: string;
  contextTitle: string;
  contextType: AssistantContext["context_type"];
  source: "root" | "detail";
  messages: ChatMessage[];
  updatedAt: string;
};
```

Behavior:

- `/ai` can open a history panel/list from the top-right button.
- Sending a message creates or updates the active history entry.
- Final assistant metadata can stay on the message for rendering source summary after restore.
- `/ai/chat` can save conversations into the same local history store, but does not expose the history entry button.
- Selecting a history item from `/ai` restores it into the root chat shell.
- Clearing history is optional for first pass but useful if cheap.

Rationale: this makes the history button real in the first round without backend migration. It also keeps future server persistence simple: the UI contract can later swap storage backends.

Alternative considered: add backend `student_ai_chat_sessions` and message tables now. Rejected for first round because it expands scope into migrations, authenticated list/read APIs, stream persistence, and cross-device privacy decisions.

### 5. Preserve Backend Stream Contract

Continue using `POST /api/student/assistant/ask/stream` with the current `StudentAssistantAskRequest` shape. The frontend sends `conversation_history` from restored/local messages exactly as it does today from component state.

One compatibility improvement is allowed if implementation touches the path: forward existing student context fields (`point_node_id`, `source_node_id`, `catalog_path`) from the student assistant request into `AgentAskRequest` because the lower-level agent schema already supports them. This is not required for the visual shell, but it makes context handoff less leaky.

Rationale: the first round should not couple visual shell work to backend session persistence.

Alternative considered: add `session_id` to the streaming request. Rejected until server-side history becomes a dedicated change.

### 6. Visual Language

Use the student app's existing mobile design language with a slightly more immersive chat canvas:

- full-height shell within available root/detail viewport;
- restrained course atmosphere such as faint grid/experiment notebook texture;
- message bubbles and assistant status borrowed from existing student/teacher chat patterns;
- compact top bar and bottom composer;
- no decorative tool cards, no generic "create image/edit image/news" controls, and no unsupported icons.

Rationale: the screenshot reference informs the layout hierarchy, not the exact dark theme or feature set.

Alternative considered: copy Grok's black starfield. Rejected because the system is a chemistry course app and should remain aligned with the existing student product.

## Risks / Trade-offs

- [Risk] Client-side history can be lost on browser storage clear or another device. -> Mitigation: name this as first-round local history and keep the storage abstraction small for later backend replacement.
- [Risk] Root `/ai` height plus bottom navigation can crowd the composer on 360px devices. -> Mitigation: test 360x780, 390x844, and 430x932 and tune shell height with safe-area spacing.
- [Risk] Removing mandatory starter prompts may conflict with existing archived specs. -> Mitigation: this change modifies those requirements so direct composer-first chat is the new root behavior.
- [Risk] Shared chat shell variants can become prop-heavy. -> Mitigation: isolate page chrome props (`variant`, `showHistory`, `context`) from stream state and storage helpers.
- [Risk] Contextual detail chats saved to root history may confuse students. -> Mitigation: history rows include context title/type and source metadata so they read as prior course conversations.

## Migration Plan

1. Add the OpenSpec deltas and validate the change.
2. Refactor the student chat panel to support root and detail variants.
3. Replace `/ai` center content with the root chat shell and history button.
4. Keep `/ai/chat` as the contextual detail route using the same shell without history button.
5. Add local history storage and restore behavior.
6. Update focused frontend tests for root chat, detail chat, history, and disabled states.
7. Run visual/mobile verification for the AI root and a contextual chat route.

Rollback is straightforward: restore `AiRootPage` to the prior center card and keep the existing `/ai/chat` detail panel. Because first-round history is client-side only, rollback does not require database migration.

## Open Questions

- Should restored history stay on `/ai` only, or should a future version reopen contextual history back into `/ai/chat` with its original source route metadata?
- Should local history have a fixed cap such as the latest 20 conversations in the first pass?
- Should root empty state show recent history chips directly, or should all history remain behind the top-right button?
