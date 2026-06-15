## Why

The current AI suggestion drawer feels disconnected from the question being repaired: teachers can trigger a repair without seeing the original item, source evidence, option diagnostics, or a persistent conversation around the repair attempt. Modern question-bank workflows keep item context, review state, generated candidates, and final adoption in one continuous authoring surface; this change turns AI repair from a one-shot side form into a point-aware question workbench.

## What Changes

- Introduce an AI question workbench for point-aware question-bank repair and AI-assisted creation.
- Show the original question, answer, explanation, linked experiment point(s), source evidence, option-level diagnostic metadata, and publication status alongside the AI conversation.
- Support one repair session per selected question with multi-turn teacher prompts, chat history, generated candidate versions, and candidate comparison against the original item.
- Let teachers accept, reject, regenerate, or continue revising individual candidates without mutating the live bank until an explicit publish action.
- Add readiness and evidence checks before publication, including deterministic objective type, answer shape, point bindings, source audit, option diagnostic links where applicable, and generation lineage.
- Replace the current detached repair drawer behavior with a cohesive workspace surface that can be reopened with prior session state.
- Preserve the existing add-question AI path, but route it through the same context-rich workbench when the teacher is creating questions for an experiment or point.

## Capabilities

### New Capabilities
- `point-aware-ai-question-workbench`: Defines AI repair/create sessions, multi-turn chat, candidate versions, comparison, validation, adoption, and audit behavior for point-aware question-bank assistance.

### Modified Capabilities
- `experiment-question-bank-management`: Changes the question detail and AI-assistance experience from a detached modal/drawer flow to an integrated question workbench entry point that preserves original-question context.

## Impact

- Admin frontend question bank page and question detail/AI assistance UI.
- Admin API for AI suggestion generation, repair sessions, candidate drafts, publication, rejection, and lineage.
- Database or persistence layer for AI repair sessions, chat turns, generated candidates, validation state, and adoption audit.
- Existing point-aware question draft validation and publication paths.
- Tests for frontend workflow, backend session APIs, validation gates, and OpenSpec validation.
