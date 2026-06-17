## Why

The project now needs to accept PR #1's student-facing H5 learning experience without regressing the productionization work already completed on the current branch. This change turns the PR into a controlled platform integration: student functionality is added, while admin router ownership, production resource protection, manual CI behavior, and the split AI policy architecture remain intact.

## What Changes

- Add a student H5 frontend app under `apps/student-web` and serve it from FastAPI alongside the existing admin console.
- Add student authentication flows for roster-backed first login, forced password change, and session-aware student identity.
- Add student pretest, learning-home, experiment group/detail, posttest, and student AI assistant APIs.
- Add database migrations for student H5 login and student assessment sessions.
- Integrate student AI assistant behavior with the existing student chat guardrails and AI configuration switches.
- Extend production readiness validation to include both admin and student frontends.
- Preserve existing productionization decisions: FastAPI lifespan startup, split admin routers, `agent_policy` service ownership, protected core resource manifests, and manual-only CI.
- Resolve PR #1 conflicts against the current production branch rather than accepting stale implementation details.

## Capabilities

### New Capabilities
- `student-h5-authentication`: Student login, roster activation, forced password change, and student session identity.
- `student-h5-learning-flow`: Student-facing learning overview, experiment group/detail content, and protected media access.
- `student-h5-assessment-flow`: Student pretest and posttest session lifecycle, answer submission, cached summaries, and mistake explanations.
- `student-h5-platform-shell`: Student H5 frontend delivery, FastAPI static serving, and production readiness validation.

### Modified Capabilities
- `student-chat-guardrails`: Student assistant requests from the H5 app must use the existing guardrail policy scope and feature-switch behavior.
- `class-roster-management`: Roster entries become the authoritative activation source for student H5 login.
- `class-learning-analytics`: Student pretest/posttest and learning activity records must remain compatible with class/student analytics.
- `experiment-centered-course-management`: Student learning pages must expose only active/published experiment resources and preserve unavailable-resource behavior.

## Impact

- Backend: `server/app/auth.py`, `server/app/admin_main.py`, student routers, student services, student schemas, AI agent policy integration, and migration files.
- Frontend: new `apps/student-web` Vite/React app plus static serving and deployment documentation.
- Validation: `scripts/validate_production_readiness.py`, production operations docs, backend pytest suite, admin frontend checks, student frontend typecheck/build.
- Data safety: protected seed resources and `data/seed/manifests/core_resources.json` must not be changed unless the underlying protected resources intentionally change.
