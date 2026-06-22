## ADDED Requirements

### Requirement: Catalog tree drag behavior remains feature-local and verified
The admin frontend SHALL implement modern catalog tree drag behavior through feature-owned modules, focused pure helpers, and real interaction verification rather than broad shell changes or superficial visual checks.

#### Scenario: Developer changes catalog drag behavior
- **WHEN** a developer updates drag preview, drop cursor, hover expansion, optimistic movement, rollback, or move reconciliation
- **THEN** the implementation MUST remain localized to catalog tree feature modules and existing catalog domain API clients
- **AND** it MUST NOT require editing unrelated admin shell, routing, or monolithic application modules.

#### Scenario: Developer adds optimistic movement logic
- **WHEN** optimistic tree movement, source/target branch detection, stale-branch marking, or rollback logic is introduced
- **THEN** the pure transformation behavior MUST be covered by focused tests
- **AND** tests MUST cover same-parent reorder, cross-parent move, root move, unloaded target parent, invalid point target, invalid descendant target, success reconciliation, and failure rollback.

#### Scenario: Developer verifies real drag interactions
- **WHEN** the modern tree movement change is implemented
- **THEN** browser or equivalent interaction QA MUST exercise real pointer drag behavior on the catalog tree
- **AND** QA MUST verify drag preview, source dragging state, before/after insertion feedback, directory drop-target feedback, hover auto-expansion, post-drop visible update, and post-success reconciliation.

#### Scenario: Browser drag tooling is unavailable
- **WHEN** local Playwright or browser tooling is missing or cannot simulate drag reliably
- **THEN** the implementation pass MUST either install/use available browser tooling or record a concrete blocker
- **AND** it MUST NOT downgrade the verification plan to payload-only unit tests.

#### Scenario: Existing fallback movement commands are maintained
- **WHEN** menu-based move before/after or other precision movement commands remain available
- **THEN** those commands MUST use the same refresh and rollback semantics as drag movement
- **AND** they MUST remain accessible without relying on drag-and-drop alone.
