## ADDED Requirements

### Requirement: Sticky segmented chapter switcher
The student frontend SHALL provide a phone-first sticky segmented switcher for local facts/experiments switching inside a selected chapter.

#### Scenario: Switcher appears on chapter page
- **WHEN** the student opens a selected family/chapter learning page
- **THEN** the page MUST render a two-option segmented switcher for facts/common properties and experiment videos
- **AND** the switcher MUST be visually associated with the current chapter rather than the global app navigation

#### Scenario: Switcher remains quickly reachable
- **WHEN** the student scrolls the chapter page on a phone viewport
- **THEN** the segmented switcher MUST remain sticky or quickly reachable according to the page layout
- **AND** it MUST NOT be placed in the bottom navigation area where it would conflict with global navigation, AI, feedback, or finish actions

#### Scenario: Switcher supports touch use
- **WHEN** a student uses touch input on a 360px to 430px CSS-pixel-wide viewport
- **THEN** each segmented option MUST have a phone-appropriate hit area, clear active state, and readable label
- **AND** switching views MUST NOT require hover, keyboard shortcuts, or undiscoverable gestures

#### Scenario: Optional swipe gesture exists
- **WHEN** an implementation supports horizontal swipe between facts and experiments
- **THEN** the visible segmented buttons MUST remain the primary discoverable switching mechanism
- **AND** swipe support MUST NOT interfere with vertical scrolling, point-card taps, video controls, AI, or feedback

### Requirement: Segmented switcher overlay governance
The segmented switcher SHALL coexist with floating entries, safe areas, and bottom actions without visual or interaction overlap.

#### Scenario: Floating entries are visible
- **WHEN** AI chat, feedback, or finish actions are available on the chapter page
- **THEN** the segmented switcher MUST remain usable without being covered by those floating entries
- **AND** floating entries MUST follow the existing overlay governance when panels are opened

#### Scenario: Safe-area and browser chrome are present
- **WHEN** the H5 app runs in a mobile browser or WebView with safe-area insets or browser chrome
- **THEN** the segmented switcher and its sticky offset MUST account for the app's safe-area and header layout
- **AND** it MUST avoid clipped labels, clipped active indicators, and horizontal overflow

#### Scenario: Mobile QA covers A/B switching
- **WHEN** mobile viewport QA runs for this change
- **THEN** it MUST cover facts-to-experiments switching, experiments-to-facts switching, element switching, experiment point list, point detail, AI entry, feedback entry, and assessment handoff
- **AND** it MUST check 360x780, 390x844, and 430x932 CSS-pixel viewports
