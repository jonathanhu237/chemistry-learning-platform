## ADDED Requirements

### Requirement: Legacy branch exposes two canonical frontend products
The legacy branch SHALL expose exactly two canonical browser-facing frontend products: `web-student` for students and `web-backoffice` for backoffice users.

#### Scenario: Frontend packages are inspected
- **WHEN** a maintainer inspects the `apps/` directory on the legacy branch
- **THEN** the old student competition frontend MUST be available at `apps/web-student`
- **AND** the old teacher competition frontend MUST be available at `apps/web-backoffice`
- **AND** the branch MUST NOT include active frontend packages named `apps/web-student-old`, `apps/web-teacher-old`, `apps/web-admin`, or `apps/web-teacher`.

#### Scenario: Product names are displayed
- **WHEN** the backoffice product shell, login screen, document title, package metadata, or Compose service name is inspected
- **THEN** it MUST identify the product as a backoffice or management backend surface
- **AND** it MUST NOT identify the product shell as a teacher-only console or `web-teacher-old`.

### Requirement: Legacy branch default runtime starts old products only
The legacy branch default Compose runtime SHALL start the old student product, old backoffice product, and required backend service without starting removed current frontend products.

#### Scenario: Default Compose topology is inspected
- **WHEN** `docker-compose.yml` is inspected on the legacy branch
- **THEN** it MUST define frontend services named `web-student` and `web-backoffice`
- **AND** `web-student` MUST build from `apps/web-student`
- **AND** `web-backoffice` MUST build from `apps/web-backoffice`
- **AND** it MUST NOT define frontend services named `web-student-old`, `web-teacher-old`, `web-teacher`, or `web-admin`.

#### Scenario: Legacy frontend API proxy is inspected
- **WHEN** the default legacy frontend services are inspected
- **THEN** both `web-student` and `web-backoffice` MUST proxy browser-facing `/api/*` traffic to the backend service
- **AND** backend API paths used by the former old products MUST remain browser-facing `/api/*` paths.

### Requirement: Backend pruning follows old API closure
The legacy branch SHALL keep backend code required by the old student and backoffice frontend API closure until a separate backend-pruning change proves those routes are unused.

#### Scenario: Runtime pruning is implemented
- **WHEN** the legacy branch frontend/runtime pruning change is applied
- **THEN** shared backend routes used by old frontends MUST remain registered
- **AND** shared migrations, seed data, media storage support, and bootstrap scripts required by old runtime MUST remain available
- **AND** backend domains MUST NOT be deleted solely because their names are associated with the newer product line.

#### Scenario: Future backend deletion is proposed
- **WHEN** a later change deletes backend routes, domains, scripts, or seed files
- **THEN** that change MUST prove the deleted files are outside the old student/backoffice API closure
- **AND** it MUST include validation that the two canonical legacy frontend products still build and load their core API-backed flows.
