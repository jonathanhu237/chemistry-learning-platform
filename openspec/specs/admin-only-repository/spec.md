## Purpose

Define the structure, runtime behavior, validation expectations, and publishing readiness for the standalone SYSU chemistry admin-management repository.

## Requirements

### Requirement: Standalone Admin Repository Structure
The extraction process SHALL produce a separate local repository containing the admin web application, admin backend runtime, database migrations, and admin bootstrap/import utilities needed to operate the management console.

#### Scenario: Extracted repository excludes student mini-program source
- **WHEN** the standalone repository is generated
- **THEN** it MUST NOT contain `apps/miniprogram`, root `miniprogram`, WXML/WXSS student mini-program pages, or generated student app bundles

#### Scenario: Extracted repository retains admin runtime files
- **WHEN** the standalone repository is generated
- **THEN** it MUST contain `apps/admin-web`, `server`, required backend migration files, selected admin/import scripts, runtime configuration examples, and documentation for local operation

### Requirement: Admin-Only Backend Entrypoint
The extracted repository SHALL run the backend through an admin-only FastAPI entrypoint that serves the admin console and mounts only admin-required API surfaces by default.

#### Scenario: Admin server starts without student routes
- **WHEN** the extracted backend is imported through its admin-only entrypoint
- **THEN** admin routes and authentication routes MUST be available while student-facing learning, testing, recommendation, report, mastery, and mini-program routes MUST NOT be mounted by default

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
- **THEN** the admin-only FastAPI entrypoint MUST import successfully and OpenSpec validation MUST pass

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
