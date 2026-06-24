## Why

The student Atom assistant currently tends to run course-material RAG for most chemistry questions whenever RAG is enabled, even when the student is asking for an explanation that does not require platform evidence. This can slow answers, constrain model reasoning around incidental textbook snippets, and make the visible thinking stream feel like a preset "always searching" workflow rather than a truthful agent decision.

This change introduces an adaptive retrieval decision layer so Atom can decide whether a turn needs platform evidence, fixed point context, dynamic RAG, resource lookup, or no retrieval before generating the answer.

## What Changes

- Add a student-assistant retrieval decision capability that combines deterministic hard rules with the configured LLM policy gate.
- Extend the policy decision contract with a retrieval mode, confidence, strict-evidence flag, and student-safe reason.
- Route answer generation through the retrieval decision instead of treating `allow_rag_lookup=true` as "always call RAG".
- Keep safety, assessment, and course-scope guardrails separate from retrieval routing while allowing retrieval decisions to be recorded in diagnostics.
- Require dynamic RAG or resource lookup only for evidence-bound requests such as citations, textbook/source figures, platform materials, videos, links, uploaded resources, and explicit "according to course material" questions.
- Allow ordinary concept explanations, mechanism reasoning, equation derivations, follow-up clarifications, and safe learning guidance to answer from model chemistry knowledge without dynamic RAG.
- Add retrieval-decision agent trace phases so the H5 Atom running line can show truthful progress such as deciding whether course material is needed, skipping retrieval, searching course material, evaluating evidence relevance, and generating the answer.
- Add tests for strict evidence requests, ordinary explanation skips, platform resource lookup, RAG-disabled fallback, policy-gate failure fallback, and student-safe visible thinking.
- No breaking API changes. Existing clients that ignore new metadata or thinking phases continue receiving normal answer streams.

## Capabilities

### New Capabilities
- `student-assistant-retrieval-decision`: Defines adaptive retrieval routing for student assistant turns, including LLM semantic routing, hard-rule overrides, retrieval modes, evidence quality handling, diagnostics, and fallback behavior.

### Modified Capabilities
- `student-chat-guardrails`: Clarifies that the student policy gate SHALL drive evidence requirements and retrieval routing separately from safety guardrails, and that ordinary course answers SHALL NOT automatically run RAG solely because RAG is enabled.
- `student-ai-visible-thinking-stream`: Adds truthful agent trace messages for retrieval-decision, retrieval-skip, dynamic retrieval, evidence-quality, and fixed-evidence phases.
- `learning-assistant-debug-console`: Adds teacher/operator diagnostics for retrieval decision mode, source, confidence, reason, and whether dynamic RAG was skipped or executed.

## Impact

- Backend assistant domain:
  - `server/app/domains/assistant/runtime.py`
  - `server/app/domains/assistant/policy.py`
  - `server/app/domains/assistant/agent.py`
  - assistant tests under `server/tests/`
- Student H5:
  - existing `thinking` stream rendering should work with new phases; minimal copy/state tests may be needed.
- Teacher/debug diagnostics:
  - debug console and structured final response diagnostics may expose retrieval-decision metadata to teacher/operator views only.
- RAG infrastructure:
  - no changes to BGE service, Elasticsearch indexing, chunk embeddings, or retrieval corpus format.
- AI configuration:
  - no extra model configuration required. The existing configured LLM is used for the semantic policy/router call when available, with deterministic fallback when unavailable.
