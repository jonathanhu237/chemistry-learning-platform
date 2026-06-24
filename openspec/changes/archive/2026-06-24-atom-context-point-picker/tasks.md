## 1. Context Mapping and State Model

- [x] 1.1 Inventory existing `AssistantContext` producers in home feed, video-library/search results, catalog point detail, and assessment report to identify reusable field mapping.
- [x] 1.2 Extract or add a frontend helper that converts a bindable catalog point/search result into an `AssistantContext` without navigating away from `/ai`.
- [x] 1.3 Add root-chat state for selected point context, editable-before-send status, and locked-after-first-send status.
- [x] 1.4 Ensure submitting from the root assistant uses the selected point context when present and preserves the existing global `learning_home` context when absent.

## 2. Picker Shell and Layout

- [x] 2.1 Add an Atom root learning-background picker sheet component opened by the composer `+` action.
- [x] 2.2 Style the picker as a bottom sheet using the Atom history-sheet baseline height `min(72dvh, 640px)`.
- [x] 2.3 Add visual-viewport and keyboard-safe sizing so the bottom search field stays visible and the Atom title/header area is not covered.
- [x] 2.4 Add accessible close/dismiss behavior and preserve composer focus/state when the picker is dismissed without selection.

## 3. Catalog Selection Mode

- [x] 3.1 Build the empty-query picker body as a catalog/chapter root selection surface.
- [x] 3.2 Reuse existing student catalog APIs to lazily load root and directory child nodes.
- [x] 3.3 Render directory rows as navigation-only rows and point rows as selectable learning-background rows.
- [x] 3.4 Add loading, empty, and error states for catalog root and directory loads inside the picker.

## 4. Compact Search Mode

- [x] 4.1 Wire the picker footer search input with a small debounce and query state.
- [x] 4.2 Switch the picker body from catalog mode to search mode when the trimmed query is non-empty.
- [x] 4.3 Reuse `searchStudentVideoLibrary(query)` or its shared helper to fetch student-visible point-placement results.
- [x] 4.4 Render compact one-row bindable point results with title, concise path/context, and snippet, without thumbnails or full video-library chrome.
- [x] 4.5 Filter or disable non-point results so the picker cannot bind directory-only or unsupported contexts.
- [x] 4.6 Add search loading, empty, error, and retry behavior within the picker.

## 5. Bound Point Chip and Chat Lifecycle

- [x] 5.1 Show an attachment-like learning-background chip/card near the root composer after a point is selected.
- [x] 5.2 Include selected point title and concise catalog path/context on the chip.
- [x] 5.3 Allow remove or replace while the root chat has no submitted user messages.
- [x] 5.4 Lock the selected point after the first submitted user message and prevent silent mid-chat replacement.
- [x] 5.5 Reset selected point binding when the existing new-chat action starts a fresh root Atom chat.
- [x] 5.6 Ensure restored global chats do not show a false selected-point chip.

## 6. Local History and Request Preservation

- [x] 6.1 Persist enough selected-point context in local history entries to restore bound chats.
- [x] 6.2 Restore the selected-point chip and active context when a bound-point history entry is opened from the root history sheet.
- [x] 6.3 Send follow-up questions from restored bound chats with the same selected point context and visible conversation history.
- [x] 6.4 Preserve existing local history behavior for global and contextual chats that do not use the picker.

## 7. Verification

- [x] 7.1 Add focused component or integration tests for opening the picker, dismissing it, selecting a point, replacing before send, and locking after send.
- [x] 7.2 Add tests for root assistant request context selection: global with no point, selected point before first send, and restored bound history.
- [x] 7.3 Verify picker layout at 360px, 390px, and 430px mobile widths for empty catalog mode, search results mode, and keyboard-focused search input.
- [x] 7.4 Verify the `+` action does not imply file upload or unsupported tools and that direct global free-form asking still works.
- [x] 7.5 Run the relevant frontend lint/type/test command for the student web app and record any unavailable checks.
