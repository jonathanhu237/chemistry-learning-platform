## ADDED Requirements

### Requirement: Platform admin manages teacher-console accounts
The backend SHALL provide `/api/web-admin/teacher-accounts` endpoints for config-token-only management of teacher-console accounts stored in `app_users`.

#### Scenario: Web-admin token lists teacher accounts
- **WHEN** a request with the configured web-admin token calls `GET /api/web-admin/teacher-accounts`
- **THEN** the response MUST include teacher-console users with role `admin` and compatible legacy role `teacher`
- **AND** each item MUST include id, username, display name, role, status, must-change-password flag, password version, created timestamp, and updated timestamp when available
- **AND** the response MUST NOT include `password_hash`.

#### Scenario: Invalid token lists teacher accounts
- **WHEN** a request without the configured web-admin token calls `GET /api/web-admin/teacher-accounts`
- **THEN** the backend MUST reject the request.

#### Scenario: Web-admin token creates teacher account
- **WHEN** a request with the configured web-admin token submits username, display name, and initial password to `POST /api/web-admin/teacher-accounts`
- **THEN** the backend MUST create an active `app_users` row with `role='admin'`, a hashed password, `must_change_password=true` unless explicitly overridden, and `password_version=1`
- **AND** the response MUST NOT include `password_hash`.

#### Scenario: Duplicate username is created
- **WHEN** the requested username already exists
- **THEN** the backend MUST return a conflict error
- **AND** it MUST NOT overwrite the existing user.

### Requirement: Platform admin updates teacher account profile, role, and status
The backend SHALL allow web-admin token requests to update display name, managed teacher-console role, and status for teacher-console accounts.

#### Scenario: Web-admin token patches account
- **WHEN** a request with the configured web-admin token calls `PATCH /api/web-admin/teacher-accounts/{account_id}` with display name, role, or status
- **THEN** the backend MUST update only the provided editable fields
- **AND** allowed roles MUST be constrained to admin and teacher
- **AND** allowed statuses MUST be constrained to active and disabled.

#### Scenario: Web-admin token migrates legacy teacher account
- **WHEN** a request with the configured web-admin token patches a legacy teacher-console account from role `teacher` to role `admin`
- **THEN** the backend MUST update the `app_users.role` value
- **AND** it MUST revoke active sessions for that account so future requests use a fresh token with the updated role.

#### Scenario: Web-admin token targets non-teacher account
- **WHEN** a web-admin token request attempts to patch a student or platform-only account through the teacher-account endpoint
- **THEN** the backend MUST reject the operation as not found or not manageable by this endpoint.

### Requirement: Platform admin resets teacher account password
The backend SHALL allow web-admin token requests to reset teacher-console account passwords while invalidating existing tokens.

#### Scenario: Password is reset
- **WHEN** a request with the configured web-admin token calls `POST /api/web-admin/teacher-accounts/{account_id}/reset-password`
- **THEN** the backend MUST replace the stored password hash
- **AND** it MUST increment `password_version` by 1
- **AND** it MUST set `must_change_password` according to the request or the endpoint default
- **AND** the response MUST NOT include `password_hash`.

#### Scenario: Reset target is unmanaged
- **WHEN** a web-admin token request attempts to reset a student or platform-only account through the teacher-account endpoint
- **THEN** the backend MUST reject the operation as not found or not manageable by this endpoint.

### Requirement: Platform admin soft-deletes teacher account by default
The backend SHALL make teacher-account deletion a soft delete by default.

#### Scenario: Web-admin token deletes teacher account
- **WHEN** a request with the configured web-admin token calls `DELETE /api/web-admin/teacher-accounts/{account_id}`
- **THEN** the backend MUST set the account status to `disabled`
- **AND** it MUST NOT physically remove the `app_users` row by default
- **AND** the response MUST identify the disabled account without returning `password_hash`.

### Requirement: Web-admin account workbench is focused
The `web-admin` frontend SHALL provide a desktop Ant Design workbench for teacher-console account management only.

#### Scenario: Web-admin token opens workbench
- **WHEN** an operator opens `web-admin` with the configured access token
- **THEN** the page MUST show teacher-account list, create, edit display name/status, reset password, and disable/delete controls
- **AND** it MUST use the existing green Ant Design visual language.

#### Scenario: Platform admin navigates web-admin
- **WHEN** the `web-admin` frontend renders navigation or page content
- **THEN** it MUST NOT expose experiment, question-bank, AI access, learning assistant, system settings, classes, student learning, media, analytics, or feedback modules.
