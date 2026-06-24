## MODIFIED Requirements

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
- **AND** `web-student` MUST default to host address `222.200.189.249`
- **AND** `web-student` MUST default to host port `5173`.
