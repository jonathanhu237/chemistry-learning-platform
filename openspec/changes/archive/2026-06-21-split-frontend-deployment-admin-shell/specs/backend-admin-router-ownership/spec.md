## ADDED Requirements

### Requirement: Backend route ownership excludes frontend SPA fallback
Backend route ownership SHALL be limited to backend-owned API, health, and service routes after the frontend deployment split.

#### Scenario: Admin SPA fallback is removed
- **WHEN** backend routes are registered
- **THEN** `/admin` and `/admin/{full_path:path}` MUST NOT be registered as backend-served SPA routes
- **AND** admin frontend fallback MUST be served by the admin frontend service.

#### Scenario: Student SPA fallback is removed
- **WHEN** backend routes are registered
- **THEN** `/` and `/{full_path:path}` MUST NOT be registered as student SPA fallback routes
- **AND** student frontend fallback MUST be served by the student frontend service.

#### Scenario: Backend static asset mounts are removed
- **WHEN** backend runtime is inspected
- **THEN** it MUST NOT mount admin or student frontend asset directories
- **AND** frontend assets MUST be served by their corresponding frontend services.
