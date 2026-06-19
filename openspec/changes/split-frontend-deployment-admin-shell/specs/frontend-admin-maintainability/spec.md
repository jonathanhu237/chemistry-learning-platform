## ADDED Requirements

### Requirement: Admin shell refactors are destructive and canonical
Teacher/admin maintainability SHALL prefer canonical app ownership over compatibility wrappers when moving shell responsibilities.

#### Scenario: App shell is moved
- **WHEN** the admin shell is moved into `src/app/*`
- **THEN** the old root `App.tsx` owner MUST be deleted
- **AND** no compatibility re-export MUST be kept solely to preserve the old internal path.

#### Scenario: Admin shell code is reviewed
- **WHEN** reviewers inspect app-level admin code
- **THEN** provider/theme, auth guard/login, route registry, nav model, sidebar/header, and route outlet responsibilities MUST be identifiable by file path
- **AND** feature pages MUST remain separate from global shell ownership.
