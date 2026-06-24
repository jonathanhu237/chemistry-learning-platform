## ADDED Requirements

### Requirement: OpenSpec inventory cleanup preserves durable capability boundaries
The engineering workflow SHALL consolidate OpenSpec capability specs when repeated implementation changes leave obsolete, empty, duplicate, or iteration-named specs behind.

#### Scenario: Completed UI iterations create overlapping specs
- **WHEN** several archived changes describe the same durable product surface through narrow implementation-era capability names
- **THEN** a follow-up cleanup MUST merge those requirements into stable owner capabilities
- **AND** it MUST preserve the normative requirements while removing obsolete or empty capability specs.

#### Scenario: A spec becomes an obsolete placeholder
- **WHEN** a capability spec has no requirements or describes a product path that has been replaced by current behavior
- **THEN** the cleanup MUST either delete the empty capability or migrate any still-valid requirements into the current owner spec
- **AND** the change summary MUST identify the replacement owner.

#### Scenario: A cleanup touches only specs
- **WHEN** an OpenSpec cleanup changes only `openspec/specs` and OpenSpec change artifacts
- **THEN** strict spec validation is the required verification gate
- **AND** application code tests are not required unless runtime code or generated artifacts are changed.
