## Why

Student-facing chat needs a narrow safety and scope layer before it can be trusted inside learning pages. The current need is intentionally small: protect the student learning assistant from out-of-course, unsafe experiment, assessment-answer, and ungrounded course-fact responses, while giving admins a quick page to test the behavior.

## What Changes

- Add a student chat guardrails capability for the learning assistant.
- Classify student messages for course scope, experiment safety, assessment-answer requests, resource lookup, progress lookup, and course-factual evidence requirements.
- Enforce deterministic preflight refusals or hints for non-learning, unsafe, and assessment-answer requests before invoking the model or tools.
- Use RAG as optional support for ordinary course-factual answers, while still refusing to fabricate unavailable platform resources.
- Add an admin-only "学习助手" page for functional testing of the same student chat path and guardrail decisions.
- Keep teacher AI workflows out of this guardrail scope.

## Capabilities

### New Capabilities

- `student-chat-guardrails`: Defines the student learning assistant chat scope, safety policy, grounding behavior, and admin functional-test API behavior.

### Modified Capabilities

- `react-ant-design-admin-console`: Adds a "学习助手" admin route for testing student chat guardrail behavior.

## Impact

- Backend: `server/app/agent.py`, `server/app/admin.py`, existing AI/platform settings, and agent logging.
- Frontend: `apps/admin-web/src/App.tsx`, `apps/admin-web/src/api.ts`, `apps/admin-web/src/styles.css`.
- Validation: backend guardrail tests, admin web typecheck/build, and OpenSpec strict validation.
