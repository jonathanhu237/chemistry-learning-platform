## Context

The previous production hardening pass completed the main production-readiness chain: protected resources are manifest-validated, frontend chunks are named and mostly lazy-loaded, FastAPI startup uses lifespan, media cleanup has guarded dry-run behavior, assistant runtime helpers have started moving out of `agent.py`, and validation can be run locally with one command.

The remaining work is not a feature change. It is engineering polish that improves signal quality, repeatability, and long-term maintainability: removing known frontend deprecation noise, turning one-off browser smoke into a maintained e2e script, diagnosing the remaining browser-smoke 404, and continuing the behavior-preserving assistant split.

## Goals / Non-Goals

**Goals:**

- Keep repository state clean, validated, and push-safe.
- Remove known Ant Design deprecation warnings from representative admin pages.
- Make browser smoke reproducible through a committed e2e script.
- Keep e2e validation opt-in locally so normal validation does not require a running browser stack.
- Diagnose or fix the remaining browser-smoke 404 with enough detail that future maintainers can act on it.
- Continue shrinking `server/app/agent.py` without changing response schemas, permissions, RAG semantics, or core evidence behavior.
- Preserve all protected chemistry resources and current database contracts unless a documented `014_...` migration is justified.

**Non-Goals:**

- Do not redesign the admin UI or change page workflows.
- Do not remove `data/media` or rewrite media records.
- Do not make GitHub Actions run automatically on every push.
- Do not alter the current question bank, knowledge framework, experiment points, chunks, embeddings, or evidence bindings.
- Do not require Playwright e2e to run in every local validation by default.

## Decisions

1. Use a committed e2e smoke script instead of ad hoc shell snippets.

   Rationale: the second pass proved browser smoke is useful, but the script lived only in chat/tool history. A committed script gives maintainers a repeatable check and lets CI/local validation opt into it later.

   Alternative considered: add full Playwright Test infrastructure immediately. This is heavier and would require more dependency and browser-install decisions than needed for a first production smoke path.

2. Keep e2e smoke opt-in in `validate_production_readiness.py`.

   Rationale: e2e requires a running backend/frontend and a browser runtime. Making it default would make normal validation brittle and slow. The release gate can opt in explicitly.

   Alternative considered: always run e2e. This would catch more regressions but would make backend-only/resource-only work harder.

3. Fix Ant Design warnings by updating component props at call sites.

   Rationale: warnings currently pollute browser smoke and hide real frontend errors. Prop-level fixes are behavior-preserving and low risk.

   Alternative considered: suppress console warnings in smoke. This would keep the noise and make debugging worse.

4. Continue assistant modularization in thin, tested slices.

   Rationale: `agent.py` is still large enough to slow reviews. Moving stable pure helpers or endpoint facade logic into services reduces risk while preserving endpoint imports and tests.

   Alternative considered: large rewrite of the assistant runtime. This is too risky because assistant behavior depends on RAG fallbacks, evidence shaping, guardrails, and response compatibility.

5. Treat media archive/tombstone as a decision point, not a forced migration.

   Rationale: the current cleanup guardrails work without schema changes. A `014_...` migration should be added only if a real archive/tombstone workflow needs durable database state.

## Risks / Trade-offs

- [Risk] e2e smoke may be environment-sensitive on machines without Chrome or backend/frontend services → Mitigation: make it opt-in, document prerequisites, and fail with actionable messages.
- [Risk] Ant Design API updates can subtly alter layout → Mitigation: run browser smoke after changes and avoid visual redesign.
- [Risk] The observed 404 may depend on local media records → Mitigation: capture the requested URL/method/status in e2e diagnostics.
- [Risk] Further assistant extraction can accidentally change response serialization → Mitigation: add focused characterization tests and keep public endpoint imports stable.
- [Risk] Adding Playwright dependencies can bloat install time → Mitigation: add the minimum dependency only when a committed script requires it, and keep validation opt-in.
