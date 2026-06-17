## 1. PR Intake

- [x] 1.1 Fetch PR #1 head and compare it against the current productionized branch.
- [x] 1.2 Merge or port PR #1 changes into the current branch without committing until conflicts are resolved.
- [x] 1.3 Preserve protected core resource files and `data/seed/manifests/core_resources.json` unless resource validation proves an intentional change.

## 2. Backend Integration

- [x] 2.1 Integrate student auth request models, login, password change, and student identity context.
- [x] 2.2 Add student pretest, learning, posttest, and assistant routers to the FastAPI app.
- [x] 2.3 Add student service and schema modules from the PR.
- [x] 2.4 Add student H5 migrations for login and assessment sessions.
- [x] 2.5 Resolve `admin_main.py` by keeping lifespan startup and adding student static serving/fallback.
- [x] 2.6 Resolve `agent.py` by keeping AI policy classification in `services/agent_policy.py`.

## 3. Frontend Integration

- [x] 3.1 Add the `apps/student-web` Vite/React app and package metadata.
- [x] 3.2 Ensure the student frontend can typecheck and build independently.
- [x] 3.3 Keep admin frontend API/storage changes only when compatible with the current admin app.

## 4. Readiness And Documentation

- [x] 4.1 Extend `scripts/validate_production_readiness.py` to validate admin and student frontends without removing existing admin checks.
- [x] 4.2 Update production operations documentation for the student H5 validation path.
- [x] 4.3 Keep GitHub Actions trigger behavior manual-only.

## 5. Verification

- [x] 5.1 Run OpenSpec validation for `integrate-student-h5-platform`.
- [x] 5.2 Run protected production resource validation.
- [x] 5.3 Run backend pytest.
- [x] 5.4 Run admin frontend typecheck, tests, build, and build report.
- [x] 5.5 Run student frontend typecheck and build.
- [x] 5.6 Run production readiness validation for the integrated platform.

## 6. Completion

- [x] 6.1 Review git diff for accidental architecture rollback or protected-resource drift.
- [x] 6.2 Commit the accepted PR integration with OpenSpec artifacts.
