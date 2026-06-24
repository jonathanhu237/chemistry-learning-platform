# student-h5-engineering-structure Specification

## Purpose
Define student H5 frontend ownership boundaries for route modules, feature modules, shared mobile utilities, API helpers, styles, and validation gates.
## Requirements
### Requirement: Student H5 route semantics are centralized
The student H5 frontend SHALL define root tabs and reusable second-level pages through a centralized route and navigation owner.

#### Scenario: Root tabs open detail experiences
- **WHEN** a user opens chapter study, element detail, point video detail, video library, AI chat, assessment session/report, or feedback from any root tab
- **THEN** the destination MUST be treated as a reusable second-level page by navigation semantics
- **AND** the implementation MUST NOT treat apparent URL depth as the page hierarchy source of truth.

#### Scenario: A component navigates to a student detail page
- **WHEN** a route, feature, card, search result, or related link navigates to a student detail page
- **THEN** it MUST use `app/router/navigation.ts` or an equivalent typed navigation owner
- **AND** it MUST preserve source context through the route search contract when source context affects back behavior or page framing.

#### Scenario: A new student route is added
- **WHEN** a new student route is added
- **THEN** it MUST be registered in the centralized router
- **AND** it MUST declare whether it is a root tab page, reusable second-level page, or nested implementation route.

### Requirement: Student H5 modules use route, feature, shared, and mobile ownership
The student H5 frontend SHALL separate route orchestration, feature UI, shared utilities, mobile primitives, and styles.

#### Scenario: A route page grows feature behavior
- **WHEN** a route page starts owning domain display logic, formatting, fetch orchestration, or reusable panels
- **THEN** that logic MUST move to the relevant `features/*` owner
- **AND** the route page SHOULD remain a thin composition boundary.

#### Scenario: Shared code is introduced
- **WHEN** reusable code is used by more than one feature or route
- **THEN** it MAY live under `shared/*` only if it does not import route or feature owners
- **AND** it MUST keep its dependency direction toward primitives and utilities.

#### Scenario: Mobile primitives are introduced
- **WHEN** a component defines generic H5/mobile layout, viewport, token, or touch behavior
- **THEN** it SHOULD live under `mobile/*` or a shared mobile owner
- **AND** feature-specific visual behavior MUST stay with the feature.

### Requirement: Student H5 API and style ownership prevents monoliths
The student H5 frontend SHALL avoid a single API file or global style layer becoming the main application owner.

#### Scenario: A new student endpoint is consumed
- **WHEN** a new backend student endpoint is consumed
- **THEN** the frontend MUST prefer a domain-specific client/schema module over expanding a monolithic `api.ts`
- **AND** shared HTTP primitives may remain centralized.

#### Scenario: Feature styling is added
- **WHEN** a feature adds styling
- **THEN** the style owner MUST be explicit
- **AND** global styles MUST be reserved for app shell, base tokens, or deliberate cross-feature primitives.

### Requirement: Student H5 structure changes keep mobile QA
Student H5 structural changes SHALL keep mobile route-stack and viewport validation as a release gate.

#### Scenario: Route stack, shell, or major page layout changes
- **WHEN** a change touches route registration, navigation helpers, authenticated shell, bottom tabs, or reusable detail pages
- **THEN** the student H5 mobile QA command MUST run
- **AND** it MUST cover the supported mobile viewport set.
