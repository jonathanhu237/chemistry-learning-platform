# `legacy` / `main` 产品统一实施计划

## Phase 0: Activation and safety baseline

- Obtain explicit approval for this PRD/design/implementation plan, then run `task.py start`; do not implement while the task remains `planning`.
- Load project development specs through `trellis-before-dev` before editing application code.
- Confirm `main` matches the intended `origin/main`, resolve the exact `legacy` commit and record merge-base/ahead counts.
- Record current build/test baselines for server, student H5 and teacher console.
- Create a pre-work safety tag on `main`.
- Export the user-owned `artifacts/catalog_outline_seed_validation_report.json` diff to a repository-external file, record its checksum, and exclude it from every stage/commit.
- Save the `git merge-tree` semantic-risk inventory, including both auto-switched frontend entrypoints and non-conflicting deletions, as the merge review checklist.

### Gate 0

- No product code has changed before task activation.
- Safety tag, legacy commit, merge-base and unrelated-file checksum are recorded.
- Current failures, if any, are distinguished from regressions introduced by this task.

## Phase 1: Identity, migration numbering and teacher-account foundation

- Preserve internal roles `admin`, `teacher`, `student`; map user-facing `admin` to “主管教师”.
- Replace/renumber legacy migration intentions above `main` migration `045`; never commit duplicate `041`/`042` files.
- Add the migration that maps any `platform_admin` user to `admin` and preserves the three-role constraint.
- Reduce the current teacher-account domain to list/create/reset/enable/disable only; remove role-edit and delete operations.
- Add supervisor-only teacher-account API ownership under the current teacher API namespace and remove dependence on the platform token.
- Add ordinary-teacher self password UI in the current account menu.
- Enforce `must_change_password` for teacher routes as well as student routes while allowing session inspection, password change and logout.
- Prevent self-disable/reset through peer controls and prevent disabling the last active supervisor.
- Add backend and frontend tests for ordinary/supervisor visibility, create, conflict, reset, disable/enable, first-login gate and session revocation.

### Validation

- Targeted auth/account/migration tests.
- Teacher typecheck and Settings/account tests.
- Route inventory confirms no ordinary teacher can call peer-account mutations.

### Checkpoint

- Commit the verified identity/account slice with a Conventional Commit; do not stage the user artifact.

## Phase 2: Canonical Home feed, focused search and video cleanup

- Add canonical recommendation storage and migrate valid rows from `legacy_recommended_video_points` when present.
- Add recommendation toggle/order to the current teacher catalog point workflow with authorization and validation.
- Extend `/api/student/home-video-feed` with normalized `q`, finite deterministic pagination and query-bound cursors.
- Filter to published paths/content with playable published media; sort explicit recommendations first and label only those items as recommended.
- Update current Home UI with the focused search form, clear/result state and finite load-more behavior while keeping active-viewport muted preview and point navigation.
- Remove phenomenon topic rail, repeated/cycled discovery, overflow/social actions and watch-later UI/API writes.
- Preserve Profile favorites; migrate/narrow saved-video data without deleting favorite rows.
- Remove `/video-library`, obsolete unified search routes and their frontend clients/styles/tests.
- Move shared ES transport/hash/analyzer utilities to a neutral module and update teacher catalog search imports.
- Delete the student video-library ES endpoint, document builder/projection state/jobs, settings, Compose variables, scripts, readiness checks and obsolete tests.
- Verify textbook RAG and teacher catalog search still use their own retained Elasticsearch contracts.

### Validation

- Backend Home feed tests: publication visibility, playable media, token AND matching, recommendation ordering, cursor/query mismatch, finite pagination and empty states.
- Teacher recommendation action tests.
- Student Home tests: search/clear/load-more, one active preview, no removed controls/routes, favorites unaffected.
- Teacher catalog-search tests plus textbook RAG smoke tests.
- Repository search shows no enabled `student-video-library` runtime/config owner.

### Checkpoint

- Commit the verified Home/search/projection cleanup slice.

## Phase 3: Student authentication, baseline and assessment reconciliation

- Remove the active pretest gate, UI/routes/API registration and temporary skip/error copy; retain historical database records without new writes.
- Implement one post-password smart-baseline readiness/create/resume gate and auto-entry behavior.
- Port latest legacy smart-assessment edge cases into current backend owners.
- Replace current experiment/total-count custom setup with the searchable chapter → directory → point scope tree.
- Expand selected scope to published usable leaf points and enforce 1/2/3 questions per point.
- Remove random/all-range entries and stale mode handling.
- Preserve multi-blank answers, submit waiting/failure behavior, mastery/BKT updates, persisted reports and Profile history.
- Run regression checks for five-tab navigation, 3D atom/orbital experience, favorites, current-device AI history wording, preview mode and current textbook RAG assistant.

### Validation

- Backend auth/baseline/smart/custom assessment/report tests.
- Student component/e2e tests for forced password → one baseline → app, returning users, hierarchical selection, invalid scope, multi-blank, submit error and report flow.
- Student typecheck, unit tests, e2e tests, production build and mobile viewport QA.

### Checkpoint

- Commit the verified student auth/assessment slice.

## Phase 4: Teacher workflow reconciliation

- Port published-question withdrawal into the current question workbench while retaining evidence-lineage and duplicate-risk validation.
- Verify withdrawal excludes the question from selection, creates an editable traceable draft, and republish updates the original question ID.
- Keep disable as a separate action and add explicit UI copy/state tests.
- Replace the primary analytics grouping with the confirmed element-family taxonomy; retain current drilldowns, report center, AI summaries and export.
- Audit/port catalog fixes for staged video bindings, visibility and final placement deletion.
- Audit/port roster fixes for password validation, explicit student-ID conflicts and archived-class identity/session disabling.
- Verify current global and per-class assessment configuration covers legacy paper semantics; add regression tests without adding `/paper`.
- Verify current student preview self-provisions/repairs its hidden account/class without operations UI.

### Validation

- Question bank/draft/workbench tests covering withdraw-edit-revalidate-republish and disable distinction.
- Analytics taxonomy, drilldown and export tests.
- Catalog/roster/class and preview regression tests.
- Teacher import-boundary validation, typecheck, unit tests, production build and targeted e2e smoke tests.

### Checkpoint

- Commit the verified teacher workflow slice.

## Phase 5: Remove duplicate runtimes and obsolete operations surface

- Delete `apps/web-student-old`, `apps/web-teacher-old`, `apps/web-admin` and any legacy entry components/assets left inside canonical apps.
- Remove web-admin and old frontend services from Compose, deployment scripts, Nginx/frontend Docker logic and readiness/resource validation.
- Remove `WEB_ADMIN_ACCESS_TOKEN`, platform-admin settings/auth, `/api/web-admin/*` and preview-maintenance APIs.
- Remove migrated `/api/student/legacy/*`, `/api/admin/legacy/*`, duplicate `/api/teacher/*` routers and legacy domains/schemas/tests.
- Remove active pretest/watch-later compatibility code and unused dependencies after consumer searches.
- Update route inventory and architecture allowlists.
- Update README, product model, engineering structure, deployment, operations and testing docs to describe one student H5, one teacher console and one textbook RAG vector path.
- Remove documentation references to OpenSpec, old runtimes, standalone video library and platform operations product when they no longer describe a retained contract.

### Validation

- `rg`/route-inventory checks find no reachable deleted surface or dead advertised setting.
- `docker compose config` exposes only retained services.
- Backend architecture validation and production readiness pass.
- Canonical frontend builds still use current entrypoints, dependencies and visual assets.

### Checkpoint

- Commit the verified runtime/config/docs deletion slice.

## Phase 6: Full reconciliation review and ancestry merge

- Run the full backend suite and migration tests from clean and representative upgraded schemas.
- Run full student and teacher typecheck/tests/build plus available mobile/browser/e2e QA.
- Run backend architecture, seed/bootstrap, Compose and production-readiness validators.
- Compare canonical app trees, entrypoints, route maps and dependency manifests against the pre-work `main` baseline and the approved cut matrices.
- Review `git diff` and staged files to prove the user artifact, secrets, uploaded PDFs and runtime data are absent.
- Perform the final two-parent merge of `legacy` into the already reconciled `main` tree without accepting legacy's destructive automatic frontend result.
- Re-run fast release gates after the merge commit and verify `git merge-base --is-ancestor legacy main`.
- Restore/verify the user artifact modification from its external backup if necessary.
- Push `main` only after all gates pass; report the exact commits and any environment-dependent checks that could not run.

## Required validation commands

Exact test selection may be narrowed during inner loops, but the final gate includes at least:

```bash
python -m pytest server/tests -q
python scripts/validate_backend_architecture.py
python scripts/validate_complete_seed_bootstrap.py
python scripts/validate_compose_stack.py
python scripts/validate_production_readiness.py

cd apps/web-student
npm run typecheck
npm test
npm run build
npm run qa:mobile

cd apps/web-teacher
npm run validate:boundaries
npm run typecheck
npm test
npm run build

git merge-base --is-ancestor legacy main
git diff --check
```

Use the existing environment/mamba setup if the default Python environment lacks project dependencies. Environment-dependent checks must fail explicitly or be reported as skipped; they may not be silently treated as passing.

## Review checklist

- [ ] Exactly five student root tabs remain.
- [ ] Home video feed/search/recommendation behavior matches the approved matrix.
- [ ] No standalone student video index or second vector-management path remains.
- [ ] One baseline and the approved hierarchical assessment setup remain.
- [ ] 3D Atom, RAG assistant, favorites, reports, feedback and preview remain.
- [ ] Current teacher console remains visually and structurally canonical.
- [ ] Supervisor teacher permissions and forced first-password behavior are enforced server-side.
- [ ] Published-question withdrawal and element-family analytics work in current UI.
- [ ] Current paper configuration owners remain; no duplicate `/paper` exists.
- [ ] Old student, old teacher and platform-operations runtimes/routes/config/docs are gone.
- [ ] Textbook upload/MinerU/embedding/rerank/publication/RAG regressions pass.
- [ ] `legacy` is an ancestor of `main`.
- [ ] User-owned artifact changes and secrets are absent from task commits.

## Rollback points

- Before Phase 1: pre-work tag plus repository-external artifact patch.
- After each phase: a tested Conventional Commit that can be reverted independently.
- Before data cleanup: database backup and migration row-count snapshot.
- Before student ES projection deletion: relational Home search and retained teacher/RAG ES checks pass.
- Before final ancestry merge: all product commits pass the full release gate; merge can be aborted without losing them.
