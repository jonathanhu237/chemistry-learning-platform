## ADDED Requirements

### Requirement: Mobile home feed preserves horizontal video clarity
The student H5 mobile design system SHALL support horizontal 16:9 video feed cards that remain clear and usable on phone viewports.

#### Scenario: Home feed renders on common phone widths
- **WHEN** the home video feed is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** video cards MUST fit the viewport without horizontal scrolling
- **AND** title, catalog path, tags, actions, media controls, and bottom navigation MUST NOT overlap

#### Scenario: Video card loads before playback
- **WHEN** a feed card is not active or video metadata is still loading
- **THEN** the card MUST preserve a stable 16:9 media box
- **AND** poster, loading, or fallback states MUST NOT shift the surrounding feed layout

#### Scenario: Feed reaches bottom navigation
- **WHEN** the student scrolls near the bottom of the home feed
- **THEN** the final card content MUST remain readable above the app bottom navigation and safe-area inset
- **AND** the bottom navigation MUST not obscure primary feed actions

