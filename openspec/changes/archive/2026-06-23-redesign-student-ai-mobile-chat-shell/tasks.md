## 1. Chat Shell Structure

- [x] 1.1 Read current student AI route, chat panel, assistant context, navigation, and relevant teacher learning assistant chat code before editing.
- [x] 1.2 Refactor the student chat panel into a reusable mobile chat shell that supports root and detail variants without duplicating stream logic.
- [x] 1.3 Preserve existing streaming behavior: status events, delta/replace/final events, error turns, markdown rendering, source summary, and recent `conversation_history`.
- [x] 1.4 Keep non-global context visible and dismissible in the detail variant while avoiding duplicate intro/current-content cards.

## 2. Root AI Chat Page

- [x] 2.1 Replace the `/ai` root center card with the direct mobile chat shell using the default `learning_home` context.
- [x] 2.2 Add root top-bar content with course assistant identity and a right-top history action.
- [x] 2.3 Ensure the root first screen has a visible composer and no required prompt, point, model, attachment, or voice step before asking.
- [x] 2.4 Tune root AI mobile layout so the composer fits above bottom navigation and safe areas.

## 3. Contextual AI Detail Page

- [x] 3.1 Keep `/ai/chat` as a second-level `DetailPageFrame` route using the shared chat shell in detail mode.
- [x] 3.2 Ensure contextual chat omits the root history action and keeps source-aware back behavior.
- [x] 3.3 Keep existing page callers routed to `/ai/chat` when they open contextual AI from point, video result, or assessment flows.
- [x] 3.4 Preserve assistant-disabled behavior for both `/ai` and `/ai/chat`.

## 4. Local History

- [x] 4.1 Add a small student AI local history store for create/update/list/read/delete or clear behavior.
- [x] 4.2 Save root chat conversations as local history entries when a student sends turns.
- [x] 4.3 Save contextual chat conversations into history metadata without showing history chrome on `/ai/chat`.
- [x] 4.4 Implement the `/ai` history panel/list with empty state, context labels, restore behavior, and safe close behavior.
- [x] 4.5 Ensure restored history sends recent restored turns as `conversation_history` on follow-up.

## 5. Context Compatibility

- [x] 5.1 Audit the student assistant request type and backend conversion for point/context fields.
- [x] 5.2 If low-risk, forward existing `point_node_id`, `source_node_id`, and `catalog_path` fields through the student assistant backend conversion into `AgentAskRequest`.
- [x] 5.3 Add or update focused tests if context compatibility behavior changes.

## 6. Tests And Verification

- [x] 6.1 Update student frontend tests for `/ai` root direct chat shell, visible composer, no unsupported controls, and root history button.
- [x] 6.2 Update student frontend tests for `/ai/chat` contextual detail behavior and root-history omission.
- [x] 6.3 Update tests for assistant-disabled AI root and detail behavior.
- [x] 6.4 Run focused frontend tests for the student app.
- [x] 6.5 Run focused backend tests if backend context compatibility changes.
- [x] 6.6 Run `openspec validate redesign-student-ai-mobile-chat-shell --strict`.
- [x] 6.7 Start the student frontend locally and perform mobile viewport visual verification for `/ai` and `/ai/chat`.
