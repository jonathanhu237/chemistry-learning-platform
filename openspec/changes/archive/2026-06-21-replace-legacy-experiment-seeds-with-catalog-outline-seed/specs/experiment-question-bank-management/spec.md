## ADDED Requirements

### Requirement: Catalog reset leaves default experiment question bank empty
The system SHALL treat the legacy default experiment question bank as invalid after the canonical catalog seed replacement.

#### Scenario: Catalog seed replacement runs
- **WHEN** the canonical catalog seed replacement resets seed-derived experiment data
- **THEN** it MUST remove or disable legacy experiment question banks and questions that were generated from old formal experiment and old point identities
- **AND** it MUST NOT preserve the old 2,310-question bank as current, draft, review, or candidate seed data.

#### Scenario: Teacher opens question bank after reset
- **WHEN** a teacher opens the experiment question bank page before a new evidence-backed bank is generated
- **THEN** the page MUST represent the current bank as empty for the affected experiment catalog scope
- **AND** it MUST NOT imply old question coverage is still valid.

### Requirement: New question-bank generation depends on catalog-node evidence
The system SHALL require fresh catalog-node source evidence before creating a new default experiment question bank.

#### Scenario: Question generation is requested for the new catalog
- **WHEN** an administrator or teacher requests default question-bank generation for the new experiment catalog
- **THEN** the generation workflow MUST use catalog point node identities
- **AND** it MUST require fresh source evidence bound to those catalog point nodes.

#### Scenario: Evidence has not been regenerated
- **WHEN** a question-bank generation workflow has no fresh catalog-node evidence for the requested point scope
- **THEN** it MUST block or mark generation as unavailable
- **AND** it MUST NOT fall back to legacy point keys, legacy reviewed bank artifacts, or old point evidence bindings.

## REMOVED Requirements

### Requirement: Point-aware default bank review
**Reason**: The old 2,310-question default bank and its old point-key review workflow are invalid after the catalog outline replacement.

**Migration**: Treat the current default bank as empty. A future change may define a new catalog-node evidence-backed question-bank generation and review process.

### Requirement: Point-aware diagnostic bank migration closure
**Reason**: The imported reviewed point-aware default bank is no longer the production migration target because it is tied to retired formal experiment and old video-point identities.

**Migration**: Use the canonical catalog seed as the new experiment structure baseline and wait for fresh catalog-node evidence before creating a replacement bank.

### Requirement: Point-aware diagnostic release evidence
**Reason**: Release evidence for the old imported point-aware default bank no longer describes the current catalog baseline.

**Migration**: Preserve future release evidence only for a newly generated bank that binds to catalog point node ids and fresh source references.
