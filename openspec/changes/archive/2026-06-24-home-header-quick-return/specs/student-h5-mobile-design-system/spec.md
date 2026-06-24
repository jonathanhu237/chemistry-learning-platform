## ADDED Requirements

### Requirement: Root scroll chrome remains native and performance-safe
The student H5 mobile design system SHALL implement root-page header and navigation quick-return behavior through native page scrolling, passive scroll observation, and thresholded state changes rather than active gesture interception.

#### Scenario: Home feed scroll remains native
- **WHEN** the student scrolls the home video feed on a supported phone browser or WebView
- **THEN** the browser MUST remain the owner of vertical page scrolling
- **AND** header quick-return behavior MUST NOT require active `touchmove` or wheel listeners that call `preventDefault`.

#### Scenario: Header collapse avoids synthetic scroll replay
- **WHEN** home header quick-return behavior is implemented
- **THEN** the implementation MUST NOT use per-gesture synthetic scroll replay, repeated `window.scrollBy` calls, or a title-height progress loop to simulate native scrolling
- **AND** React state updates for the quick-return chrome MUST be thresholded rather than driven by every raw touch delta.

#### Scenario: Unsupported animation APIs do not change behavior
- **WHEN** a mobile browser or WebView does not support CSS Scroll-Driven Animations or similar experimental animation APIs
- **THEN** the home header quick-return behavior MUST still work through the option-2 state-based navigation pattern
- **AND** support for those experimental APIs MUST NOT be required for the home feed to feel scrollable.

#### Scenario: Mobile QA checks root chrome smoothness
- **WHEN** mobile viewport QA runs for this change
- **THEN** QA MUST cover the home root at 360x780, 390x844, and 430x932 CSS-pixel viewports where practical
- **AND** QA MUST verify that downward scroll can compress the home header, upward scroll can restore it, and video feed scrolling remains smooth without visible control overlap.
