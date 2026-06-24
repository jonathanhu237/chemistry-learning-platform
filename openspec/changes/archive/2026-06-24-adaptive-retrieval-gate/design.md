## Context

The student assistant already has several pieces of the needed architecture:

- `classify_agent_request()` creates a local classification with policy and RAG hints.
- `_run_openai_policy_gate()` optionally asks the configured LLM for a structured policy decision.
- `_apply_policy_decision_to_classification()` applies safety/resource decisions back to the run classification.
- `run_agent_stream()` emits student-safe `thinking` events from model reasoning summaries or agent trace fallback.
- Chat-completion and Responses payload builders still call `rag_search_tool()` whenever `allow_rag_lookup` is true, so the implementation does not fully honor the existing requirement that RAG is support for ordinary course answers rather than a hard requirement.

The design introduces a retrieval decision layer after safety/policy classification and before answer payload construction. It does not change the RAG engine itself.

Current simplified flow:

```text
question
  -> local classification
  -> policy gate
  -> if allow_rag_lookup then rag_search_tool
  -> answer generation
  -> output guardrails
```

Target flow:

```text
question
  -> local classification
  -> safety/policy gate
  -> retrieval decision gate
  -> execute only the selected retrieval/resource path
  -> answer generation
  -> output guardrails
```

## Goals / Non-Goals

**Goals:**

- Decide per student turn whether to skip dynamic RAG, use fixed point evidence, run dynamic RAG, perform platform resource lookup, or require strict evidence.
- Use the configured LLM as the semantic router when available; no new model/provider settings are required.
- Preserve deterministic safety and resource-boundary rules so important evidence-bound turns are not missed.
- Keep retrieval routing separate from safety guardrails while recording the decision in teacher/operator diagnostics.
- Make visible thinking reflect real retrieval decisions without exposing raw diagnostics or fake chain-of-thought.
- Reduce unnecessary RAG calls for ordinary explanations, follow-ups, equation reasoning, and safe conceptual guidance.
- Preserve existing behavior for explicit platform-resource availability, textbook/source image, citation, and "according to material" requests.

**Non-Goals:**

- No rewrite of BGE, Elasticsearch, chunk indexing, embeddings, or reranking.
- No teacher AI workflow changes beyond diagnostics where those views already inspect student assistant turns.
- No exposure of raw model chain-of-thought.
- No extra LLM configuration screen.
- No migration to a full Agents SDK tool-call runtime for every provider.
- No student-facing display of raw retrieval mode, policy labels, evidence ids, scores, or tool names.

## Decisions

### Decision 1: Add a retrieval decision object to runtime context

Add a small structured object, for example `StudentAIRetrievalDecision`, to `server/app/domains/assistant/runtime.py`.

Proposed fields:

```python
mode: Literal[
    "skip",
    "fixed_evidence",
    "dynamic_rag",
    "resource_lookup",
    "strict_evidence",
]
source: Literal["llm_policy", "hard_rule", "local_fallback", "feature_disabled"]
reason: str
student_reason: str
confidence: float | None
strict_evidence: bool
allowed_tools: tuple[str, ...]
should_call_rag: bool
should_call_resource_lookup: bool
should_use_fixed_point_evidence: bool
```

Rationale:

- A dedicated object is easier to test and reason about than spreading flags across `classification`.
- The final response can include teacher/admin diagnostics through existing `classification`, `guardrail_decisions`, or structured response metadata without changing the student UI contract.
- `StudentAIPolicyDecision` stays focused on safety/policy mode, while retrieval decision handles tool routing.

Alternative considered:

- Put more booleans directly into `classification`. This is faster but makes the policy layer harder to understand and risks repeating the current `allow_rag_lookup` ambiguity.

### Decision 2: Extend the existing policy gate instead of adding a separate model call

The configured LLM policy gate should return retrieval fields together with the existing policy decision:

```json
{
  "mode": "normal_answer",
  "reason": "ordinary learning answer",
  "evidence_required": false,
  "allowed_tools": [],
  "retrieval_mode": "skip",
  "retrieval_reason": "The student asks for a conceptual explanation, not platform evidence.",
  "retrieval_confidence": 0.88,
  "strict_evidence": false
}
```

Rationale:

- Uses the same configured LLM and connection already tested by the platform.
- Avoids an extra model call and keeps latency predictable.
- The existing fallback path can still work when the policy gate is unavailable or invalid.

Alternative considered:

- Add a second LLM router call after policy. This gives cleaner separation but costs latency and increases failure surface. Keep it as a future option only if combined policy/retrieval prompts become unreliable.

### Decision 3: Hard rules override LLM routing only at high-confidence boundaries

Hard rules should not try to parse all natural language. They only enforce boundaries that must not be missed.

Hard-on retrieval/resource cases:

- Explicit platform resource availability: uploaded, published, watch, download, link, file, video, material availability.
- Explicit source/citation/evidence request: cite, source, according to textbook/material, page, figure, evidence image, source image, Frost/Latimer/source diagram.
- `source_asset_request` and trusted point evidence/image requests.
- Policy mode `needs_platform_evidence`.
- Existing feature switch or request context indicates RAG is disabled: force no dynamic RAG.

Hard-off or normal-answer cases:

- Safety refusal and assessment hint modes should not run retrieval for answer generation unless the hint needs fixed point context.
- Ordinary short follow-ups inherit context and should not become platform evidence requests only because they are ambiguous.
- "Explain a video point" remains a learning answer, not platform resource availability.

Rationale:

- The LLM handles semantic nuance; hard rules protect product promises and safety boundaries.

Alternative considered:

- Full keyword-only routing. Rejected because Chinese natural language cannot be exhaustively matched and would regress on paraphrases.

### Decision 4: Replace direct `allow_rag_lookup` checks at generation entry points

Update these paths to consult the retrieval decision:

- `_run_openai_chat_completion()`
- `_run_openai_chat_completion_stream()`
- `_openai_answer_context_payload()`
- Any local/SDK path that currently infers retrieval solely from `classification["allow_rag_lookup"]`

Target behavior:

- `skip`: do not call `rag_search_tool`; pass empty supplemental RAG evidence and tell the answer prompt not to claim platform evidence.
- `fixed_evidence`: include trusted point evidence, skip supplemental dynamic RAG unless the decision also requires strict source evidence.
- `dynamic_rag`: call `rag_search_tool`; use evidence if relevant.
- `resource_lookup`: call resource lookup; do not fabricate resources.
- `strict_evidence`: call the required evidence/resource tool; if no usable evidence is found, output guardrails must prevent an unsupported platform-evidence claim.

Rationale:

- The primary bug is at these generation entry points: `allow_rag_lookup` currently means permission, but implementation treats it as obligation.

Alternative considered:

- Disable `rag_preferred` in local classification. This would reduce retrieval but would not solve explicit evidence routing, visible thinking, or policy gate integration.

### Decision 5: Retrieval quality is a post-retrieval decision, not a prompt wish

After dynamic RAG runs, classify evidence as usable or not usable using existing final evidence count and lightweight metadata checks.

Initial quality gate can be conservative:

- Usable when final evidence has at least one selected source with text preview, figure asset, or trusted source metadata.
- Unusable when retrieval returns empty evidence or only diagnostics/candidates that are not included in final evidence.
- For strict-evidence/resource turns, no usable evidence means "not found" or existing no-resource response.
- For ordinary turns, no usable evidence means answer from model chemistry knowledge without claiming platform support.

Rationale:

- Prevents weak keyword hits from constraining the answer.
- Does not require reranker-score threshold changes in this change.

Alternative considered:

- Add new reranker thresholds now. Rejected because it touches BGE tuning and should be separate from routing.

### Decision 6: Visible thinking uses retrieval decision phases

Agent trace fallback should add fixed safe phases:

- `policy`: judging question scope/type.
- `retrieval_decision`: deciding whether course material is needed.
- `context`: preparing current course context.
- `retrieval_skip`: answering without supplemental retrieval because evidence is not required.
- `fixed_evidence`: reading current point evidence.
- `retrieval`: searching course material or platform resources.
- `evidence_quality`: checking whether retrieved material is relevant.
- `generation`: organizing the answer.
- `fallback`: local fallback when model streaming fails.

These events must be emitted only when that operation actually starts or happens.

Rationale:

- Gives Atom a richer thinking path without fake model thinking.
- Aligns with the existing `reasoning_summary` first, `agent_trace` fallback contract.

Alternative considered:

- Keep only generic "generating" copy. Rejected because it hides the main product improvement and makes retrieval decisions invisible to students.

### Decision 7: Prompt wording must separate evidence-bound claims from ordinary explanations

Update answer instructions from "facts, experiment phenomena, equations, and resource recommendations must first call tools" to a narrower contract:

- Platform resource availability, citations, source images, textbook/material references, and "according to course material" claims must be grounded in tool evidence.
- Ordinary concept explanations, mechanism reasoning, equation derivations, and follow-up clarifications may use reliable chemistry knowledge when retrieval is skipped or unavailable.
- If no evidence was provided, the answer must not claim that a platform material, page, figure, or uploaded resource exists.
- Fixed point evidence remains trusted context for selected point explanations.

Rationale:

- The prompt currently nudges the model toward over-grounding every factual answer.

Alternative considered:

- Rely only on code-level routing. Rejected because the final model still needs to understand the meaning of empty evidence and strict-evidence fields.

## Risks / Trade-offs

- Risk: The router skips RAG for a question that should cite course material. -> Mitigation: hard-on rules for explicit evidence/platform wording, tests with paraphrases, and strict-evidence output guardrails.
- Risk: The LLM policy gate returns malformed or inconsistent retrieval fields. -> Mitigation: parse/validate retrieval modes, clamp confidence, fallback to deterministic local policy, record diagnostics.
- Risk: Ordinary answers become less grounded than before. -> Mitigation: skip only dynamic RAG; fixed point evidence and curriculum context remain available, and explicit evidence requests still force retrieval.
- Risk: More policy prompt complexity could increase latency. -> Mitigation: combine retrieval routing with the existing policy gate instead of adding a second LLM call.
- Risk: Debug metadata leaks to students. -> Mitigation: expose only sanitized `thinking.message` in H5; keep raw decision details to teacher/admin diagnostics and backend logs.
- Risk: Tests overfit to exact Chinese copy. -> Mitigation: assert phases/source/tool behavior and use stable safe copy constants rather than fragile UI text snapshots where possible.

## Migration Plan

1. Add retrieval decision data structures and parser defaults without changing generation behavior.
2. Extend policy gate prompt/parse logic and local fallback to fill retrieval decisions.
3. Switch generation payload builders from `allow_rag_lookup` obligation to retrieval-decision execution.
4. Add visible thinking phases for decision/skip/retrieval/evidence-quality.
5. Add diagnostics and tests.
6. Deploy backend first; existing H5 clients that ignore new phases remain compatible.

Rollback:

- Revert generation entry points to the previous `allow_rag_lookup` path if needed.
- Keep new metadata ignored by frontend/admin if rollback is partial.
- Since no database migration is required, rollback is code-only.

## Open Questions

- Should the first implementation expose retrieval-decision statistics in the teacher monitoring console, or only in the debug console turn inspector?
- Should `fixed_evidence` be a standalone mode or a flag that can combine with `skip`/`dynamic_rag`? The implementation can model it as a flag while keeping the public decision mode simple.
- Do we want a future teacher setting for "prefer grounded answers" that biases the router toward dynamic RAG? This is out of scope for the first implementation.
