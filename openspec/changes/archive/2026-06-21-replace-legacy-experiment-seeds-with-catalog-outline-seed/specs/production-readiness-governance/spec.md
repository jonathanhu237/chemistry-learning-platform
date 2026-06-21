## MODIFIED Requirements

### Requirement: Protected Core Resource Manifest

The platform SHALL define a versioned manifest for every current core resource required to rebuild or validate the production baseline.

#### Scenario: Current resources are registered
- **GIVEN** the production-readiness manifest is generated or checked
- **WHEN** it lists protected core resources after the catalog outline seed replacement
- **THEN** it MUST include the canonical structured experiment catalog seed, the 30 mapped point-content example seed, the knowledge framework, canonical chunks, canonical embeddings, ES analyzer dictionaries, and current import/validation reports
- **AND** each entry MUST record semantic role, path or source location, required status, item count where applicable, byte size, and SHA256 where applicable.

#### Scenario: Retired resources are encountered
- **GIVEN** old point inventory files, old point-aware question-bank seed files, old manually reviewed point evidence files, or old video-point evidence artifacts remain under historical paths
- **WHEN** cleanup classification or production validation runs
- **THEN** those retired resources MUST NOT be classified as protected current core data
- **AND** they MAY be archived or removed according to cleanup policy after the new protected resources validate.

#### Scenario: Canonical retrieval corpus is encountered
- **GIVEN** canonical chunks and chunk embeddings remain under current production resource paths
- **WHEN** cleanup classification or production validation runs
- **THEN** those corpus resources MUST remain classified as protected current core data
- **AND** they MUST NOT be deleted merely because old point evidence bindings are retired.

### Requirement: Production Validation Chain

The repository SHALL provide a documented validation chain that proves the production baseline can be built, tested, and data-validated.

#### Scenario: Maintainer validates the baseline
- **GIVEN** a maintainer runs the production-readiness validation command or documented command set
- **WHEN** validation completes after the catalog outline seed replacement
- **THEN** it MUST check OpenSpec strict validation, protected resource manifests, catalog seed counts, 30-example content mapping, backend tests, frontend typecheck, frontend tests, frontend build, and core data counts
- **AND** it MUST report failures with enough detail to identify the broken stage.

#### Scenario: Fresh rebuild is verified
- **GIVEN** an empty database and the declared production resources are available
- **WHEN** the documented restore/import path is executed
- **THEN** the platform MUST recreate the current chapter-scoped experiment catalog tree from the structured seed
- **AND** it MUST recreate the 30 mapped point-content examples
- **AND** it MUST preserve or import canonical chunks and embeddings
- **AND** it MUST leave the retired experiment question bank and retired point evidence bindings empty or absent.

#### Scenario: Legacy protected counts are checked
- **GIVEN** validation code still contains old expected counts for 300 video points, 77 question banks, 2,310 questions, or 300 point evidence bindings
- **WHEN** the production-readiness validation command runs
- **THEN** validation MUST fail until those old protected counts are removed or replaced by catalog-outline seed expectations
- **AND** the failure MUST identify the outdated baseline expectation.

## ADDED Requirements

### Requirement: Retired seed documentation
Production operations documentation SHALL explain the intentional retirement of legacy experiment seed resources.

#### Scenario: Maintainer reads production seed documentation
- **WHEN** a maintainer reads the seed or production operations documentation after this change
- **THEN** the documentation MUST state that old question-bank seeds, old video point inventory, old video references, and old point evidence bindings are invalid for the current catalog baseline
- **AND** it MUST state that canonical chunks and embeddings remain valid retrieval corpus resources.

#### Scenario: Maintainer looks for question-bank regeneration instructions
- **WHEN** a maintainer searches the documentation for the new question-bank baseline
- **THEN** the documentation MUST state that the current bank is empty until fresh catalog-node evidence and a future generation workflow create a replacement
- **AND** it MUST NOT instruct maintainers to import the retired 2,310-question bank as a current baseline.
