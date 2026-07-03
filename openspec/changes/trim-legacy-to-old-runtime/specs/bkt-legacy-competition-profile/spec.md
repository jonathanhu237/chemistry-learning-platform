## MODIFIED Requirements

### Requirement: Legacy competition profile is a separate product profile
The system SHALL provide a legacy competition profile made of a student frontend and a backoffice frontend that share the current backend and core data.

#### Scenario: Legacy profile is inspected
- **WHEN** a maintainer inspects the implemented legacy profile on the legacy branch
- **THEN** it MUST expose a student product identified as `web-student`
- **AND** it MUST expose a backoffice product identified as `web-backoffice`
- **AND** both products MUST use the same backend API and database as the old runtime
- **AND** the profile MUST NOT require a separate legacy database, legacy seed corpus, or legacy backend fork
- **AND** the profile MUST NOT expose the old products as optional `web-student-old` or `web-teacher-old` companions.

#### Scenario: Current products are inspected after legacy profile is added
- **WHEN** a maintainer opens the legacy branch frontend product set
- **THEN** the old SYSU-red competition product behavior MUST be the canonical product behavior
- **AND** the newer green Atom/RAG `web-student`, `web-teacher`, or `web-admin` product behavior MUST NOT remain as active frontend packages in the legacy branch
- **AND** old-profile navigation, old SYSU-red theme, and old forbidden-term gating MUST replace the newer current product runtime in this branch.

### Requirement: Legacy runtime validation uses an old-only compose boundary
The legacy product SHALL provide the default compose entrypoint for the old student, backoffice, and old-scoped backend runtime without starting the unrelated mainline application stack.

#### Scenario: Maintainer starts the legacy runtime
- **WHEN** a maintainer needs to run or validate the old competition profile in containers
- **THEN** they MUST be able to use the default `docker-compose.yml` to start only the old frontend services and the backend surface needed by old
- **AND** the runtime MUST NOT start current `web-teacher`, `web-admin`, Elasticsearch, video worker, or other mainline-only services by default
- **AND** the student frontend service MUST be named `web-student`
- **AND** the backoffice frontend service MUST be named `web-backoffice`
- **AND** the old runtime MAY connect to the shared core database and media storage rather than creating a parallel old database

#### Scenario: Maintainer verifies old backend changes
- **WHEN** old-scoped backend routes, schemas, services, or association tables are changed
- **THEN** validation MUST rebuild or restart the old backend runtime so Python changes are present in the running container
- **AND** validation MUST check backend health and route registration/auth boundaries
- **AND** validation MUST execute the old service or endpoint path against the real database schema, not only mocked sessions
- **AND** validation MUST prove old-only storage such as recommended-learning association tables is isolated from main catalog/media/BKT identities
- **AND** any temporary recommendation toggles or smoke-test rows MUST be removed after validation
- **AND** a real-schema failure such as a missing SQL column MUST block acceptance until fixed
