## ADDED Requirements

### Requirement: Mobile shell coordinates soft keyboard viewport
The student H5 mobile shell SHALL coordinate focused text entry, bottom navigation chrome, and visible viewport sizing so keyboard-open layouts do not expose stale page space.

#### Scenario: Shell records visible viewport height
- **WHEN** the browser provides `window.visualViewport` during an authenticated student session
- **THEN** the shell MUST expose the current visual viewport height to CSS for keyboard-aware layouts
- **AND** the value MUST update on visual viewport resize or scroll events
- **AND** the shell MUST provide a fallback based on the normal viewport when `window.visualViewport` is unavailable.

#### Scenario: Keyboard-active state is root-scoped
- **WHEN** focus enters a text input or textarea that belongs to a root-level keyboard-aware surface
- **THEN** the shell MAY enter a keyboard-active state for that root route
- **AND** the state MUST be cleared when focus leaves that surface, the route changes, or the visual viewport returns to the normal height
- **AND** the state MUST NOT be globally applied to unrelated root pages unless those pages explicitly opt into keyboard-aware layout.

#### Scenario: Bottom navigation hides during keyboard-active root entry
- **WHEN** a root route is keyboard-active and the bottom navigation would otherwise be visible
- **THEN** the bottom navigation MUST move fully offscreen
- **AND** it MUST disable pointer events while hidden
- **AND** it MUST NOT leave a translucent, clickable, or visually occupied toolbar band above the keyboard.

#### Scenario: Visible viewport replaces bottom-nav reservation
- **WHEN** a keyboard-aware root surface is keyboard-active
- **THEN** the route content height MUST be based on the visible viewport
- **AND** it MUST NOT subtract the bottom navigation height while the bottom navigation is hidden
- **AND** fixed or grid child surfaces MUST remain within the visible viewport without horizontal overflow.

#### Scenario: Keyboard-active empty content remains readable
- **WHEN** a keyboard-aware root surface has an empty-state welcome or prompt while the keyboard-active state is applied
- **THEN** the empty-state content MUST remain within the visible content area above the composer
- **AND** it MUST be allowed to shift upward from its closed-keyboard placement
- **AND** it MUST NOT be implemented as a fixed overlay that covers the composer, messages, or route controls.

#### Scenario: Keyboard-aware layout degrades safely
- **WHEN** visual viewport metrics are unavailable, delayed, or unchanged despite input focus
- **THEN** the app MUST keep the focused input and submit action usable
- **AND** it MUST still hide app bottom navigation for the focused keyboard-aware root surface
- **AND** it MUST recover normal bottom navigation when focus leaves the surface.
