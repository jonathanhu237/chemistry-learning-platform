## MODIFIED Requirements

### Requirement: Mobile home feed preserves horizontal video clarity
The student H5 mobile design system SHALL support horizontal 16:9 video feed cards and compact action rows that remain clear, aligned, and usable on phone viewports.

#### Scenario: Home feed renders on common phone widths
- **WHEN** the home video feed is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** video cards MUST fit the viewport without horizontal scrolling
- **AND** title, catalog path, tags, action row, media controls, and bottom navigation MUST NOT overlap

#### Scenario: Home video action row fits common phone widths
- **WHEN** a home video card action row is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** the left `查看实验` CTA and the right icon group MUST remain on one visual row without wrapping into an incoherent second line
- **AND** the like, favorite or bookmark, share, Atom, and more controls MUST keep stable touch targets and accessible names
- **AND** the Atom control MUST remain visually identifiable as the green highlighted product action without pushing adjacent icons out of view

#### Scenario: Video card loads before playback
- **WHEN** a feed card is not active or video metadata is still loading
- **THEN** the card MUST preserve a stable 16:9 media box
- **AND** poster, loading, fallback states, or action-row icon states MUST NOT shift the surrounding feed layout

#### Scenario: Feed reaches bottom navigation
- **WHEN** the student scrolls near the bottom of the home feed
- **THEN** the final card content MUST remain readable above the app bottom navigation and safe-area inset
- **AND** the bottom navigation MUST not obscure primary feed actions
