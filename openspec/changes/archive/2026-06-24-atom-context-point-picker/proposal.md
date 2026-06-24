## Why

The Atom root assistant currently has a `+` affordance but no clear way for a global chat with no active point context to bind itself to a concrete learning point. Students need a lightweight way to choose one point from the existing catalog/search data without leaving Atom or opening the full video-library/search page.

## What Changes

- Add an Atom-internal half-height learning-background picker opened from the root composer `+`.
- Use one picker shell with two content modes:
  - default empty-query mode renders a catalog/directory selection component;
  - non-empty query mode renders a compact point-search list using existing video-library search data.
- Keep the picker visually inside Atom by using the existing root assistant/history-sheet bottom-sheet grammar, while leaving the underlying Atom title area readable.
- Bind at most one concrete point placement to the current chat.
- Display the selected point as an attachment-like learning-background chip/card near the composer before the first send.
- Lock the chat to the selected point once the first message is sent; changing the point after that requires starting a new Atom chat.
- Preserve the current default `learning_home` global assistant path when no point is selected.
- Reuse existing catalog, learning-page, and video-library search data contracts where possible; avoid a new full search route, new backend chat-session model, or broad search redesign.

## Capabilities

### New Capabilities
- `student-h5-atom-context-picker`: Defines the Atom root `+` learning-background picker, directory/search mode switch, selected-point chip, and one-point chat binding lifecycle.

### Modified Capabilities
- `student-h5-ai-assistant`: The root assistant composer gains a supported learning-background picker action and bound-point display while preserving direct free-form asking.
- `point-context-learning-assistant`: Point context may be selected from the Atom root before asking and then must be preserved as the fixed context for that chat.

## Impact

- Frontend:
  - `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/web-student/src/features/assistant/assistantContext.ts`
  - `apps/web-student/src/styles/assistant.css`
  - catalog browsing helpers/components under `apps/web-student/src/features/catalog/` and `apps/web-student/src/routes/learn/`
  - video-library/search helpers under `apps/web-student/src/routes/video-library/VideoLibraryPage.tsx`
- APIs:
  - Prefer existing student catalog APIs and existing `searchStudentVideoLibrary(query)` response shape.
  - Existing assistant stream payload should continue to carry `AssistantContext` fields such as `context_type`, `context_title`, `context_summary`, `chapter_id`, `experiment_id`, `point_node_id`, `source_node_id`, `catalog_path`, and `knowledge_point_ids`.
- UX and layout:
  - Reuse the Atom history sheet height baseline: `min(72dvh, 640px)`.
  - Use visual-viewport/keyboard variables already provided by the student shell so the picker and bottom search field remain usable when the keyboard opens.
  - Do not navigate away from `/ai` to `/search` or `/video-library` for this picker.
