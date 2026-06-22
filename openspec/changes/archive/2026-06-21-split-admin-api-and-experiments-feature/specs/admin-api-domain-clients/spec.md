## ADDED Requirements

### Requirement: Admin API HTTP primitives are shared but domain-neutral
The admin frontend SHALL keep transport behavior in a domain-neutral API HTTP module.

#### Scenario: HTTP module is inspected
- **WHEN** reviewers inspect `apps/admin-web/src/api/http.ts`
- **THEN** it MUST own shared request helpers such as `api`, `postJson`, `patchJson`, `putJson`, and `postJsonStream`
- **AND** it MUST NOT export feature-specific response schemas such as experiments, media, question bank, analytics, feedback, or learning assistant types.

#### Scenario: Authenticated API request receives unauthorized response
- **WHEN** an admin API request receives HTTP 401
- **THEN** the shared HTTP behavior MUST clear the admin auth token using the existing token semantics
- **AND** downstream callers MUST continue to receive an error compatible with existing error handling.

### Requirement: Admin auth API ownership is explicit
The admin frontend SHALL place auth/session types and token storage helpers in a dedicated auth API module.

#### Scenario: Admin shell loads the current user
- **WHEN** `RequireAdmin` or session-loading code imports auth helpers
- **THEN** it MUST import user/session/token helpers from the canonical auth API module
- **AND** it MUST NOT import from a catch-all `api/index.ts` barrel.

#### Scenario: Login succeeds
- **WHEN** the login page receives an access token
- **THEN** the token MUST be stored under the same browser storage key used before this refactor
- **AND** the successful login redirect behavior MUST remain compatible with the existing admin shell.

### Requirement: Admin domain clients own endpoint paths and schemas
The admin frontend SHALL define endpoint paths, request types, and response types in domain-owned API modules.

#### Scenario: Experiments domain client is inspected
- **WHEN** reviewers inspect the experiments API module
- **THEN** experiment catalog, experiment video point, point learning content, related link, and publication request/response types MUST be owned there
- **AND** experiment endpoint paths MUST NOT be embedded only inside React page components.

#### Scenario: Media domain client is inspected
- **WHEN** reviewers inspect the media API module
- **THEN** media asset, processing job, duplicate candidate, upload completion, and preview URL helpers MUST be owned there or in a media-owned helper
- **AND** unrelated domains MUST NOT import media-specific schemas from a global type barrel.

#### Scenario: Question bank domain client is inspected
- **WHEN** reviewers inspect the question bank API module
- **THEN** question bank, question, draft, point-aware suggestion, and workbench types/functions MUST be owned there
- **AND** streaming question-workbench helpers MUST use the shared HTTP stream primitive rather than duplicating stream parsing.

### Requirement: Catch-all admin API barrel is removed
The admin frontend SHALL stop using `apps/admin-web/src/api/index.ts` as a catch-all domain type and helper barrel.

#### Scenario: Source imports are searched
- **WHEN** source files under `apps/admin-web/src` are searched after the migration
- **THEN** no source file MUST import from `../api`, `../../api`, or another directory import that resolves to `apps/admin-web/src/api/index.ts`
- **AND** imports MUST reference explicit modules such as `api/http`, `api/auth`, `api/experiments`, or `api/media`.

#### Scenario: Legacy API barrel is checked
- **WHEN** the API split is complete
- **THEN** `apps/admin-web/src/api/index.ts` MUST NOT remain as a compatibility re-export for old imports
- **AND** any retained API index file MUST be unused by admin source and MUST NOT export domain schemas.

### Requirement: Non-API utilities leave the API layer
The admin frontend SHALL keep UI or formatting helpers out of domain API modules unless they are part of request construction.

#### Scenario: Formatting helper is inspected
- **WHEN** reviewers look for byte-size formatting such as `formatBytes`
- **THEN** it MUST be owned by a UI-neutral library or feature helper outside the API transport/domain layer
- **AND** domain clients MUST remain focused on HTTP calls, request construction, and typed response models.

### Requirement: API split preserves visible admin behavior
The admin API split SHALL preserve existing frontend workflows while changing import ownership.

#### Scenario: Admin validation runs
- **WHEN** admin typecheck, tests, build, and e2e smoke run after the API split
- **THEN** existing admin routes MUST compile and render without missing imports, changed endpoint paths, or changed auth behavior
- **AND** large route chunks MUST remain behind their existing lazy route boundaries.
