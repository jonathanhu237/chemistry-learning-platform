## Why

The `legacy` branch is now intended to carry the old competition product line, but the repository still exposes the newer `web-student`, `web-teacher`, and `web-admin` products alongside the old student/teacher frontends. This creates the wrong product shape for the branch and keeps an unnecessary platform-operations token console in a code line that should present only a student endpoint and a single backoffice endpoint.

## What Changes

- **BREAKING** Replace the legacy branch default frontend surface with two canonical products:
  - `web-student`: the former old student competition frontend.
  - `web-backoffice`: the former old teacher competition frontend, renamed and presented as a general backoffice rather than a teacher-only product.
- **BREAKING** Remove the newer `apps/web-admin`, `apps/web-teacher`, and current `apps/web-student` frontend products from the legacy branch runtime surface.
- **BREAKING** Replace the old-specific Compose entrypoint with the default Compose topology for the legacy branch.
- **BREAKING** Remove the standalone web-admin operations frontend and its token-login product concept from the legacy branch user-facing topology.
- Preserve the FastAPI backend, migrations, shared database/media expectations, seed data, and scripts required by the old student and backoffice products.
- Keep backend pruning conservative in this change: remove obvious frontend/runtime ownership drift first, then leave deeper backend module deletion for a later old-API-closure pass.
- Rename visible old teacher-facing UI copy toward `后台` / `后台管理` where it identifies the product shell, while preserving teaching workflow labels such as `实验管理`, `学情分析`, and `评价报告`.

## Capabilities

### New Capabilities
- `legacy-branch-old-runtime`: Defines the legacy branch canonical two-product runtime, package names, Compose topology, and retention boundary for old-only deployment.

### Modified Capabilities
- `bkt-legacy-competition-profile`: Old products are no longer optional `*-old` companions in this branch; they become the canonical student and backoffice products.
- `web-console-product-boundaries`: The legacy branch no longer exposes three current web consoles or a standalone web-admin token console as user-facing products.
- `split-frontend-deployment`: The legacy branch default Compose topology changes from current three-console deployment plus optional old services to the old student/backoffice deployment.

## Impact

- Frontend package directories under `apps/`, including renaming old apps and removing newer current frontend products from this branch.
- Compose files and frontend Docker build arguments.
- README and operational documentation describing local development, ports, and product names.
- Legacy frontend tests and package metadata that currently assert `web-student-old`, `web-teacher-old`, `Teacher Console`, or teacher-only shell names.
- Backend configuration and tests only where they directly reference the removed standalone web-admin runtime surface; deeper backend route/module cleanup is intentionally deferred.
