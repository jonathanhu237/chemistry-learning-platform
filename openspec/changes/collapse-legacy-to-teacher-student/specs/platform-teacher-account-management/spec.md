## ADDED Requirements

### Requirement: Teacher accounts are bootstrapped without token operations
The legacy branch SHALL create and update initial teacher accounts through trusted scripts or migrations rather than a token-protected web-admin account workbench.

#### Scenario: Bootstrap creates teacher account
- **WHEN** the bootstrap account script is run for the legacy branch
- **THEN** it MUST create or update an `app_users` account with `role='teacher'`
- **AND** it MUST NOT create `role='admin'` or `role='platform_admin'` accounts.

#### Scenario: Bootstrap updates password
- **WHEN** the bootstrap script resets or initializes a teacher password
- **THEN** it MUST store a hashed password
- **AND** it MUST update password-version or session invalidation state consistently with existing auth rules.

### Requirement: Web-admin teacher account management is retired
The legacy branch SHALL not provide a `web-admin` frontend or `/api/web-admin/teacher-accounts` token API for teacher account management.

#### Scenario: Account management routes are inspected
- **WHEN** the production route table is inspected
- **THEN** `/api/web-admin/teacher-accounts` routes MUST be absent
- **AND** teacher account bootstrap MUST be documented as the supported setup path.

#### Scenario: Environment configuration is inspected
- **WHEN** `.env.example`, Compose files, settings validation, and production docs are inspected
- **THEN** `WEB_ADMIN_ACCESS_TOKEN` MUST NOT be required for the legacy branch.

## REMOVED Requirements

### Requirement: Platform admin manages teacher-console accounts
**Reason**: Token-based platform administration is removed from the legacy branch.
**Migration**: Use bootstrap/script-managed teacher account setup.

### Requirement: Platform admin updates teacher account profile, role, and status
**Reason**: There is no platform admin identity or web-admin token account-management API in the legacy branch.
**Migration**: Account lifecycle beyond initial bootstrap requires a future teacher-account-management change.

### Requirement: Platform admin resets teacher account password
**Reason**: Password initialization and reset are handled by trusted scripts in this version.
**Migration**: Use the bootstrap script or a future explicit account-management feature.

### Requirement: Platform admin soft-deletes teacher account by default
**Reason**: There is no web-admin token endpoint for teacher account deletion in the legacy branch.
**Migration**: Use direct administrative scripts or a future account lifecycle feature if needed.

### Requirement: Web-admin account workbench is focused
**Reason**: The `web-admin` frontend is removed from the legacy branch.
**Migration**: Document script/bootstrap teacher setup instead of a web account workbench.
