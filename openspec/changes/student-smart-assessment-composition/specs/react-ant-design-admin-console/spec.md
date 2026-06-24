## ADDED Requirements

### Requirement: Explainable smart assessment strategy controls
The admin console SHALL provide teacher-facing controls and visual previews for smart assessment composition strategy.

#### Scenario: Admin edits global smart assessment defaults
- **WHEN** an administrator opens system settings
- **THEN** the page MUST provide controls for smart assessment enabled state, total question count, untested point ratio, weak tendency percentage, and maximum questions per experiment
- **AND** the controls MUST use teacher-facing labels rather than internal algorithm names.

#### Scenario: Teacher sees mastery ticket curve
- **WHEN** a user edits or previews smart assessment strategy
- **THEN** the UI MUST show a chart mapping point mastery score to relative draw tickets for measured points
- **AND** it MUST label the chart as relative draw tickets or relative weight rather than final probability.

#### Scenario: Teacher changes weak tendency
- **WHEN** the weak tendency percentage changes
- **THEN** the strategy curve MUST update to show how lower mastery scores receive more tickets
- **AND** a zero weak tendency MUST render an approximately flat measured-point curve.

#### Scenario: Teacher changes untested ratio
- **WHEN** the untested point ratio changes
- **THEN** the UI MUST show untested quota separately from the measured-point mastery curve
- **AND** it MUST NOT display untested points as a fake mastery score on the curve.

#### Scenario: Teacher previews class distribution
- **WHEN** a class strategy preview is available
- **THEN** the UI SHOULD show estimated paper composition for the current class, including untested point quota, measured point distribution grouped by experiment, and any underfilled-pool warnings
- **AND** the preview MUST make clear that final papers depend on question availability and session sampling.

### Requirement: Custom assessment controls
The admin console SHALL provide simple teacher-facing controls for student custom assessment availability and question-count boundaries.

#### Scenario: Admin edits global custom assessment defaults
- **WHEN** an administrator opens system settings
- **THEN** the page MUST provide controls for custom assessment enabled state, default question count, maximum question count, and maximum questions per experiment
- **AND** default and maximum question count controls MUST use fixed values from `5`, `10`, `15`, and `20`.

#### Scenario: Admin configures custom assessment question boundaries
- **WHEN** an administrator saves custom assessment settings
- **THEN** the UI MUST prevent a default question count greater than the maximum question count
- **AND** the student H5 MUST only expose question-count options up to the effective maximum.

#### Scenario: Teacher edits class custom assessment settings
- **WHEN** an authorized teacher or admin opens class settings
- **THEN** the class settings UI MUST show whether custom assessment settings are inherited or overridden
- **AND** it MUST allow authorized users to save or clear class-level custom assessment settings.

#### Scenario: Custom assessment is disabled
- **WHEN** custom assessment is disabled by effective settings
- **THEN** the student H5 assessment center MUST keep smart assessment available if enabled
- **AND** it MUST show custom assessment as unavailable rather than opening the custom selection page.
