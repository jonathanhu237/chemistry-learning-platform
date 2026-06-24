# admin-shell-architecture Specification

## Purpose
TBD - created by archiving change split-frontend-deployment-admin-shell. Update Purpose after archive.
## Requirements
### Requirement: Teacher app ownership moves under src/app
The teacher console frontend SHALL use `apps/web-teacher/src/app/*` as the canonical app-level owner for providers, theme, auth, routes, navigation, and shell layout.

#### Scenario: Teacher app entrypoint is inspected
- **WHEN** `apps/web-teacher/src/main.tsx` imports the teacher console app
- **THEN** it MUST import the canonical app entrypoint from `apps/web-teacher/src/app`
- **AND** it MUST NOT import `apps/web-teacher/src/App.tsx`.

#### Scenario: Legacy root App owner is checked
- **WHEN** the admin shell refactor is complete
- **THEN** `apps/web-teacher/src/App.tsx` MUST NOT exist as a compatibility wrapper
- **AND** no source file MUST import from the deleted root App path.

### Requirement: Admin routes use frontend root paths
The teacher/admin frontend SHALL remove the `/admin` browser basename and use root-relative routes inside its own frontend service.

#### Scenario: Admin canonical route is opened
- **WHEN** a browser opens `/overview` on the admin frontend service
- **THEN** the admin overview page MUST render without requiring an `/admin` prefix.

#### Scenario: Old backend-hosted admin route is requested
- **WHEN** a browser or test requests `/admin/overview` from the backend service
- **THEN** the backend MUST NOT serve the admin SPA
- **AND** the route MUST NOT be treated as a canonical admin route.

### Requirement: Admin route registry is the single source of route and navigation metadata
The teacher/admin frontend SHALL define canonical admin routes and navigation metadata in one app-level registry.

#### Scenario: Navigation items are rendered
- **WHEN** the admin shell renders navigation
- **THEN** nav item paths, labels, icons, and role visibility MUST be derived from the canonical route registry
- **AND** the shell MUST NOT maintain a second independent nav list that can drift from route registration.

#### Scenario: Lazy page routes are rendered
- **WHEN** the admin route outlet renders top-level pages
- **THEN** lazy page components and fallback behavior MUST be derived from the canonical route registry
- **AND** route-level code splitting MUST be preserved.

### Requirement: Admin auth and shell responsibilities are separated
The teacher/admin frontend SHALL split login, session loading, role guards, shell layout, sidebar, header, and route outlet into explicit app-level owners.

#### Scenario: User session is loaded
- **WHEN** a protected admin route is opened
- **THEN** session loading and role validation MUST be handled by an auth owner
- **AND** feature pages MUST NOT own global auth redirection behavior.

#### Scenario: Admin user logs out
- **WHEN** the admin user logs out from the shell header
- **THEN** token clearing, query cache clearing, and navigation to login MUST be coordinated by shell/auth owners
- **AND** feature pages MUST NOT duplicate logout behavior.

### Requirement: Admin legacy aliases are removed unless canonical
The teacher/admin frontend SHALL remove old route aliases that existed only because the app lived under the backend-hosted `/admin` path.

#### Scenario: Legacy alias is opened
- **WHEN** `/curriculum` or `/review` is opened on the admin frontend service
- **THEN** the app MUST NOT preserve the old alias unless the route registry explicitly lists it as canonical
- **AND** tests MUST reflect the canonical route set.
