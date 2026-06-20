## ADDED Requirements

### Requirement: Explainable smart assessment strategy controls
The admin console SHALL provide teacher-facing controls and visual previews for smart assessment composition strategy.

#### Scenario: Admin edits global smart assessment defaults
- **WHEN** an administrator opens system settings
- **THEN** the page MUST provide controls for smart assessment enabled state, total question count, untested experiment ratio, weak tendency percentage, and maximum questions per experiment
- **AND** the controls MUST use teacher-facing labels rather than internal algorithm names.

#### Scenario: Teacher sees mastery ticket curve
- **WHEN** a user edits or previews smart assessment strategy
- **THEN** the UI MUST show a chart mapping mastery score to relative draw tickets for measured experiments
- **AND** it MUST label the chart as relative draw tickets or relative weight rather than final probability.

#### Scenario: Teacher changes weak tendency
- **WHEN** the weak tendency percentage changes
- **THEN** the strategy curve MUST update to show how lower mastery scores receive more tickets
- **AND** a zero weak tendency MUST render an approximately flat measured-experiment curve.

#### Scenario: Teacher changes untested ratio
- **WHEN** the untested experiment ratio changes
- **THEN** the UI MUST show untested quota separately from the measured-experiment mastery curve
- **AND** it MUST NOT display untested experiments as a fake mastery score on the curve.

#### Scenario: Teacher previews class distribution
- **WHEN** a class strategy preview is available
- **THEN** the UI SHOULD show estimated paper composition for the current class, including untested quota, measured experiment distribution, and any underfilled-pool warnings
- **AND** the preview MUST make clear that final papers depend on question availability and session sampling.
