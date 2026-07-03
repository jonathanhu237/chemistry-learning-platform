## Context

The `legacy` branch currently contains both the newer three-console product line and the old competition frontends. The user direction is to make this branch the old product line only: one student frontend and one backoffice frontend. The old frontends are not isolated from the modern backend: they call shared admin, catalog, assessment, analytics, video-library, and student-learning APIs. That means frontend/runtime pruning can be done now, while deep backend module pruning needs a separate API-closure pass.

Current relevant shape:

```text
apps/
  web-student/       newer student product
  web-teacher/       newer teacher/admin product
  web-admin/         newer platform operations product
  web-student-old/   old competition student product
  web-teacher-old/   old competition teacher product

docker-compose.yml      newer full runtime
docker-compose.old.yml  old runtime
```

Target legacy-branch shape:

```text
apps/
  web-student/     old competition student product
  web-backoffice/  old competition backoffice product

docker-compose.yml  old runtime promoted to default
```

## Goals / Non-Goals

**Goals:**
- Make the old student and old teacher products the canonical legacy branch frontends.
- Rename the old teacher product to a backoffice product in package, Compose, and visible shell copy.
- Remove the standalone web-admin token-console frontend from the legacy branch runtime surface.
- Keep the branch buildable and runnable through a two-frontend Compose topology.
- Preserve old frontend API behavior while removing the newer frontend applications.

**Non-Goals:**
- Do not delete backend domains solely because they sound modern; old frontends still depend on many shared backend routes.
- Do not redesign teacher/admin/student authorization in this change beyond removing `platform_admin` from old frontend admission.
- Do not change mainline product semantics outside the legacy branch.
- Do not remove shared seed data, migrations, media storage, or bootstrap scripts needed by old runtime.

## Decisions

1. **Promote old apps by rename instead of keeping `*-old` names.**
   - Decision: `apps/web-student-old` becomes `apps/web-student`, and `apps/web-teacher-old` becomes `apps/web-backoffice`.
   - Rationale: The legacy branch is now the old product line. Keeping `old` and `teacher` names would preserve the wrong product model.
   - Alternative considered: Leave directory names unchanged and only change UI copy. Rejected because service and package names would still communicate the old app as optional.

2. **Remove newer frontends from the legacy branch runtime surface.**
   - Decision: Delete `apps/web-admin`, `apps/web-teacher`, and the current `apps/web-student` before moving old apps into canonical names.
   - Rationale: The branch should have only the two formal entrypoints: student and backoffice.
   - Alternative considered: Keep newer apps but remove them from Compose. Rejected because maintainers would still see unsupported products in the branch.

3. **Promote `docker-compose.old.yml` to the default Compose file.**
   - Decision: Replace the current `docker-compose.yml` with the old-only runtime and remove the separate `docker-compose.old.yml`.
   - Rationale: The default runtime should match the branch purpose.
   - Alternative considered: Keep both Compose files. Rejected because it preserves the new runtime as the default mental model.

4. **Retain backend modules conservatively.**
   - Decision: Keep backend routes/domains required by old API calls. Remove or update only references that directly describe the removed standalone frontend runtime.
   - Rationale: Old student/backoffice call shared `/api/admin/*`, `/api/student/*`, and `/api/auth/*` routes. Deleting backend modules now would risk breaking the runtime.
   - Alternative considered: Delete all non-legacy-named backend modules. Rejected because old is implemented as a compatibility profile over shared backend services.

5. **Treat backoffice role tightening as a follow-up.**
   - Decision: This change may remove `platform_admin` admission from the old backoffice frontend, but full `admin` versus `teacher` feature/data scoping remains a separate authorization change.
   - Rationale: Product/runtime pruning and role redesign have different risks and tests.

## Risks / Trade-offs

- **Risk: Old runtime still imports modern-looking backend modules.** -> Mitigation: Document that backend pruning is deferred and validate through old frontend tests plus backend route tests.
- **Risk: Directory renames break package lockfiles, Docker build args, and README commands.** -> Mitigation: Update package names, Compose build args, and development docs in the same task.
- **Risk: Removing `web-admin` frontend leaves unused `/api/web-admin/*` routes.** -> Mitigation: Leave backend routes for a later closure pass unless tests prove they are dead in the legacy branch.
- **Risk: Visible UI copy remains teacher-oriented after renaming the app.** -> Mitigation: Update shell-level labels and tests for `后台`; keep workflow labels that are genuinely teaching workflows.
- **Risk: Git history loses rename detection if deletes and moves are too broad.** -> Mitigation: Use `git mv` for old app promotion after removing target directories.

## Migration Plan

1. Delete newer frontend app directories from the legacy branch.
2. Rename old frontend directories into canonical names.
3. Update package names, app titles, local storage keys if appropriate, and visible backoffice shell copy.
4. Replace default Compose with the old runtime and update service names, image names, ports, and build args.
5. Update README and operational references for two entrypoints.
6. Run frontend tests/builds for `apps/web-student` and `apps/web-backoffice`.
7. Run focused backend tests covering auth, admin classes/analytics/catalog/question-bank routes, student legacy routes, and route import.

Rollback is normal git rollback of the branch commit. No database migration is required for the runtime rename itself.

## Open Questions

- Whether the backoffice service should keep the old browser port `15177` or move to a canonical non-old port. Default for this change: keep existing old ports to avoid deployment surprise.
- Whether `/api/web-admin/*` should be deleted in the same branch after the frontend removal. Default for this change: defer until after the two-entrypoint runtime is stable.
