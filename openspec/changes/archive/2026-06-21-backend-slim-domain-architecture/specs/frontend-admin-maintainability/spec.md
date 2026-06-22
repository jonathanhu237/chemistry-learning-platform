## ADDED Requirements

### Requirement: Admin frontend is audited but not refactored in backend slim pass
The backend slim architecture change SHALL include a teacher/admin frontend maintainability audit without performing admin frontend module restructuring.

#### Scenario: Admin frontend audit is produced
- **WHEN** the backend slim refactor is complete
- **THEN** implementation notes MUST identify oversized admin feature pages, monolithic API areas, route-shell coupling, backend endpoint assumptions, and recommended follow-up changes.

#### Scenario: Admin frontend structure is not optimized in this pass
- **WHEN** this backend slim change is implemented
- **THEN** admin frontend code MUST NOT be broadly reorganized into new feature/API module architecture as part of this change
- **AND** admin frontend edits MUST be limited to endpoint updates, test updates, and minimal fixes required by backend canonical route cleanup.

#### Scenario: Admin frontend follow-up is actionable
- **WHEN** the audit identifies frontend maintainability problems
- **THEN** the audit MUST group follow-up recommendations by feature owner, expected risk, and verification gate.
