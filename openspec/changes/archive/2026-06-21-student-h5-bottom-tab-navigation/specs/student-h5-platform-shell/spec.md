## ADDED Requirements

### Requirement: Authenticated student bottom tab shell
The student H5 authenticated shell SHALL provide app-level bottom tab navigation after the student has completed login and required onboarding gates.

#### Scenario: Authenticated student enters app shell
- **WHEN** an authenticated student reaches the main H5 app
- **THEN** the app MUST render a bottom navigation bar for app-level destinations
- **AND** the bar MUST include student learning, experiments, assessment, and profile destinations
- **AND** the assistant destination MUST be available only when student assistant feature switches allow it.

#### Scenario: Student switches app tabs
- **WHEN** the student taps a bottom navigation item
- **THEN** the app MUST switch to that destination without logging the student out
- **AND** the app SHOULD preserve nested learning state such as selected chapter or point where practical.

#### Scenario: Onboarding surfaces render outside shell
- **WHEN** the app is showing login, password reset, pretest loading, pretest error, or pretest question surfaces
- **THEN** the bottom tab shell MUST NOT obscure those required onboarding actions
- **AND** those surfaces MAY keep the institutional branding used for entry and authentication.

### Requirement: Authenticated shell uses mobile app headers
The authenticated student H5 shell SHALL use compact mobile app headers instead of the large institutional brand rail on primary app tabs.

#### Scenario: Student views authenticated tab
- **WHEN** the student opens `学习`, `实验`, `问答`, `测评`, or `我的`
- **THEN** the top of the page MUST show compact destination or context information
- **AND** it MUST NOT show the large `中山大学化学学院 / 元素实验` brand rail as the primary first-viewport content.

#### Scenario: Student views login or entry gate
- **WHEN** the student is not yet in the authenticated app shell
- **THEN** the app MAY show institutional branding and the product title
- **AND** that branding MUST NOT force the authenticated shell to use the same large header.
