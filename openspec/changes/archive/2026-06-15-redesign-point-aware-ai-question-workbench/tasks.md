## 1. Session And Data Model

- [x] 1.1 Inspect existing AI generation, draft, publication, and point-aware metadata persistence paths.
- [x] 1.2 Add persistence for workbench sessions with mode, experiment id, optional point key, optional original question id, original-question snapshot, operator, status, and timestamps.
- [x] 1.3 Add persistence for session chat turns with role, content, provider metadata, error state, and timestamps.
- [x] 1.4 Add persistence for generated candidates linked to session turns with validation state, draft id when applicable, rejection/publish status, and lineage metadata.
- [x] 1.5 Implement server-side context assembly for repair mode from canonical question data, source audit, point bindings, option diagnostics, and answer metadata.
- [x] 1.6 Implement server-side context assembly for create mode from selected experiment, selected point, source coverage, and existing question coverage.

## 2. Backend APIs And AI Flow

- [x] 2.1 Add APIs to create or reopen repair and create workbench sessions.
- [x] 2.2 Add APIs to fetch a session with original context, chat turns, candidates, and validation results.
- [x] 2.3 Add API support for sending a teacher prompt as a new session turn and generating assistant responses.
- [x] 2.4 Update AI prompt construction to include immutable context, relevant prior turns or compact session memory, and the teacher's latest instruction.
- [x] 2.5 Convert AI responses into one or more structured candidates while preserving point-aware metadata and generation lineage.
- [x] 2.6 Validate candidate objective type, deterministic answer shape, point keys, source audit, option diagnostics where applicable, and lineage before marking a candidate publishable.
- [x] 2.7 Add APIs to reject a candidate, request another revision, and publish a valid candidate through the existing draft/publication path.
- [x] 2.8 Preserve teacher prompts and session state when provider generation fails, returning an actionable error state to the workbench.

## 3. Frontend Workbench

- [x] 3.1 Replace the detached AI suggestion drawer entry points with navigation into an AI question workbench surface.
- [x] 3.2 Build the repair-mode workbench layout with original-question context and AI conversation visible together.
- [x] 3.3 Build the original context panel for stem, options, answer, explanation, status, point keys, source audit, source references, option diagnostics, and lineage.
- [x] 3.4 Build the chat timeline and prompt composer for multi-turn repair/create prompts.
- [x] 3.5 Build candidate cards that show candidate content, changed fields, validation readiness, source/evidence state, and linked turn.
- [x] 3.6 Implement candidate actions for reject, continue revising, and publish with explicit confirmation.
- [x] 3.7 Build create-mode workbench context for selected experiment, selected point, source coverage, existing coverage, and generated candidates.
- [x] 3.8 Preserve selected experiment, point filter, keyword filter, and list position when exiting the workbench.
- [x] 3.9 Ensure the workbench is usable on desktop and narrow viewports without overlapping original context, chat, candidate actions, or validation text.

## 4. Verification

- [x] 4.1 Add backend tests for session creation/reopen, context assembly, chat turn persistence, candidate validation, rejection, and publication lineage.
- [x] 4.2 Add backend tests for generation failure preserving session state and teacher prompt history.
- [x] 4.3 Add frontend tests or focused manual coverage for repair-mode original context visibility, multi-turn prompts, candidate comparison, and publish/reject actions.
- [x] 4.4 Add frontend tests or focused manual coverage for create-mode workbench launch from experiment/point context.
- [x] 4.5 Run backend tests covering question-bank AI workflows.
- [x] 4.6 Run frontend typecheck and production build.
- [x] 4.7 Verify the local question-bank page in browser at desktop and narrow widths.
- [x] 4.8 Add Python Playwright CDP verification for taking over a Chrome question-bank tab.
- [x] 4.9 Run Python Playwright CDP verification against the teacher-visible Chrome page or report the missing DevTools endpoint blocker.
- [x] 4.10 Run `openspec validate redesign-point-aware-ai-question-workbench --strict`.
