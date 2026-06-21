## MODIFIED Requirements

### Requirement: E2E smoke is repeatable
The system SHALL provide committed smoke commands that can log in with local-only accounts and visit representative paths for the teacher console and the platform console.

#### Scenario: Teacher E2E smoke succeeds against a running local stack
- **WHEN** the backend and `web-teacher` frontend are running and a local smoke teacher account can be prepared
- **THEN** the teacher smoke command MUST verify that representative teacher paths including overview, videos, learning assistant, question banks, and analytics load without login redirect or error overlay.

#### Scenario: Platform E2E smoke succeeds against a running local stack
- **WHEN** the backend and `web-admin` frontend are running and a local smoke web-admin token is configured
- **THEN** the platform smoke command MUST verify that the teacher-account workbench loads without login redirect or teacher-module leakage.

## ADDED Requirements

### Requirement: Compose service names are canonical
The production-like Compose topology SHALL use `web-admin`, `web-teacher`, and `web-student` as the canonical frontend service names.

#### Scenario: Compose stack is inspected
- **WHEN** `docker-compose.yml` or compose validation output is inspected
- **THEN** the frontend services MUST be named `web-admin`, `web-teacher`, and `web-student`
- **AND** services named `admin-web` or `student-web` MUST NOT be required by the default application stack.

#### Scenario: Frontend ports are inspected
- **WHEN** Compose frontend port mappings are inspected
- **THEN** `web-admin` MUST default to host port `5175`
- **AND** `web-teacher` MUST default to host port `5174`
- **AND** `web-student` MUST default to host port `5173`.
