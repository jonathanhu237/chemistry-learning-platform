## ADDED Requirements

### Requirement: Mobile overlay headers use veil layers without duplicated backgrounds
The student H5 mobile design system SHALL implement translucent overlay headers by layering a local veil over the real page background instead of duplicating complex page backgrounds inside the header.

#### Scenario: Overlay header needs a soft fade
- **WHEN** a mobile page header needs content behind it to be softened or faded while the foreground title remains readable
- **THEN** the implementation MUST use a separate background veil layer, such as a pseudo-element, behind the header foreground
- **AND** the foreground title, icons, buttons, and hit targets MUST remain fully opaque
- **AND** the design MUST NOT rely on whole-header opacity for this effect.

#### Scenario: Page background contains glows or radial gradients
- **WHEN** the page background contains radial gradients, glow fields, canvas treatments, or other position-sensitive background art
- **THEN** overlay headers MUST NOT duplicate that full background stack inside the header
- **AND** the page-level background MUST remain the single source of truth for position-sensitive art
- **AND** the header veil MUST use a simple translucent tint or linear gradient that does not require pixel-perfect background alignment.

#### Scenario: Veil fallback works without backdrop blur
- **WHEN** a mobile browser or WebView does not support `backdrop-filter` consistently
- **THEN** the header overlay MUST still provide the required fade/readability behavior through the veil's own gradient and opacity stops
- **AND** blur MUST NOT be required for the intended translucency
- **AND** product-specific light chat headers MAY choose an alpha-only veil when sharp underlying content should remain visible through the fade.

#### Scenario: Overlay header respects touch and route scoping
- **WHEN** an overlay header includes interactive controls
- **THEN** those controls MUST keep phone-appropriate hit areas above the veil layer
- **AND** the overlay header selectors MUST be scoped to the intended page or variant so unrelated student pages do not inherit its chrome.

#### Scenario: Overlay header spacing is scoped to scrollable content states
- **WHEN** a mobile page uses an overlay header above content that can be either empty/static or scrollable
- **THEN** header-safe top padding, scroll-padding, or first-content offsets MUST be scoped to the scrollable/content-present state
- **AND** empty or static states MUST NOT inherit scroll-only spacing that creates false scrollbars, pushes centered content downward, or compresses bottom controls
- **AND** the overlay header selector MUST win the cascade over generic foreground-layer selectors that set positioning or stacking.

#### Scenario: Nested mobile scroll surfaces avoid desktop scrollbar chrome
- **WHEN** a mobile chat surface is embedded in a desktop teacher preview or iframe while using an internal scroll container
- **THEN** the internal scroll container SHOULD keep scrolling available without drawing persistent desktop scrollbar chrome over the phone canvas
- **AND** scrollbar hiding MUST be scoped to the intended mobile surface rather than disabling page-level scrolling globally.

### Requirement: Light-theme chat header veils preserve canvas continuity
The student H5 mobile design system SHALL support light-theme chat header veils that preserve a continuous page canvas instead of introducing visible card or strip artifacts.

#### Scenario: Light chat canvas renders behind a header veil
- **WHEN** a light-theme chat canvas uses warm paper, pale yellow-green, or sage-green background tones
- **THEN** the header veil MUST use compatible light translucent stops so the top area reads as the same canvas atmosphere
- **AND** the lower edge of the veil MUST fade out smoothly without creating a visible horizontal strip.

#### Scenario: Protected action groups sit above variable content
- **WHEN** header actions sit above scrollable messages, welcome content, or other variable chat content
- **THEN** those action groups MUST use a compact real-background capsule or equivalent protected surface
- **AND** the protected surface MUST be smaller and more purposeful than a full card-style header
- **AND** it MUST preserve visual alignment with the title row.

#### Scenario: Overlay header is verified on common phone sizes
- **WHEN** mobile viewport QA runs for a page using a translucent chat header veil
- **THEN** QA MUST include 360x780, 390x844, and 430x932 CSS-pixel viewports where practical
- **AND** QA MUST verify that foreground text is readable, action controls are reachable, the veil edge is not a hard strip, and no duplicated-background seam is visible.

### Requirement: Light-theme assistant replies may use flat canvas turns
The student H5 mobile design system SHALL support cardless assistant reply surfaces when the page background itself is the intended reading canvas.

#### Scenario: Assistant reply uses the page canvas as its surface
- **WHEN** a light-theme mobile assistant page intentionally uses a continuous canvas background
- **THEN** successful assistant reply text MAY render directly on that canvas without a card background
- **AND** the page MUST retain enough inline padding, line height, and contrast for long-form reading
- **AND** the cardless treatment MUST NOT depend on duplicating the page background inside the reply block.

#### Scenario: User and assistant authorship remains clear
- **WHEN** a cardless assistant reply appears near a user-authored message
- **THEN** the user-authored message SHOULD remain visually distinct through alignment, color, or bubble treatment
- **AND** the assistant reply SHOULD use typography and action-row placement rather than a card shell to communicate turn boundaries.

#### Scenario: Action rows delimit flat assistant turns
- **WHEN** a cardless assistant reply needs interactive affordances
- **THEN** the reply SHOULD place feedback, copy, more, citation, or similar actions in a lightweight row below the answer body
- **AND** the action row MUST avoid reading as a nested card inside another card
- **AND** the action row MUST preserve phone-appropriate hit areas and accessible names.

#### Scenario: Flat reply surfaces are verified with long content
- **WHEN** mobile viewport QA covers a cardless assistant reply surface
- **THEN** QA MUST include at least one long answer with paragraphs and list items
- **AND** QA MUST check that answer text, action controls, citation affordances, follow-up chips, and bottom composer controls do not overlap or overflow on common phone widths.
