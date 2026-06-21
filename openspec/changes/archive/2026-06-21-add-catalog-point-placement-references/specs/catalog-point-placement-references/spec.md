## ADDED Requirements

### Requirement: Canonical experiment point and catalog placement identity
The system SHALL separate canonical experiment point identity from catalog placement identity.

#### Scenario: New experiment is created in a directory
- **WHEN** a teacher creates a new point entry under a catalog directory
- **THEN** the system MUST create a canonical experiment point entity
- **AND** it MUST create a catalog point placement under the selected directory targeting that canonical experiment point.

#### Scenario: Existing experiment is reused in another directory
- **WHEN** a teacher adds an existing experiment to another catalog directory
- **THEN** the system MUST create a new catalog point placement with its own placement node id, parent id, chapter id, display order, and breadcrumbs
- **AND** the placement MUST target the existing canonical experiment point rather than copying point content, videos, evidence, question bindings, or assessment identity.

#### Scenario: Catalog tree is requested
- **WHEN** a catalog tree is requested by a student or teacher
- **THEN** each visible point entry MUST expose a durable placement node id
- **AND** it MUST expose or resolve the canonical experiment point id according to the caller's authorization and API contract.

#### Scenario: Placement and canonical ids are compared
- **WHEN** two visible point entries target the same canonical experiment point
- **THEN** the system MUST treat them as the same experiment for shared content, videos, evidence, question-bank identity, assessment identity, analytics identity, and feedback identity
- **AND** it MUST treat them as different catalog placements for parent path, ordering, breadcrumbs, and placement-level publication context.

### Requirement: Strict tree placement structure
The system SHALL keep catalog placement nodes in a normal chapter-scoped tree while allowing canonical experiment points to be reused.

#### Scenario: Placement has a parent
- **WHEN** a point placement is created or moved
- **THEN** it MUST have at most one parent directory within the catalog tree
- **AND** the move MUST NOT create true multi-parent node ids.

#### Scenario: Placement targets a canonical point
- **WHEN** a visible point placement exists
- **THEN** it MUST target exactly one canonical experiment point
- **AND** a directory node MUST NOT target a canonical experiment point.

#### Scenario: Legacy shortcut kind is submitted
- **WHEN** a client attempts to create a `shortcut`, `reference`, or other non-directory/non-point catalog node kind
- **THEN** the system MUST reject the request
- **AND** reuse MUST be represented by point placements targeting canonical experiment points.

### Requirement: Shared experiment editing semantics
The system SHALL make shared canonical experiment fields editable from any placement while preserving placement-local fields.

#### Scenario: Teacher edits shared point content from a reused placement
- **WHEN** a teacher edits experiment title, principle, reaction equations, phenomenon explanation, safety note, teacher-only point note, videos, or other shared point content from any placement
- **THEN** the system MUST save the change on the canonical experiment point
- **AND** all active placements targeting that canonical experiment point MUST reflect the shared change.

#### Scenario: Teacher edits placement-local data
- **WHEN** a teacher edits placement parent, display order, placement publication state, breadcrumbs through movement, or explicitly supported placement card overrides
- **THEN** the system MUST update only that placement
- **AND** it MUST NOT duplicate or fork the canonical experiment point.

#### Scenario: Shared experiment has multiple placements
- **WHEN** a teacher opens an editor for an experiment that has more than one active placement
- **THEN** the editor MUST show that the experiment is reused in multiple directories
- **AND** it MUST indicate that shared content edits affect every listed placement.

### Requirement: Placement removal and canonical archival
The system SHALL remove catalog placements independently from canonical experiment points and SHALL guard final canonical archival.

#### Scenario: Non-final placement is removed
- **WHEN** a teacher removes or archives one placement while at least one other active placement targets the same canonical experiment point
- **THEN** the system MUST remove or archive only that placement
- **AND** it MUST preserve the canonical experiment point, shared content, videos, evidence bindings, question bindings, assessment identity, analytics, and feedback references.

#### Scenario: Final placement removal is requested
- **WHEN** a teacher attempts to remove or archive the last active placement for a canonical experiment point
- **THEN** the system MUST require an explicit final-placement decision before archiving the canonical experiment point
- **AND** it MUST NOT silently hard-delete shared content, videos, evidence, question, assessment, analytics, or feedback data.

#### Scenario: Canonical experiment is archived
- **WHEN** a canonical experiment point is archived after final-placement confirmation or an authorized canonical archive action
- **THEN** the system MUST disable student access and search documents for all of its placements
- **AND** it MUST preserve audit metadata needed to understand historical question, assessment, analytics, and feedback references.

### Requirement: Placement-aware student point detail
The system SHALL resolve student point detail through placement context to canonical experiment content.

#### Scenario: Student opens a point placement
- **WHEN** a student opens a point detail route using a placement node id
- **THEN** the backend MUST resolve the placement to its canonical experiment point
- **AND** the response MUST include canonical experiment content, videos, related points, and assessment context together with the source placement breadcrumbs.

#### Scenario: Same canonical experiment is opened from different placements
- **WHEN** a student opens the same canonical experiment through two different published placements
- **THEN** both responses MUST show the same shared experiment content and videos
- **AND** each response MUST preserve its own chapter, breadcrumbs, source placement id, and route-return context.

#### Scenario: Placement is unavailable
- **WHEN** a placement is archived, unpublished, missing, or belongs to an unavailable catalog path
- **THEN** the student point detail route MUST return a controlled unavailable response
- **AND** it MUST NOT expose canonical experiment content through that unavailable placement.

### Requirement: Placement-aware student search indexing
The system SHALL index published point placements as search documents while grouping shared learning identity by canonical experiment point.

#### Scenario: Published placement is indexed
- **WHEN** a point placement and its catalog path are published and the canonical experiment point has publishable content
- **THEN** the system MUST create or update a student search document keyed by the placement node id
- **AND** the document MUST include placement id, canonical experiment point id, chapter context, catalog path, canonical point content, student-facing related text, extracted chemistry terms, and published video metadata.

#### Scenario: Canonical content changes
- **WHEN** shared canonical experiment content or videos change
- **THEN** the system MUST enqueue search upserts for every active published placement targeting that canonical experiment point
- **AND** unpublished or archived placements MUST NOT be indexed as active student search results.

#### Scenario: Placement path changes
- **WHEN** a placement is moved, published, unpublished, archived, or restored
- **THEN** the system MUST update or delete the search document for that placement
- **AND** it MUST NOT create duplicate documents for unrelated placements.

### Requirement: Reviewed seed grouping for duplicate experiment leaves
The system SHALL use reviewed grouping rules when converting catalog outline leaves into canonical experiment points and placements.

#### Scenario: Singleton leaf is seeded
- **WHEN** an outline leaf has no reviewed duplicate mapping
- **THEN** the seed process MUST create one canonical experiment point
- **AND** it MUST create one placement for the leaf under the full outline path.

#### Scenario: Reviewed duplicate leaves are seeded
- **WHEN** multiple outline leaves are reviewed as the same real experiment
- **THEN** the seed process MUST create one canonical experiment point
- **AND** it MUST create one placement per reviewed leaf path targeting that canonical experiment point.

#### Scenario: Ambiguous duplicate title is encountered
- **WHEN** two leaves have the same or similar title but no reviewed grouping rule
- **THEN** the seed process MUST keep them as separate canonical experiment points
- **AND** it MUST report the ambiguity for product/data review rather than merging by title alone.

#### Scenario: Corrected sibling hypochlorite points are seeded
- **WHEN** the outline contains `NaClO + MnSO4` and `NaClO + 品红溶液` as sibling leaves
- **THEN** the seed process MUST keep them as distinct placements
- **AND** it MUST keep them targeting distinct canonical experiment points unless an explicit future review says otherwise.

### Requirement: Corrected outline import completion
The system SHALL import the complete corrected experiment outline into the active catalog after the canonical point and placement architecture is available.

#### Scenario: Corrected outline import runs
- **WHEN** the corrected outline importer runs against the target development database after the canonical point/placement migration
- **THEN** the active visible catalog MUST contain 569 nodes derived from `docs/实验目录_整理版.md`
- **AND** those visible nodes MUST include 176 directory nodes and 393 point placement nodes.

#### Scenario: Full directory tree is preserved
- **WHEN** the corrected outline import completes
- **THEN** every imported `##` section and every non-leaf bullet from the outline MUST be represented as a visible directory node in the same chapter path and source order
- **AND** every imported leaf bullet MUST be represented as a visible point placement targeting a canonical experiment point.

#### Scenario: Chapter 21 placeholder is imported
- **WHEN** the importer encounters the chapter 21 placeholder text `暂无对应实验内容`
- **THEN** chapter 21 MUST remain empty
- **AND** the importer MUST NOT create a directory, point placement, canonical experiment point, or placeholder content for that text.

#### Scenario: Placement-to-canonical integrity is validated
- **WHEN** the corrected outline import validation runs
- **THEN** every active point placement MUST target exactly one active canonical experiment point
- **AND** every non-archived canonical experiment point created by the import MUST have at least one active point placement.

#### Scenario: Canonical grouping count is reported
- **WHEN** the corrected outline import validation reports results
- **THEN** it MUST report visible directory count, visible point placement count, total visible node count, canonical experiment point count, duplicate grouping count, and ambiguous duplicate count
- **AND** the canonical experiment point count MUST be derived from the reviewed grouping map rather than from automatic title-only dedupe.

#### Scenario: Sample content is imported after grouping
- **WHEN** the 30 sample content examples are imported
- **THEN** every sample MUST bind through its reviewed placement mapping to exactly one canonical experiment point
- **AND** the validation MUST confirm 30 unique sample target placements and their canonical point bindings.

#### Scenario: Existing incorrect independent point seed is replaced
- **WHEN** the corrected outline import completes
- **THEN** old independent duplicate point identities that conflict with the reviewed canonical grouping MUST no longer be the authoritative active seed baseline
- **AND** validation MUST fail if the active catalog still exposes reviewed duplicate experiments as unrelated canonical point identities.

### Requirement: Migration audit for point identity split
The system SHALL provide auditable migration mapping from old catalog point nodes to new placements and canonical experiment points.

#### Scenario: Existing point node is migrated
- **WHEN** an existing catalog point node is migrated
- **THEN** the migration MUST record the old node id, resulting placement node id, resulting canonical experiment point id, duplicate grouping decision, and migration source
- **AND** the record MUST be available for validation and data repair.

#### Scenario: Conflicting duplicate resources are found
- **WHEN** multiple old point nodes grouped into one canonical experiment point have conflicting content, video bindings, evidence state, question references, or publication state
- **THEN** the migration MUST produce a conflict report
- **AND** it MUST use deterministic safe defaults that preserve data without silently overwriting reviewed content.
