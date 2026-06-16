## Context

The admin-only repository already includes an agent runtime that can answer student learning questions with optional RAG, curriculum lookup, published-resource lookup, and own-progress lookup. The product scope for this change is a single student learning-page chat surface, plus an admin test page named "学习助手" to exercise that same student path.

The guardrails must stay smaller than a general-purpose LLM safety framework. Teachers do not need these guardrails for their own AI workflows, and the admin page is a functional test surface rather than a teacher-facing assistant.

## Goals / Non-Goals

**Goals:**

- Enforce student chat scope before model/tool execution where possible.
- Refuse out-of-course and unsafe experiment-detail requests.
- Provide hints instead of direct assessment answers.
- Prefer platform evidence for ordinary course-factual answers when RAG is enabled, while allowing model chemistry knowledge when RAG is disabled or has no match.
- Require platform lookup for published-resource and platform-availability claims.
- Surface policy decisions, tool calls, sources, and guardrail actions in an admin-only test page.

**Non-Goals:**

- Add a full policy-authoring product or generic guardrail platform.
- Apply student guardrails to teacher question-bank assistants, teacher analytics, or other teacher AI workflows.
- Build a moderation queue, human review workflow, or complex taxonomy editor.
- Depend on heavyweight guardrail frameworks for this narrow use case.

## Decisions

1. Use a narrow in-repo policy layer instead of adding a general guardrail framework.

   The student learning assistant needs deterministic checks for a known education scenario. Existing open-source approaches such as NeMo Guardrails, Guardrails AI validators, Open WebUI filters, Dify moderation extensions, LangChain middleware, LLM Guard, and Llama Guard-style classifiers all separate input checks, tool permissions, and output checks. This implementation keeps those concepts but avoids introducing a broad framework that would be disproportionate for one student chat.

2. Gate before tools and output-check after answer generation.

   Preflight guardrails handle out-of-scope requests, unsafe experiment-detail requests, simple greetings, and assessment-answer leakage. Tool permissions are then derived from the policy decision. Output guardrails prevent fabricated platform resources and overly long mobile responses. Ordinary chemistry facts can still be answered from model knowledge when platform evidence is unavailable.

3. Treat optional LLM policy decisions as an enhancement, not the source of truth.

   The system can call an OpenAI-style policy gate when configured, but invalid or unavailable policy decisions fall back to local deterministic classification. Invalid structured output must not turn a risky request into a normal answer.

4. Reuse existing student AI feature switches.

   The admin test endpoint respects the student AI assistant switch and the RAG access switch. If RAG is disabled, the endpoint must not pass RAG permission into the agent even if the tester toggles it on.

5. Make the admin page diagnostic rather than instructional.

   The "学习助手" page exposes inputs, sample prompts, switches, and raw policy diagnostics so admins can verify behavior. It is hidden from teacher operators, does not add a teacher assistant workflow, and does not hide the fact that the request is simulated as a student chat.

## Risks / Trade-offs

- Local keyword classification can miss nuanced unsafe or off-scope prompts. Mitigation: keep the local policy conservative for the known Chinese chemistry-learning cases and allow an optional model gate.
- RAG-disabled answers may be less aligned with local course wording. Mitigation: clearly log `rag_lookup_disabled`, avoid fabricated source claims, and prefer RAG evidence whenever it is available.
- Admin testing could be mistaken for a teacher assistant. Mitigation: keep the page admin-only, label it as student learning chat simulation, and route requests through `user_role="student"`.
- Policy diagnostics can expose implementation detail. Mitigation: keep the page inside authenticated admin console access and do not expose it to student users.

## Migration Plan

No database migration is required. Deploy backend and admin frontend together so the new route and client types are available at the same time. In the local Docker Compose environment, every backend code update for this change must rebuild and recreate the backend service with `docker compose up -d --build backend`; browser refresh, Vite hot reload, or a plain container restart is not sufficient because backend source is baked into the image rather than bind-mounted. After the rebuild, verify the changed routes against the running backend, such as by checking `/openapi.json` for `/api/admin/learning-assistant/ask/stream`. Rollback is the inverse deployment: remove or hide the admin route, rebuild the backend image, and leave existing agent behavior untouched.

## Open Questions

- None.
