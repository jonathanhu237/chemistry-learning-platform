## Purpose

Define the structure, runtime behavior, validation expectations, and publishing readiness for the standalone SYSU chemistry admin-management repository, including its student H5 login shell.

## Requirements

### Requirement: Standalone Platform Repository Structure
The extraction process SHALL produce a separate local repository containing the admin web application, the student H5 login shell, backend runtime, database migrations, and admin bootstrap/import utilities needed to operate the management console.

#### Scenario: Extracted repository excludes student mini-program source
- **WHEN** the standalone repository is generated
- **THEN** it MUST NOT contain `apps/miniprogram`, root `miniprogram`, WXML/WXSS student mini-program pages, or generated student app bundles
- **AND** it MAY contain `apps/student-web` for the browser-based H5 login surface

#### Scenario: Extracted repository retains runtime files
- **WHEN** the standalone repository is generated
- **THEN** it MUST contain `apps/admin-web`, `apps/student-web`, `server`, required backend migration files, selected admin/import scripts, runtime configuration examples, and documentation for local operation

### Requirement: Scoped Backend Entrypoint
The extracted repository SHALL run the backend through a scoped FastAPI entrypoint that serves the admin console, the student H5 login shell, and only the API surfaces required by those experiences by default.

#### Scenario: Server starts without student learning routes
- **WHEN** the extracted backend is imported through its scoped entrypoint
- **THEN** admin routes, authentication routes, and student H5 login/password routes MUST be available while student-facing learning, testing, recommendation, report, mastery, and mini-program routes MUST NOT be mounted by default

#### Scenario: Admin frontend dependencies remain available
- **WHEN** the admin frontend requests shared read data still required by admin screens
- **THEN** the admin-only backend MUST provide compatible endpoints or the frontend MUST be updated to call an admin-scoped equivalent

### Requirement: Delivery Artifact Pruning
The extraction process SHALL exclude bulky or non-admin delivery artifacts that are not required for the admin console to run.

#### Scenario: Generated and raw artifacts are omitted
- **WHEN** the standalone repository is generated
- **THEN** raw curriculum extraction output, intermediate data, generated student app JSON, uploaded media, page image dumps, logs, dependency folders, and build output MUST be omitted unless explicitly required for admin bootstrap

#### Scenario: Required seed data is preserved
- **WHEN** admin bootstrap/import scripts depend on seed data
- **THEN** the required seed files MUST be preserved or the scripts/documentation MUST explain how to regenerate them

### Requirement: Independent Validation
The standalone repository SHALL include enough configuration and scripts to validate that the admin web app and admin backend can build or import independently.

#### Scenario: Frontend validation succeeds
- **WHEN** validation is run in the standalone repository
- **THEN** the admin web app typecheck and production build MUST complete successfully

#### Scenario: Backend validation succeeds
- **WHEN** validation is run in the standalone repository
- **THEN** the scoped FastAPI entrypoint MUST import successfully and OpenSpec validation MUST pass

### Requirement: Local Docker Backend Update Discipline
The standalone repository SHALL treat backend source changes as Docker image changes in the local Compose environment because the backend service does not bind-mount the repository source tree.

#### Scenario: Backend code changes are applied locally
- **WHEN** any file under `server`, backend migration/runtime configuration, or backend-dependent scripts are changed and the local admin console is served through Docker Compose
- **THEN** the backend update MUST be applied with `docker compose up -d --build backend`
- **AND** operators MUST NOT rely on browser refresh, Vite hot reload, or a plain container restart to load backend route, schema, or Python code changes.

#### Scenario: Backend route availability is verified
- **WHEN** a backend change adds, removes, or renames an API route
- **THEN** the route MUST be verified against the running backend after the rebuild, for example through `/openapi.json` or a focused HTTP request to the changed endpoint.

### Requirement: Git Repository Publishing Readiness
The standalone repository SHALL be initialized as a clean local Git repository with an initial commit and documented GitHub publishing instructions.

#### Scenario: Local Git repository is ready
- **WHEN** extraction and validation complete
- **THEN** the standalone repository MUST have its own `.git` directory, tracked files, and an initial commit

#### Scenario: GitHub push uses explicit destination
- **WHEN** a GitHub remote URL is available
- **THEN** the standalone repository MUST add that remote and push the initial commit

#### Scenario: GitHub remote is unavailable
- **WHEN** no GitHub remote URL or authenticated GitHub creation tool is available
- **THEN** the process MUST stop after the local commit and report the exact command needed to add the remote and push
