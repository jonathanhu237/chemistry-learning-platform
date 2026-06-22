## MODIFIED Requirements

### Requirement: Catalog node kinds
The system SHALL support exactly directory and point node kinds with explicit behavior and without manual student-card presentation fields.

#### Scenario: Directory node is opened
- **WHEN** a directory node is opened
- **THEN** the system MUST return its child nodes, breadcrumbs, directory identity, publication state, teacher authoring metadata where applicable, and navigation metadata
- **AND** it MUST NOT require or expose point learning content, video bindings, related point links, assessment context, ES result identity, manual student-card description, manual card image, manual card icon, manual card accent, manual card layout, or manual card presentation metadata for the directory itself.

#### Scenario: Point node is opened
- **WHEN** a point node is opened
- **THEN** the system MUST return point detail content, video bindings, related links, assessment context, and source path context where available
- **AND** it MUST NOT return child catalog nodes, manual point-card short description, manual point-card cover image, manual point-card icon, manual point-card accent, or manual point-card emphasis fields for the point.

#### Scenario: Point node is used as parent
- **WHEN** a client attempts to create or move another catalog node under a point node
- **THEN** the system MUST reject the operation
- **AND** the point node id and existing bindings MUST remain unchanged.

#### Scenario: Hybrid or shortcut node kind is submitted
- **WHEN** a client attempts to create or update a catalog node with kind `hybrid` or `shortcut`
- **THEN** the system MUST reject the request
- **AND** no live compatibility path MUST preserve hybrid or shortcut behavior.

## ADDED Requirements

### Requirement: Manual student-card fields are removed
The catalog tree data model SHALL remove obsolete manual student-card presentation fields from live schema, APIs, and read models.

#### Scenario: Catalog schema migration runs
- **WHEN** the migration for this change is applied
- **THEN** the catalog node storage MUST drop manual student-card fields including `student_description`, `card_image_asset_id`, `card_icon_key`, `card_accent`, `card_layout`, `card_presentation`, and `point_card_presentation`
- **AND** the migration MUST NOT attempt to preserve or reconstruct values from those fields.

#### Scenario: Catalog node create or update is requested
- **WHEN** a client sends create or update payload fields for removed student-card presentation data
- **THEN** the backend MUST ignore, reject, or strip those fields according to the API compatibility policy
- **AND** no removed field value MUST be persisted in catalog node storage.

#### Scenario: Catalog node read model is returned
- **WHEN** teacher, student, search, or preview read models serialize catalog nodes
- **THEN** the payload MUST NOT include the removed manual student-card fields
- **AND** consumers MUST derive student-facing card display from remaining catalog, point-content, and video metadata.

#### Scenario: Seed or import code processes catalog nodes
- **WHEN** catalog seed, copy, import, or reset code creates catalog nodes
- **THEN** it MUST NOT populate removed student-card fields
- **AND** validation MUST fail or warn if fixtures/tests still depend on those removed fields.

### Requirement: Catalog card display is derived from authoritative content
The system SHALL treat student catalog card display as a read-model projection rather than teacher-authored card configuration.

#### Scenario: Directory card projection is needed
- **WHEN** a student catalog response needs to render a directory card
- **THEN** the read model MUST provide enough remaining metadata for title, hierarchy, child availability, and stable default visual treatment
- **AND** it MUST NOT depend on stored directory student-card copy, image, icon, accent, or layout fields.

#### Scenario: Point card projection is needed
- **WHEN** a student catalog response needs to render a point card
- **THEN** the read model MUST derive title from point/catalog title, derive optional summary from point learning content when available, and derive visual media from bound video thumbnail when available
- **AND** it MUST NOT depend on stored point-card override fields.

#### Scenario: Search documents are built
- **WHEN** student search or video-library documents are built
- **THEN** searchable student-facing text MUST come from directory titles/path, point title, point learning content, related experiment titles, and video metadata
- **AND** it MUST NOT include removed manual student-card description or presentation fields.

### Requirement: Related experiment titles are canonical target titles
The catalog related-link model SHALL keep ordering, hidden/default override state, and manual additions without supporting teacher-authored student-facing short display names.
The catalog related-link storage SHALL NOT retain obsolete title override columns for related-link labels.

#### Scenario: Teacher saves related experiment links
- **WHEN** a teacher saves related experiment links for a point
- **THEN** the write payload MUST identify target point nodes, relation type, hidden state, sort order, and metadata where needed
- **AND** it MUST NOT accept or persist a student-facing display label, short name, or per-link title override.

#### Scenario: Stale clients send a related-link label
- **WHEN** a stale client sends a `label`, `display_title`, `short_title`, or equivalent title override for a related link
- **THEN** the backend MUST reject, ignore, or strip that value according to the API compatibility policy
- **AND** the value MUST NOT affect persisted related-link ordering, target identity, search text, preview payloads, student payloads, or AI context.

#### Scenario: Related-link title override columns are migrated away
- **WHEN** catalog migrations are applied to an existing database
- **THEN** obsolete related-link `label` columns MUST be dropped from both legacy and catalog related-link tables
- **AND** fresh database baseline migrations MUST NOT create related-link `label` columns.

#### Scenario: Related links are read for teacher authoring
- **WHEN** the teacher workbench reads related links for a point
- **THEN** each link MUST expose the resolved target experiment title from the canonical target point or placement
- **AND** the payload MUST NOT require the teacher frontend to hydrate a short-name or display-label form field.

#### Scenario: Related links are read for students or preview
- **WHEN** student H5, teacher preview, search documents, video-library search, or AI context consumes related links
- **THEN** the visible related experiment title MUST come from the resolved target point title
- **AND** any old stored label value MUST NOT override `target_title`.

#### Scenario: Existing persisted title override data is removed by migration
- **WHEN** old related-link records contain stored label values from a previous implementation
- **THEN** the destructive migration MUST remove the obsolete label columns instead of preserving those values
- **AND** teacher detail, teacher preview, student H5, search documents, video-library search, and AI context MUST use the resolved target experiment title.

## REMOVED Requirements

### Requirement: Directory card presentation
**Reason**: Directory card presentation fields are a manual student-card configuration model that the product no longer wants to maintain.

**Migration**: Drop the fields and derive directory card display from directory title, hierarchy, child availability, and stable student frontend defaults.

### Requirement: Point card presentation stays constrained
**Reason**: Point card overrides are no longer considered useful even when constrained; they duplicate point content and obscure the one-point learning primitive.

**Migration**: Drop `point_card_presentation` and derive point card display from point title, point learning content summary, binary video state, and bound video thumbnail when available.
