## ADDED Requirements

### Requirement: Authoritative docs catalog seed
The system SHALL treat the updated experiment catalog docs as the authoritative seed source for catalog structure.

#### Scenario: Full catalog tree is imported
- **WHEN** the authoritative catalog seed is imported
- **THEN** the system MUST preserve the complete chapter directory hierarchy from the docs
- **AND** it MUST NOT collapse the tree to only point leaves.

#### Scenario: Leaf nodes are experiment points
- **WHEN** a seed item has no child experiment catalog items under the authoritative docs structure
- **THEN** the system MUST create it as a point-capable catalog node
- **AND** parent directory nodes MUST remain directory/navigation nodes even when all descendants are points.

#### Scenario: Empty or placeholder content is encountered
- **WHEN** the docs contain placeholder wording such as no corresponding experiment content
- **THEN** the importer MUST treat the placeholder as empty source content
- **AND** it MUST NOT create fake point text, fake evidence, or fake student-facing content from that placeholder.

### Requirement: Catalog seed replaces legacy experiment point seeds
The system SHALL use catalog node identities as the only authoritative point identity after seed replacement.

#### Scenario: Legacy point evidence is removed from seed baseline
- **WHEN** the catalog seed reset runs
- **THEN** old point-to-chunk bindings keyed by legacy `(experiment_id, point_key)` MUST be cleared or marked retired
- **AND** canonical `source_chunks` and embeddings MUST remain available as the candidate evidence corpus.

#### Scenario: Legacy question bank is removed from seed baseline
- **WHEN** the catalog seed reset runs
- **THEN** old question-bank seed data that depends on invalid legacy point identity MUST be cleared or made inactive
- **AND** the system MUST treat the new default question bank as empty until catalog-node evidence regeneration succeeds.

#### Scenario: Validation checks legacy identity leakage
- **WHEN** production resource validation runs after the seed reset
- **THEN** it MUST fail if active point evidence or generated question seed rows still depend only on legacy `(experiment_id, point_key)` identity
- **AND** it MUST accept references keyed by catalog node id or stable catalog seed key.

### Requirement: Sample point seed maps examples to catalog nodes
The system SHALL map the 30 sample point examples to real catalog point nodes rather than importing them as detached examples.

#### Scenario: Sample title is short or ambiguous
- **WHEN** a sample point example contains only a short title, reagent phrase, or main-number block
- **THEN** the mapper MUST match it against catalog path, leaf title, known reagent names, teacher note, and point content context
- **AND** it MUST NOT assume that the main-number block alone identifies the correct node.

#### Scenario: Sample mapping is ambiguous
- **WHEN** two or more catalog point nodes remain plausible matches for one sample
- **THEN** the mapping process MUST require an explicit override or review record
- **AND** it MUST NOT silently bind the sample to an arbitrary node.

#### Scenario: Corrected sample wording is used
- **WHEN** a known sample wording correction exists, such as `NaClO + 品红溶液`
- **THEN** the seed mapping MUST use the corrected wording for matching and reporting
- **AND** validation MUST surface the correction so future runs do not reintroduce the old typo.

### Requirement: Directories remain first-class catalog content
The catalog tree SHALL preserve directory nodes as first-class teacher-managed navigation content.

#### Scenario: Directory has no direct point content
- **WHEN** a directory node has no point content fields
- **THEN** teacher APIs MUST still return it for tree editing and organization
- **AND** student APIs MAY use publication rules to show, hide, or render it as navigation without treating it as an experiment point.

#### Scenario: Directory is moved
- **WHEN** a directory subtree is moved
- **THEN** all descendant point node ids MUST remain stable
- **AND** ES state, evidence state, videos, questions, analytics, and sample mappings MUST continue to resolve through catalog node identity.
