## 1. Student Guardrail Runtime

- [x] 1.1 Verify local student chat classification covers greetings, out-of-course requests, unsafe experiment requests, assessment-answer requests, resource requests, progress lookup, and evidence-required course facts.
- [x] 1.2 Ensure preflight guardrails refuse or hint before model/tool execution for out-of-course, unsafe experiment, and direct assessment-answer requests.
- [x] 1.3 Ensure course-factual and resource answers use platform evidence when available and avoid fabricated sources or resources.
- [x] 1.4 Harden optional model policy gate invalid-output handling so invalid decisions fall back to local policy instead of normal answer mode.
- [x] 1.5 Revise ordinary course-factual answers so RAG is optional support and model chemistry knowledge can answer when RAG is disabled or has no match.

## 2. Admin Test API

- [x] 2.1 Add an admin-only learning assistant test endpoint that executes requests as student chat.
- [x] 2.2 Respect student AI assistant and student RAG feature switches in the test endpoint.
- [x] 2.3 Return answer, mode, classification, tool calls, source refs, guardrail decisions, and review flag for admin diagnostics.

## 3. Admin Web Test Page

- [x] 3.1 Add a "学习助手" admin-only navigation item and route.
- [x] 3.2 Build the test form with question, optional context fields, RAG/progress toggles, and sample prompts.
- [x] 3.3 Display current AI configuration status and returned guardrail diagnostics.
- [x] 3.4 Hide the page from teacher navigation so it is not presented as a teacher workflow.

## 4. Verification

- [x] 4.1 Add backend tests for representative student guardrail decisions and invalid policy gate fallback.
- [x] 4.1a Add backend regression coverage for Agent SDK failure falling back to ordinary model answers without source-grounding override.
- [x] 4.2 Run backend syntax/tests for the student guardrail path.
- [x] 4.3 Run admin web typecheck and production build.
- [x] 4.4 Run `openspec validate student-chat-guardrails --strict`.
