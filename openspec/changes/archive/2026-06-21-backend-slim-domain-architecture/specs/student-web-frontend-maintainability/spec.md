## ADDED Requirements

### Requirement: Student frontend is audited but not refactored in backend slim pass
The backend slim architecture change SHALL include a student H5 frontend maintainability audit without performing student frontend module restructuring.

#### Scenario: Student frontend audit is produced
- **WHEN** the backend slim refactor is complete
- **THEN** implementation notes MUST identify oversized student modules, monolithic API areas, route-shell coupling, backend endpoint assumptions, and recommended follow-up changes.

#### Scenario: Student frontend structure is not optimized in this pass
- **WHEN** this backend slim change is implemented
- **THEN** student frontend code MUST NOT be broadly reorganized into new feature/API module architecture as part of this change
- **AND** student frontend edits MUST be limited to endpoint updates, test updates, and minimal fixes required by backend canonical route cleanup.

#### Scenario: Student mobile behavior remains verified
- **WHEN** backend canonical route cleanup affects student H5 API calls or navigation
- **THEN** student frontend typecheck, e2e tests, build, and mobile viewport QA MUST be run or explicitly documented if unavailable.
