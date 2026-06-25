## 1. Audit Active Assistant Runtime

- [x] 1.1 Re-run code search for synchronous OpenAI usage under `server/app/domains/assistant` and classify each match as active Atom runtime, dead legacy helper, or out-of-scope utility.
- [x] 1.2 Confirm `run_agent_stream` reaches only `_run_openai_responses_stream` or `_run_openai_chat_completion_stream` for OpenAI-backed streaming.
- [x] 1.3 Confirm student and teacher streaming endpoints still pass `should_cancel` into the shared runtime.
- [x] 1.4 Confirm no tests or runtime imports reference the legacy always-RAG OpenAI helper names before deleting them.

## 2. Remove Legacy Synchronous Stream Code

- [x] 2.1 Delete `_legacy_run_openai_chat_completion_always_rag` from `server/app/domains/assistant/agent.py`.
- [x] 2.2 Delete `_legacy_openai_answer_context_payload_always_rag` if it is only used by deleted legacy helpers.
- [x] 2.3 Delete `_legacy_run_openai_chat_completion_stream_always_rag` from `server/app/domains/assistant/agent.py`.
- [x] 2.4 Delete `_legacy_run_local_agent_always_rag` if it is only used by removed always-RAG legacy paths.
- [x] 2.5 Remove now-unused imports or helper code introduced only for the deleted legacy paths.

## 3. Make Remaining Atom One-Shot OpenAI Calls Async-Safe

- [x] 3.1 Replace `_run_openai_chat_completion` synchronous `OpenAI` usage with the existing async OpenAI client factory or remove the helper if it is no longer needed.
- [x] 3.2 Remove `_openai_client` from `agent.py` if no active assistant-domain code still needs it.
- [x] 3.3 Verify `_run_openai_policy_gate` and student follow-up/title metadata generation use `AsyncOpenAI`.
- [x] 3.4 Preserve existing provider failure fallback behavior and cancellation handling after the one-shot cleanup.

## 4. Add Static Regression Enforcement

- [x] 4.1 Add a backend static test that scans `server/app/domains/assistant` for disallowed synchronous OpenAI client imports and constructors.
- [x] 4.2 Extend the static test to reject synchronous `stream=True` provider loops such as `for chunk in stream`.
- [x] 4.3 Allow `AsyncOpenAI` and async provider streaming patterns in the static test.
- [x] 4.4 Add clear failure messages that identify the file and disallowed pattern.
- [x] 4.5 Keep the static test scoped to Atom assistant runtime code so unrelated non-Atom OpenAI usage is not accidentally pulled into this change.

## 5. Strengthen Runtime Regression Tests

- [x] 5.1 Keep or extend the test proving a slow fake provider stream allows unrelated async work to complete before the delayed delta.
- [x] 5.2 Keep or extend tests proving cancellation before provider generation emits no events and records no provider failure.
- [x] 5.3 Keep or extend tests proving cancellation during provider streaming emits no stale `delta`, `final`, or `error`.
- [x] 5.4 Keep or extend tests proving real connected provider/runtime errors still surface through the existing safe error path.
- [x] 5.5 Add a focused assertion that `run_agent_stream` branches call async provider helper names and not removed legacy helper names.

## 6. Verification

- [x] 6.1 Run `python -m pytest server/tests/test_student_assistant.py server/tests/test_student_assistant_visible_thinking.py server/tests/test_student_assistant_length_guardrail.py -q`.
- [x] 6.2 Run the new static assistant async enforcement test directly.
- [x] 6.3 Run `python -m py_compile server/app/domains/assistant/agent.py server/app/domains/assistant/student_assistant.py server/app/api/student/student_assistant.py server/app/api/admin/admin_learning_assistant.py`.
- [x] 6.4 Run `openspec validate enforce-async-atom-ai-streaming --strict`.
- [x] 6.5 If backend code changed, hot-update or rebuild the backend container according to the current local deployment workflow.
- [x] 6.6 Smoke-check that the backend health endpoint still responds after update.
