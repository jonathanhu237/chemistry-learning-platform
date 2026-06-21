## ADDED Requirements

### Requirement: Bottom-tab student app information architecture
The student H5 learning experience SHALL organize authenticated student workflows around bottom app tabs rather than a single learning page with floating global entries.

#### Scenario: Student views bottom-tab destinations
- **WHEN** a student is in the authenticated app shell with all features enabled
- **THEN** the app MUST provide destinations for `学习`, `实验`, `问答`, `测评`, and `我的`
- **AND** each destination MUST represent app-level navigation, not a chapter-local view switch.

#### Scenario: Student opens learning tab
- **WHEN** the student opens `学习`
- **THEN** the app MUST provide the periodic-table chapter entry, current or recommended chapter access, selected chapter facts, selected chapter experiment videos, and point detail navigation
- **AND** chapter-local controls such as `性质通识` and `实验视频` MUST remain inside the learning tab.

#### Scenario: Student opens experiments tab
- **WHEN** the student opens `实验`
- **THEN** the app MUST provide an experiment-resource or point-resource overview using existing student-visible experiment data
- **AND** it MUST avoid showing generic placeholder marketing content.

#### Scenario: Student opens assessment tab
- **WHEN** the student opens `测评`
- **THEN** the app MUST provide student assessment status, post-learning assessment entry when available, and report access where data exists
- **AND** assessment actions MUST remain reachable above the bottom navigation.

#### Scenario: Student opens profile tab
- **WHEN** the student opens `我的`
- **THEN** the app MUST provide student identity, feedback, account, and logout-oriented actions
- **AND** global support actions such as feedback MUST live here instead of as floating page controls.

## MODIFIED Requirements

### Requirement: Student H5 mobile-first WebView contract
The student learning surface SHALL be treated as a phone-first H5 / mini-program WebView experience, not as a desktop admin page or a shrunken desktop layout.

#### Scenario: Student opens H5 on a phone viewport
- **WHEN** the student H5 app is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** primary learning screens MUST fit the viewport without horizontal scrolling
- **AND** headings, cards, segmented chapter switcher, bottom navigation, chat page, profile feedback, and action buttons MUST remain tappable and non-overlapping
- **AND** the layout MUST prioritize the phone flow: app-level tabs, current chapter context, A/B facts-or-experiments switching, experiment-point cards, point detail, chat, feedback, and assessment.

#### Scenario: Student uses touch-only interaction
- **WHEN** a student uses the app without hover, precise mouse input, or desktop keyboard shortcuts
- **THEN** all required learning, A/B switching, chat, feedback, login, password-change, pretest-skip, and logout actions MUST be reachable through touch controls
- **AND** interactive controls SHOULD use phone-appropriate hit areas and spacing.

#### Scenario: Desktop browser is used only for development preview
- **WHEN** a developer opens the student H5 app on a wide desktop browser
- **THEN** the app MAY center or constrain the phone layout for preview
- **BUT** it MUST NOT introduce desktop-only navigation, table-first layouts, hover-only affordances, or admin-console density into the student H5 experience.

### Requirement: Global authenticated H5 feedback
The student H5 app SHALL provide authenticated feedback from the `我的` profile destination when the feedback feature is enabled.

#### Scenario: Student submits feedback from profile
- **WHEN** an authenticated student submits feedback from `我的`
- **THEN** the backend MUST create a feedback record using the authenticated student's identity
- **AND** it MUST capture feedback type, content, page path or screen, optional screenshot attachment, and any available route or learning context metadata
- **AND** the feedback MUST appear in the existing admin feedback management workflow.

#### Scenario: Student reports a page problem
- **WHEN** a student encounters a problem on a learning, experiment, assistant, or assessment page
- **THEN** the app MUST allow the student to report it through `我的` with a written description and optional screenshot
- **AND** the app MUST NOT require a current-page floating feedback widget to submit the report.

#### Scenario: Feedback switch is disabled
- **WHEN** the admin feedback switch is disabled
- **THEN** the H5 app MUST hide or disable the profile feedback entry after configuration refresh
- **AND** the backend MUST reject new student feedback submissions even if a stale client attempts one.

#### Scenario: Client cannot spoof student identity
- **WHEN** a student feedback request includes client-supplied student or class identity in metadata
- **THEN** the backend MUST derive the authoritative student and class identity from the authenticated token
- **AND** it MUST NOT trust client-supplied identity fields.
