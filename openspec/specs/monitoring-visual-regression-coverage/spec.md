# monitoring-visual-regression-coverage Specification

## Purpose
TBD - created by archiving change restore-ai-monitoring-guardrail-polish. Update Purpose after archive.
## Requirements
### Requirement: Guardrail module visual restoration
The monitoring console SHALL render the `安全护栏` module with a dedicated safety-policy visualization rather than only generic metric cards.

#### Scenario: Teacher opens safety guardrail module
- **WHEN** an authenticated teacher-console user opens the `AI/RAG/ES 监控` route and selects `安全护栏`
- **THEN** the module SHALL show a guardrail-specific defense surface including a radar or shield focal area, policy version, input/judgement/action flow, recent decision metrics, safety coverage layers, and recent outcome distribution
- **AND** the page SHALL continue using the existing monitoring module tab shell.

#### Scenario: Guardrail policy has no recent outcomes
- **WHEN** the safety guardrail module has no recent student AI decision outcomes
- **THEN** the module SHALL show the restored guardrail policy visual structure
- **AND** it SHALL show a controlled empty state for the outcome distribution.

### Requirement: Monitoring visual QA coverage
The monitoring console SHALL include visual QA coverage for modules that were missed by the prior AI/RAG/ES monitoring refactor verification.

#### Scenario: Guardrail visual QA runs
- **WHEN** the guardrail restoration is implemented
- **THEN** verification SHALL inspect or capture the `安全护栏` module at normal desktop width
- **AND** verification SHALL inspect or capture the `安全护栏` module at a narrow laptop width for wrapping, clipping, or overlap.

#### Scenario: Trend visual QA runs
- **WHEN** the guardrail restoration is implemented
- **THEN** verification SHALL inspect or capture the `调用趋势` module at normal desktop width
- **AND** it SHALL confirm the trend tab still uses readable compact monitoring layout.
