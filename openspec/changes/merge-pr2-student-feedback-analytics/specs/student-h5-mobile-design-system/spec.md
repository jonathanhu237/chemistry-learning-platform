## ADDED Requirements

### Requirement: Feedback attachment controls follow mobile overlay governance
The student H5 feedback attachment UI SHALL be implemented inside the existing mobile feedback overlay rather than as a second floating widget.

#### Scenario: Feedback panel includes screenshot controls
- **WHEN** the feedback overlay is open on a phone viewport
- **THEN** the panel MUST provide a touch-friendly screenshot add/change/remove control
- **AND** the selected filename or attachment state MUST fit within the panel without horizontal overflow
- **AND** the submit action MUST remain reachable with the mobile keyboard expected.

#### Scenario: AI and feedback overlays coexist
- **WHEN** the feedback panel is open with or without an attachment
- **THEN** AI chat entry, segmented chapter switcher, finish actions, and point cards MUST follow existing overlay governance
- **AND** no floating feedback widget from an alternate component may overlap the current panel.

#### Scenario: Attachment validation is visible to student
- **WHEN** a student chooses an unsupported screenshot file
- **THEN** the H5 app MUST show a clear mobile-readable validation message
- **AND** it MUST allow the student to choose another file without losing typed feedback content.

### Requirement: Mobile QA covers feedback attachments
Mobile viewport QA SHALL cover the feedback attachment interaction after PR2 integration.

#### Scenario: Feedback attachment QA runs
- **WHEN** mobile QA is run for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST cover opening feedback, selecting or simulating a screenshot attachment, removing an attachment, submitting feedback, and closing the panel
- **AND** it MUST verify that the feedback panel does not block the facts/experiments switcher, point detail back action, or assessment handoff.
