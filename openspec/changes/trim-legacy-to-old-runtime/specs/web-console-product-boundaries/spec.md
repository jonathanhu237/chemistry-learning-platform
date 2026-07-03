## MODIFIED Requirements

### Requirement: Three web consoles have explicit product boundaries
The legacy branch SHALL not expose three current web consoles; it SHALL expose one student endpoint and one backoffice endpoint for the old competition runtime.

#### Scenario: Services use canonical names and ports
- **WHEN** the default local or production-like service topology is inspected on the legacy branch
- **THEN** the student frontend service MUST be named `web-student`
- **AND** the backoffice frontend service MUST be named `web-backoffice`
- **AND** no standalone platform operations frontend service named `web-admin` MUST be present
- **AND** no current teacher frontend service named `web-teacher` MUST be present.

#### Scenario: Product ownership is unambiguous
- **WHEN** a maintainer inspects frontend packages, Compose services, or documentation on the legacy branch
- **THEN** `web-student` MUST identify the old student experiment-learning frontend
- **AND** `web-backoffice` MUST identify the old BKT teaching-management and administration backend frontend
- **AND** platform operations features MUST NOT be exposed through a standalone token-login frontend product.

#### Scenario: Preview governance does not duplicate teacher workflows
- **WHEN** the legacy branch runtime is inspected
- **THEN** standalone web-admin preview infrastructure governance MUST NOT be a user-facing frontend product
- **AND** any remaining backend preview-governance route MUST be treated as retained backend compatibility until a later backend-pruning change removes it.

### Requirement: Console access boundaries are separated
The backend and frontend guards SHALL enforce access boundaries for the two canonical legacy branch products.

#### Scenario: Configured token opens web-admin
- **WHEN** a user attempts to open a standalone `web-admin` product on the legacy branch
- **THEN** no such frontend product MUST be available
- **AND** user-facing backoffice access MUST use username/password authentication rather than a configured web-admin token.

#### Scenario: Missing or invalid token opens web-admin
- **WHEN** a user lacks a configured web-admin token
- **THEN** that missing token MUST NOT block access to the canonical `web-student` or `web-backoffice` products
- **AND** old runtime startup MUST NOT depend on a standalone web-admin frontend login flow.

#### Scenario: Teacher-console user opens web-teacher
- **WHEN** an active authenticated user with `role='admin'` or legacy `role='teacher'` opens the legacy branch backoffice
- **THEN** the backoffice MUST allow access according to its legacy branch backoffice guard.

#### Scenario: Platform or student user opens web-teacher
- **WHEN** an authenticated user with `role='student'` opens the legacy branch backoffice
- **THEN** the backoffice MUST reject the session
- **AND** `role='platform_admin'` MUST NOT be required or treated as a canonical legacy branch backoffice role.

### Requirement: Legacy products have explicit product boundaries
The legacy branch SHALL treat the former old student and old teacher products as the canonical student and backoffice products for the branch.

#### Scenario: Product ownership is inspected
- **WHEN** a maintainer inspects frontend packages, Compose services, route documentation, or product docs on the legacy branch
- **THEN** `web-student` MUST identify the legacy student experiment-learning frontend
- **AND** `web-backoffice` MUST identify the legacy BKT teaching-management backend frontend
- **AND** neither product MUST be documented as an optional companion to a newer current product in this branch.

#### Scenario: User opens current and old products
- **WHEN** the same backend account and data are used on the legacy branch
- **THEN** the old products MUST present their legacy navigation and capability subset
- **AND** newer current-product routes and navigation MUST NOT remain active frontend products on the branch
- **AND** route availability in old student MUST NOT imply the same route is visible in old backoffice.

### Requirement: Legacy boundary hides platform and diagnostic ownership
The legacy backoffice product SHALL avoid standalone platform operations and diagnostic monitoring workflows that belong to removed current products.

#### Scenario: Legacy teacher navigation is rendered
- **WHEN** an authenticated backoffice user opens `web-backoffice`
- **THEN** navigation MUST focus on experiment navigation, AI question generation, review, assessment reports, classes, and learning scores
- **AND** navigation MUST NOT include standalone platform-account governance, student-preview infrastructure governance, learning assistant, intelligent monitoring, AI/RAG/ES diagnostics, provider credential management, or web-admin token-console workflows
- **AND** the shell MUST identify itself as a backoffice or management backend rather than a teacher-only console.
