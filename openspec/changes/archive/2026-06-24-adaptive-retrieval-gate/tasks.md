## 1. Runtime Decision Model

- [x] 1.1 Add a `StudentAIRetrievalDecision` runtime structure with mode, source, reason, student-safe reason, confidence, strict-evidence state, allowed tools, and execution booleans.
- [x] 1.2 Add `retrieval_decision` to `AgentRunContext` and include teacher/operator-safe decision metadata in built assistant responses without changing student answer text.
- [x] 1.3 Add parser validation for retrieval modes and confidence values, including safe defaults for missing, malformed, or unknown fields.

## 2. Policy Gate and Local Routing

- [x] 2.1 Extend the OpenAI-compatible policy gate prompt to request retrieval mode, retrieval reason, retrieval confidence, and strict-evidence output in the same JSON response.
- [x] 2.2 Update policy decision parsing so valid LLM retrieval fields populate the runtime retrieval decision.
- [x] 2.3 Implement deterministic local retrieval fallback for ordinary explanation, explicit evidence request, source asset request, platform resource request, fixed point evidence, RAG-disabled, safety, and assessment paths.
- [x] 2.4 Implement hard-rule overrides that force evidence/resource lookup for explicit platform evidence boundaries and prevent platform resource lookup for ordinary learning explanations.
- [x] 2.5 Record retrieval decision source and override diagnostics in guardrail/diagnostic data for teacher/operator inspection only.

## 3. Generation and Tool Execution

- [x] 3.1 Replace direct `allow_rag_lookup` obligation checks in `_run_openai_chat_completion()` with retrieval-decision execution.
- [x] 3.2 Replace direct `allow_rag_lookup` obligation checks in `_run_openai_chat_completion_stream()` with retrieval-decision execution.
- [x] 3.3 Replace direct `allow_rag_lookup` obligation checks in `_openai_answer_context_payload()` with retrieval-decision execution.
- [x] 3.4 Ensure `skip` mode does not call `rag_search_tool` and passes empty supplemental RAG evidence with no platform-evidence claim.
- [x] 3.5 Ensure `fixed_evidence` mode includes hydrated point evidence without requiring supplemental dynamic RAG.
- [x] 3.6 Ensure `dynamic_rag`, `resource_lookup`, and `strict_evidence` modes call only the selected tool paths and preserve existing no-resource/no-evidence fail-closed behavior.
- [x] 3.7 Add a lightweight usable-evidence check that distinguishes selected supporting evidence from empty or non-supporting retrieval results.
- [x] 3.8 Update answer instructions so ordinary explanations can use reliable chemistry knowledge while platform resources, citations, source images, and course-material claims require evidence.

## 4. Visible Thinking Stream

- [x] 4.1 Add fixed safe agent trace keys and copy for `retrieval_decision`, `retrieval_skip`, `fixed_evidence`, `retrieval`, `evidence_quality`, `generation`, and `fallback`.
- [x] 4.2 Update `run_agent_stream()` to emit retrieval-decision trace events only when the matching operation actually starts or occurs.
- [x] 4.3 Ensure skipped retrieval emits a student-safe skip/knowledge organization trace and never claims course-material search ran.
- [x] 4.4 Ensure dynamic retrieval and evidence-quality traces appear only when RAG or platform lookup actually runs.
- [x] 4.5 Verify H5 running-line rendering continues to use sanitized `thinking.message` without exposing raw phase, tool, provider, or policy details.

## 5. Diagnostics and Debug Console

- [x] 5.1 Include retrieval decision metadata in structured assistant diagnostics available to admin/debug views.
- [x] 5.2 Update the learning assistant debug console inspector to display retrieval mode, source, confidence, strict-evidence state, reason, override state, and executed retrieval/resource actions.
- [x] 5.3 Show explicit empty states for skipped dynamic RAG so stale RAG traces from previous turns are not displayed.
- [x] 5.4 Keep student H5 source summaries and action-row citation disclosure unchanged except for existing sanitized source metadata when evidence is actually used.

## 6. Tests and Verification

- [x] 6.1 Add backend tests proving ordinary concept/explanation questions skip dynamic RAG while still generating an answer.
- [x] 6.2 Add backend tests proving explicit citation/source/textbook/material requests require evidence and fail closed when no usable evidence exists.
- [x] 6.3 Add backend tests proving platform resource availability requests use resource lookup and do not fabricate missing resources.
- [x] 6.4 Add backend tests proving RAG-disabled turns do not call dynamic RAG and still answer ordinary questions from model/local knowledge when available.
- [x] 6.5 Add backend tests proving malformed or unavailable policy-gate output falls back to deterministic local retrieval routing.
- [x] 6.6 Add stream tests proving `agent_trace` thinking phases reflect retrieval decision, skipped retrieval, actual retrieval, evidence quality, generation, and fallback without raw diagnostics.
- [x] 6.7 Add debug-console or response-shape tests proving retrieval decision diagnostics are present for teacher/operator views and absent from student-visible thinking text.
- [x] 6.8 Run targeted assistant tests and relevant frontend type/tests for changed surfaces.
