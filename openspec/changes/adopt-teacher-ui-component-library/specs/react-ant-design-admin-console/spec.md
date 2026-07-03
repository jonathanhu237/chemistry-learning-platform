## MODIFIED Requirements

### Requirement: React Ant Design admin shell

The teacher console SHALL be implemented as a React + TypeScript desktop web application named `web-teacher` using Ant Design or the selected Ant Design-compatible component-library foundation for standard shell and management UI primitives.

#### Scenario: Authenticated teacher-console user opens web-teacher

- **GIVEN** an active teacher-console user with `role='teacher'` is authenticated
- **WHEN** they open the teacher console
- **THEN** the system SHALL render a React application shell with component-library-backed layout primitives, top account controls, route-based content, and a left navigation menu
- **AND** the shell SHALL load route data through typed API clients rather than direct DOM mutation.

#### Scenario: Unauthenticated user opens teacher console

- **GIVEN** a user is not authenticated or their session has expired
- **WHEN** they open a teacher-console route
- **THEN** the system SHALL render the teacher-console login screen
- **AND** successful login SHALL return the user to an authenticated teacher-console shell.

#### Scenario: Non-teacher-console role opens teacher console

- **GIVEN** a student user is authenticated
- **WHEN** they open a teacher-console route
- **THEN** the system SHALL reject the session for the teacher console.

### Requirement: Visual consistency with mini-program brand

The teacher console SHALL use Ant Design or the selected Ant Design-compatible component-library primitives while preserving the current legacy teacher-console brand instead of adopting a generic component-library theme.

#### Scenario: Teacher UI renders standard pages

- **GIVEN** the teacher UI has loaded
- **WHEN** list, form, dashboard, modal, dropdown, tab, and management pages are rendered
- **THEN** they SHALL use the current SYSU red visual language, warm page background, low-radius rectangular controls, compact desktop density, and readable management-table/list spacing
- **AND** they SHALL avoid the component library's default blue/white visual identity.

#### Scenario: Component-library theme tokens are inspected

- **WHEN** a maintainer inspects the teacher component-library provider or theme configuration
- **THEN** primary, background, border, text, radius, and spacing tokens SHALL map to the legacy teacher-console style tokens or documented equivalents
- **AND** feature pages SHALL NOT each define unrelated primary colors, card radii, or control densities.

#### Scenario: Migrated teacher pages are reviewed

- **WHEN** login, shell navigation, experiment management, LLM question generation, analytics, and report pages are visually checked after migration
- **THEN** brand assets, sidebar structure, page hierarchy, and teacher workflow density SHALL remain recognizable from the pre-migration console
- **AND** text and controls SHALL fit without overlap on supported desktop widths.
