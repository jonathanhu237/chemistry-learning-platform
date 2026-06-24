## ADDED Requirements

### Requirement: Unified second-level back arrow geometry
The student H5 mobile design system SHALL provide one shared vector geometry for second-level back arrows instead of allowing each screen to independently choose an icon, copied SVG, or bitmap-derived asset.

#### Scenario: Shared back arrow source is used
- **WHEN** a student H5 second-level back arrow is rendered in React UI or injected into player HTML chrome
- **THEN** the visible glyph MUST come from the shared student mobile back-arrow source
- **AND** ordinary detail headers, unified search back controls, point-video player chrome, and point-video empty states MUST NOT maintain separate hand-copied arrow paths for the same back affordance.

#### Scenario: Arrow is line-drawn SVG
- **WHEN** the shared back arrow glyph is implemented
- **THEN** it MUST be drawn as SVG vector line/path geometry
- **AND** it MUST NOT embed, crop, trace, or reference a bitmap screenshot of the X/Twitter or Bilibili reference arrow.

#### Scenario: Geometry follows measured reference proportions
- **WHEN** the shared arrow is rendered at the standard second-level glyph size
- **THEN** the visible arrow MUST read wider than Lucide's default `ArrowLeft` shape
- **AND** the horizontal tail MUST extend farther right than the previous Lucide-style `x=19` endpoint on a `24x24` viewBox
- **AND** the arrow head MUST be vertically lower than the previous Lucide-style `y=5` to `y=19` span
- **AND** the stroke MUST be visually lighter than the previous `2.4` stroke-width implementation
- **AND** the arrow joint MUST avoid square burrs or protruding artifacts at the left point.

#### Scenario: Touch target remains phone-safe
- **WHEN** the back arrow visual is moved or resized
- **THEN** its tappable control MUST remain phone-appropriate and SHOULD preserve the existing `44px` hit area where practical
- **AND** the implementation MUST NOT shrink the accessible target merely to make the visible glyph closer to the screen edge.

### Requirement: Second-level back arrow placement matches mobile reference spacing
The student H5 mobile design system SHALL position the visible second-level back arrow with reference-like left whitespace rather than the current overly-loose left margin.

#### Scenario: Reference-derived left whitespace is used
- **WHEN** a second-level student page is rendered near the current preview width of `406px`
- **THEN** the first visible arrow pixel MUST use the tuned compact-left standard validated by phone preview
- **AND** ordinary page headers MUST keep a `44px` tappable icon button while using a compact `38px` back column and about `4px` title gap
- **AND** ordinary page-header titles MUST sit about one Chinese character away from the arrow rather than being pushed by the full touch-target width
- **AND** the visual left whitespace MUST be materially smaller than the previous wide-left-padding implementation without overcorrecting to the screen edge.

#### Scenario: Adopted placement constants are preserved
- **WHEN** the current student H5 second-level back standard is implemented
- **THEN** normal `PageBar` back controls MUST use the adopted compact placement equivalent to `margin-left: 12px`, a `38px` back column, a `4px` title gap, and `translateX(-8px)` on the icon button
- **AND** unified search back controls MUST use the same `translateX(-8px)` visual placement standard
- **AND** point-video playable chrome and empty-video back controls MUST use the adopted `10px` left placement standard
- **AND** all of those controls MUST preserve phone-safe hit targets.

#### Scenario: Common phone widths remain aligned
- **WHEN** second-level back arrows are rendered on `360px`, `390px`, or `430px` wide phone viewports
- **THEN** the visible arrow left edge MUST remain in a compact reference-like band rather than drifting back to the previous wide-left-padding look
- **AND** the page MUST avoid horizontal scrolling or clipped titles caused by the placement adjustment.

#### Scenario: Video and non-video arrows feel related
- **WHEN** comparing a normal second-level detail page, a unified search detail-style page, a point-video page with player controls visible, and a point-video empty state
- **THEN** the back arrow glyph geometry MUST be the same
- **AND** the apparent left spacing MUST feel consistent even though the video page places the arrow inside the player frame rather than inside a page header.

### Requirement: Back arrow regression coverage
The student H5 mobile design system SHALL include regression coverage that protects the shared arrow geometry and placement contract.

#### Scenario: Source-level guard prevents drift
- **WHEN** student-web regression tests run
- **THEN** they MUST verify that the shared back-arrow module or equivalent shared source is used by PageBar-style detail headers, unified search, and point-video player back controls
- **AND** they MUST catch reintroduction of independent copied SVG strings or direct Lucide-only `ArrowLeft` geometry for the student second-level back affordance.

#### Scenario: Geometry constants are protected
- **WHEN** the shared back-arrow implementation changes
- **THEN** tests or equivalent checks MUST guard the intended `24x24` viewBox family, lighter stroke, longer tail, and lower-height arrow head
- **AND** placement checks MUST guard against restoring the previous excessive video-player left offset or equivalent wide-left-padding behavior.
