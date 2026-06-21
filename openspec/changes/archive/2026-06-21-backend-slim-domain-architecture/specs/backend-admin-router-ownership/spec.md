## MODIFIED Requirements

### Requirement: Existing admin API contracts remain compatible
The backend SHALL preserve only the canonical admin API route inventory accepted for the backend slim architecture. Legacy aliases and compatibility endpoints MAY be removed when the updated route inventory, frontend calls, backend tests, and e2e validation are changed deliberately in the same refactor.

#### Scenario: Canonical path and method pairs remain registered
- **WHEN** the production FastAPI app route table is inspected
- **THEN** every admin path and method pair listed in the updated canonical route inventory MUST be registered
- **AND** each canonical path and method pair MUST be registered exactly once.

#### Scenario: Legacy compatibility aliases are removed
- **WHEN** a path exists only to preserve an older admin route alias, internal module shape, or deprecated deletion/archive behavior
- **THEN** the backend slim refactor MAY remove that alias
- **AND** the removed alias MUST NOT remain registered unless it is explicitly listed as canonical in the updated route inventory
- **AND** clients and tests MUST be updated to use the canonical route.

#### Scenario: Removed route aliases are recorded
- **WHEN** route aliases are removed during the backend slim refactor
- **THEN** the route inventory or implementation notes MUST record the removed aliases and their canonical replacements or deletion rationale.
