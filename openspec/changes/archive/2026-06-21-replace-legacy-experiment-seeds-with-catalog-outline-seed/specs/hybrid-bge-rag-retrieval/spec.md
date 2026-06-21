## ADDED Requirements

### Requirement: Catalog-node point evidence rebuild contract
The system SHALL treat old experiment video point evidence bindings as invalid after the catalog outline seed replacement and SHALL require future evidence generation to target catalog point node identities.

#### Scenario: Catalog seed replacement retires evidence bindings
- **WHEN** the canonical catalog seed replacement resets old experiment point data
- **THEN** it MUST remove or disable legacy point-to-chunk evidence bindings derived from old formal experiment and video point identities
- **AND** it MUST preserve canonical chunks and chunk embeddings as reusable retrieval corpus data.

#### Scenario: Future evidence generation selects points
- **WHEN** a future GPU/BGE rerank evidence generation job runs for the new catalog
- **THEN** it MUST load target points from leaf catalog nodes
- **AND** it MUST identify each target by catalog node id or deterministic catalog seed key rather than `experiment_id` and `point_key`.

#### Scenario: Future evidence generation builds queries
- **WHEN** a future GPU/BGE rerank evidence generation job prepares retrieval queries for a catalog point
- **THEN** it MUST include the point title and full catalog path context
- **AND** it MUST NOT rely on retired formal experiment titles as the authoritative scope.

#### Scenario: Future evidence output is imported
- **WHEN** freshly generated evidence is imported for catalog points
- **THEN** each evidence record MUST bind to a catalog point node identity
- **AND** validation MUST reject rows that only reference legacy experiment ids or old point keys.

### Requirement: Evidence-dependent AI generation fails closed during reset
The system SHALL not generate new point-aware question-bank content from ungrounded or legacy evidence during the reset window.

#### Scenario: Teacher workbench requests evidence-backed generation
- **WHEN** a teacher or administrator starts evidence-backed question generation for a catalog point before fresh evidence exists
- **THEN** the backend MUST report insufficient catalog-node evidence
- **AND** it MUST NOT silently use old evidence bindings or ungrounded generation.

#### Scenario: BGE service configuration is validated
- **WHEN** catalog-node evidence generation tooling is implemented or reused
- **THEN** it MUST validate the configured BGE service URL and port before generating evidence
- **AND** it MUST fail with a diagnostic if the runtime configuration does not match the available BGE service.
