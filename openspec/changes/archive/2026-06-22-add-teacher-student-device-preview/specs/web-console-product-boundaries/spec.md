## MODIFIED Requirements

### Requirement: Three web consoles have explicit product boundaries
The platform SHALL expose three independent web consoles named `web-admin`, `web-teacher`, and `web-student`.

#### Scenario: Services use canonical names and ports
- **WHEN** the default local or production-like service topology is inspected
- **THEN** the student frontend service MUST be named `web-student` and expose port `5173`
- **AND** the teacher frontend service MUST be named `web-teacher` and expose port `5174`
- **AND** the platform operations frontend service MUST be named `web-admin` and expose port `5175`.

#### Scenario: Product ownership is unambiguous
- **WHEN** a maintainer inspects frontend packages, Compose services, or documentation
- **THEN** `web-teacher` MUST identify the teacher console that owns experiment, question-bank, AI, settings, class, resource, analytics, feedback, learning-assistant, and student-preview shell workflows
- **AND** `web-admin` MUST identify the platform operations console for teacher-account management and teacher-preview infrastructure governance
- **AND** `web-student` MUST identify the student H5 frontend.

#### Scenario: Preview governance does not duplicate teacher workflows
- **WHEN** `web-admin` manages hidden preview classes or preview test students
- **THEN** it MUST expose only operational governance actions such as list, inspect, reset, disable, restore, or audit
- **AND** it MUST NOT duplicate teacher catalog, class instruction, question-bank, analytics, feedback, learning-assistant, or student learning workflows.
