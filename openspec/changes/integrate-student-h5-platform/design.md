## Context

PR #1 adds a student-facing H5 app, student authentication, pretest/posttest flows, learning pages, and student AI assistant APIs. The current branch has already completed productionization work that must not regress: FastAPI uses lifespan startup instead of `on_event`, admin endpoints are split across owned routers/services, student AI policy code lives in `server/app/services/agent_policy.py`, CI is manual-only, and protected seed resources are guarded by manifests.

The integration target is therefore not a direct merge of the PR branch. It is a controlled accept: keep the student product surface, discard stale implementation details that conflict with the productionized architecture, and extend validation so both admin and student frontends are covered.

## Goals / Non-Goals

**Goals:**

- Integrate PR #1's student H5 frontend and backend APIs into the current production branch.
- Keep current production architecture decisions intact, including lifespan startup and split admin/service ownership.
- Preserve protected core resource files and manifests unless the actual protected resources intentionally change.
- Make student functionality deployable from the same FastAPI service as the admin console.
- Extend production readiness validation to include `apps/student-web`.
- Keep the branch in a state where the PR can be considered functionally accepted after verification.

**Non-Goals:**

- Redesign the student H5 UI beyond conflict-safe integration.
- Fully modularize the new student frontend during this acceptance pass.
- Change GitHub Actions trigger policy or add release automation.
- Delete local media files or historical assets.
- Rework admin console behavior unrelated to student integration.

## Decisions

### Decision: Port the PR into the production branch rather than merging it verbatim

The PR is based on an older branch state and conflicts with recent productionization. The integration will keep its student functionality while resolving conflicts in favor of the current branch for architecture-sensitive files.

Alternatives considered:

- Direct merge: fastest, but would reintroduce `@app.on_event`, duplicate AI policy code in `agent.py`, and risk stale readiness docs.
- Cherry-pick only frontend: safer for frontend, but would drop backend tests and migration context.

### Decision: Keep FastAPI lifespan as the only startup hook

Student routers and static mounts will be added to `admin_main.py`, but startup database initialization remains inside the existing lifespan flow.

Alternatives considered:

- Keep PR's `@app.on_event("startup")`: rejected because it reintroduces a known deprecation warning and conflicts with the current app lifecycle.

### Decision: Keep student AI policy ownership in `services/agent_policy.py`

PR #1 includes a copy of `classify_agent_request` in `agent.py`. The integration will not re-add that copy. Student assistant APIs will use the existing formal agent entry points and the existing policy module.

Alternatives considered:

- Accept the copied function: rejected because it recreates the compatibility-layer risk the previous router/service split removed.

### Decision: Serve admin and student static apps from one FastAPI deployment

The admin build remains mounted under `/admin` and `/admin/assets`. The student build is served at `/` with `/assets`, while API prefixes remain excluded from SPA fallback.

Alternatives considered:

- Serve student H5 from a separate service: valid for later scale-out, but unnecessary for this integration and would expand deployment scope.

### Decision: Treat protected resource manifest changes as opt-in

The integration will not accept changes to `data/seed/manifests/core_resources.json` unless the corresponding protected files are intentionally changed and resource validation passes.

Alternatives considered:

- Accept the PR manifest hash drift: rejected because current question bank, knowledge framework, point inventory, canonical chunks/embeddings, and evidence bindings are production-critical.

## Risks / Trade-offs

- Migration uniqueness risk -> `014_student_h5_login.sql` adds a unique active normalized student id index; existing duplicate active roster entries could make migration fail. Mitigate with migration review and local test coverage, and document the preflight check for deployment.
- Student service size risk -> PR services are functional but already large. Mitigate by accepting them now and scheduling later decomposition after behavior is verified.
- Static fallback risk -> Serving two SPAs from one FastAPI app can accidentally intercept API routes. Mitigate by explicitly excluding `/api`, `/admin`, and `/assets` paths from fallback behavior.
- AI cost/availability risk -> Student assistant endpoints may call configured AI services. Mitigate by respecting existing AI feature switches and cached summary/explanation behavior.
- Assessment retake semantics risk -> Completed pretest uniqueness may limit future retakes. Mitigate by preserving PR behavior for acceptance and tracking any future retake requirement separately.

## Migration Plan

1. Integrate student frontend files, backend routers/services/schemas, tests, and migrations from PR #1.
2. Resolve conflicts in favor of current production architecture for `admin_main.py`, `agent.py`, readiness validation, docs, and protected resources.
3. Run backend tests and frontend checks for both admin and student apps.
4. Run OpenSpec validation and production readiness validation.
5. Commit the integration as an acceptance of PR #1 into the productionized branch.

Rollback is a normal git revert of the integration commit. The migrations are additive; database rollback in a deployed environment requires dropping the added student-session tables/indexes only if no production student data has been created.

## Open Questions

- Should completed pretests be strictly one-time per student forever, or should future retakes be supported?
- Should student H5 eventually deploy as a separate static service/CDN instead of FastAPI static files?
- Should student frontend modularization become the next engineering-quality change after this functional acceptance?
