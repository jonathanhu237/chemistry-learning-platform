# experiment-catalog-tree Specification

## Purpose
TBD - created by archiving change experiment-catalog-tree-point-architecture. Update Purpose after archive.
## Requirements
### Requirement: Published catalog edits preserve visibility
The catalog tree SHALL keep publication visibility separate from routine teacher edits to published catalog content.

#### Scenario: Teacher edits an already published point
- **WHEN** a teacher changes point title, principle, reaction equations, phenomenon explanation, safety note, related links, or video binding on a point whose placement and shared content are already published
- **THEN** the point and content MUST remain published unless the teacher explicitly unpublishes, archives, hides, or deletes it
- **AND** student-facing read models MUST read the latest saved authoritative content according to current publication and path visibility rules.

#### Scenario: Teacher edits a published point into an incomplete state
- **WHEN** a teacher clears or invalidates a required field on an already published point
- **THEN** the node status model MUST report the missing or invalid field as content completeness state
- **AND** it MUST NOT silently convert the point or content publication state to draft solely because the field was edited.

#### Scenario: Teacher edits a published directory title
- **WHEN** a teacher changes a published directory title or moves a published directory in a way that affects descendant paths
- **THEN** descendant point placements MUST keep their own publication state
- **AND** downstream search/evidence state MUST be marked stale or pending for affected placements rather than treating the directory edit as an unpublish action.

#### Scenario: Teacher-only note changes
- **WHEN** a teacher edits a directory or point teaching note that is not exposed to students or student search
- **THEN** the system MUST persist the note for teacher/admin use
- **AND** it MUST NOT change publication visibility or student-searchable content by itself.

### Requirement: Publication actions are explicit visibility transitions
The catalog tree SHALL reserve publication-state changes for explicit visibility actions, not autosave side effects.

#### Scenario: Teacher explicitly publishes an unpublished point
- **WHEN** a teacher explicitly publishes a valid unpublished point
- **THEN** the system MUST update the point/content publication state to published
- **AND** downstream ES/RAG sync MUST be triggered according to the hard-change policy.

#### Scenario: Teacher explicitly removes visibility
- **WHEN** a teacher explicitly unpublishes, archives, hides, deletes, or moves a point under an unpublished path
- **THEN** the system MUST remove or disable student visibility according to catalog rules
- **AND** downstream ES delete or disable work MUST be triggered immediately.

### Requirement: Catalog point media bindings expose student playback metadata
The catalog tree service SHALL include student playback metadata in teacher point-detail media binding responses.

#### Scenario: Ready learning rendition exists
- **WHEN** a teacher opens a point with an active video binding whose media asset has a ready learning rendition
- **THEN** the media binding payload MUST include the learning rendition file size as `playback_file_size_bytes`
- **AND** it MUST include the learning rendition width and height as `playback_width` and `playback_height` when available
- **AND** it MUST include the learning rendition duration as `playback_duration_seconds` when available
- **AND** it MUST include available playback frame rate, bitrate, video codec, and audio codec metadata for that rendition
- **AND** it MUST keep the media asset `created_at` timestamp available for upload-time display.

#### Scenario: No ready learning rendition exists
- **WHEN** a teacher opens a point with an active video binding whose media asset has no ready learning rendition
- **THEN** the media binding payload MUST prefer another ready rendition when available
- **AND** if no ready rendition is available, it MUST fall back to the asset playback/source metadata without failing the point-detail response
- **AND** it MUST NOT label the uploaded source file size as a processed student playback rendition.

#### Scenario: Binding is inactive or asset is archived
- **WHEN** a media binding is archived or the media asset lifecycle is no longer active
- **THEN** the point-detail media binding response MUST continue excluding that binding
- **AND** playback metadata MUST NOT make inactive bindings appear current.

### Requirement: Chapter-scoped recursive catalog tree
The system SHALL model experiment learning structure as a chapter-scoped recursive catalog tree rather than a fixed chapter -> experiment -> point hierarchy.

#### Scenario: Chapter catalog is requested
- **WHEN** a chapter catalog is requested by an authorized user
- **THEN** the system MUST return root catalog nodes for that chapter ordered by display order
- **AND** each node MUST expose enough metadata to render either directory navigation/card behavior or point learning behavior.

#### Scenario: Catalog depth differs by chapter
- **WHEN** two chapters have different directory depths
- **THEN** the system MUST support both without requiring placeholder experiment levels
- **AND** the student and teacher APIs MUST NOT assume a fixed third, fourth, or fifth level.

#### Scenario: Directory has no point children
- **WHEN** a directory node currently has no published child point nodes
- **THEN** the system MUST keep the directory editable for teachers
- **AND** the student API MUST either hide it or render an intentional empty state according to publication settings.

#### Scenario: Teacher opens a chapter workbench
- **WHEN** the teacher workbench loads a chapter catalog tree
- **THEN** the admin API MUST expose chapter-level counts for active directory nodes, point nodes, playable video points, missing-video points, and actionable point nodes
- **AND** it MUST expose point status buckets for `blocked`, `needs_content`, `needs_video`, `ready`, `draft`, `published`, and `sync_attention`
- **AND** the teacher UI MUST present those counts near the tree controls instead of requiring teachers to infer them from expanded rows.

#### Scenario: Teacher filters or searches the tree
- **WHEN** a teacher uses the chapter tree status controls
- **THEN** the UI MUST offer filters covering all primary point states: all, actionable, blocked, needs content, needs video, ready/draft, published, and sync attention
- **AND** each filter MUST show its chapter-level point count when the summary is available.
- **WHEN** a teacher enters at least two characters in the tree search field
- **THEN** the search MUST run against the current chapter's catalog node title, summary, teacher note, point learning content, and legacy experiment identity fields.

### Requirement: Stable point node identity
The system SHALL use stable catalog point node identity as the authoritative identity for point learning content.

#### Scenario: Point is moved
- **WHEN** a teacher moves a point node to a different parent directory
- **THEN** the point node id MUST remain unchanged
- **AND** video bindings, point content, question bindings, assessment metadata, analytics, feedback context, and search index state MUST continue to resolve to the same point.

#### Scenario: Point is renamed
- **WHEN** a teacher renames a point node
- **THEN** the title and searchable text MUST update
- **AND** the identity used by stored bindings and historical records MUST NOT change.

#### Scenario: Legacy point key exists
- **WHEN** migrated data has a legacy `(experiment_id, point_key)` identity
- **THEN** the system MUST map it to a stable point node id
- **AND** new write paths MUST use the stable point node id instead of the legacy pair.

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

### Requirement: Point learning content belongs to point-capable nodes
The system SHALL attach manually authored point learning content only to point nodes.

#### Scenario: Teacher saves the point authoring model
- **WHEN** a teacher edits a point node
- **THEN** the system MUST support manually maintained point title, teacher-only note, point knowledge, related point links, and video bindings
- **AND** point knowledge MUST include principle mode with either equation or text, phenomenon explanation, and safety note.

#### Scenario: Teacher saves equation principle content
- **WHEN** a teacher saves point content with principle mode `equation`
- **THEN** the system MUST require a chemical equation value
- **AND** it MUST store phenomenon explanation and safety note as teacher-authored text.

#### Scenario: Teacher saves text principle content
- **WHEN** a teacher saves point content with principle mode `text`
- **THEN** the system MUST require a principle text value
- **AND** it MUST NOT require a chemical equation.

#### Scenario: Point has no video
- **WHEN** a point node has learning content but no published video
- **THEN** the system MUST still allow the point to appear in the catalog and search when published
- **AND** the student detail page MUST render a graceful no-video state.

#### Scenario: Teacher-only note is stored
- **WHEN** a teacher saves a teacher-only note for a point node
- **THEN** the system MUST persist the note for admin authoring context
- **AND** student APIs, student search documents, student snippets, and student page payloads MUST NOT expose or index the note.

#### Scenario: Directory receives point content
- **WHEN** a client attempts to save point learning content, video bindings, related point links, or point publication state on a directory node
- **THEN** the system MUST reject the operation
- **AND** the directory MUST remain a navigation/category node.

### Requirement: Related point links use node identities
The system SHALL represent related experiment links between stable point nodes.

#### Scenario: Default related links are generated
- **WHEN** a point has sibling or adjacent point nodes in the same catalog neighborhood
- **THEN** the system MAY generate default related links from nearby published points
- **AND** generated defaults MUST reference target point node ids.

#### Scenario: Teacher edits related links
- **WHEN** a teacher manually edits related point links
- **THEN** the system MUST persist the chosen target point node ids, labels, order, and hidden overrides
- **AND** it MUST allow links to points outside the current directory when selected intentionally.

### Requirement: Published point-node search documents
The system SHALL build student video-library search documents from published point nodes and their student-facing point knowledge.

#### Scenario: Published point is indexed
- **WHEN** a point node is published or its searchable content changes
- **THEN** the system MUST queue an ES document upsert keyed by point node id
- **AND** the document MUST include chapter path, ancestor directory category/path text, point title, principle, phenomenon explanation, safety note, student-facing related link text, extracted formulae, aliases, reaction features, and video readiness signals where available.
- **AND** the document MUST NOT include teacher-only notes, raw AI source chunks, `experiment_video_point_evidence` payloads, standalone directory-only documents, video resource titles, original file names, media asset ids, thumbnail paths, stream paths, or other video resource metadata.

#### Scenario: Point is unpublished or archived
- **WHEN** a point node becomes unpublished or archived
- **THEN** the system MUST queue deletion or disabling of its student search document.

#### Scenario: Directory text matches a search query
- **WHEN** a student searches for text that appears only in a published ancestor directory title or description
- **THEN** the search backend MUST return matching descendant published point documents
- **AND** it MUST NOT return the directory as an independent video-library result.

#### Scenario: Raw media asset exists
- **WHEN** a teacher uploads a media asset that is not bound to a published point node
- **THEN** the media asset MUST NOT appear in student video-library search.

#### Scenario: Bound video has a teacher-only title
- **WHEN** a published point has an active ready video binding whose media asset title or file name contains text absent from point content
- **THEN** that text MUST NOT be added to the student search document or searchable text
- **AND** search recall MUST depend on the point's authored learning content and catalog context instead.

### Requirement: Chemistry ES analyzer dictionaries
The system SHALL provide a production-ready ES/IK analyzer stack for student video-library search.

#### Scenario: ES index is created
- **WHEN** the student video-library ES index is created or recreated
- **THEN** the index MUST use an IK-based chemistry analyzer for Chinese text fields
- **AND** the analyzer stack MUST include the IK tokenizer, Harbin Institute of Technology stopwords, project chemistry stopwords, a chemistry custom dictionary, and a chemistry synonym dictionary.

#### Scenario: Dictionary assets are deployed
- **WHEN** the Docker Compose application stack starts ES/IK
- **THEN** the required stopword, custom dictionary, and synonym files MUST be available to the ES/IK container
- **AND** production readiness validation MUST fail if the analyzer assets or IK analyzer are missing.

#### Scenario: Chemistry synonym is searched
- **WHEN** a student searches by a formula, Chinese reagent name, English reagent name, ion notation, or common alias covered by the synonym dictionary
- **THEN** the search backend MUST match published point-node documents containing the equivalent student-facing point knowledge
- **AND** matching MUST NOT depend on teacher-only notes or AI evidence chunks.

### Requirement: Destructive legacy model replacement
The system SHALL retire legacy experiment-parent write paths and old seed-derived experiment data after replacing the catalog seed with the canonical outline-backed tree.

#### Scenario: Legacy admin point API is called
- **WHEN** a client calls the old experiment video-point write API after the catalog seed replacement
- **THEN** the system MUST not process the write as an authoritative path
- **AND** tests MUST verify application code uses catalog-node APIs.

#### Scenario: Legacy seed data is reset
- **WHEN** the new catalog seed replacement runs against a database containing legacy formal experiments, experiment video points, point content, media bindings, evidence bindings, or question-bank rows
- **THEN** the seed/import process MAY delete or replace those legacy seed-derived rows without preserving old-to-new audit mappings
- **AND** the resulting catalog tree MUST be rebuilt from the structured canonical outline seed.

#### Scenario: Non-seed resources exist
- **WHEN** the destructive seed replacement runs
- **THEN** it MUST preserve canonical RAG chunks, chunk embeddings, analyzer dictionaries, users, roles, courses, and other non-seed platform resources
- **AND** it MUST document which seed-derived tables are intentionally reset.

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

### Requirement: Canonical outline-backed catalog seed
The system SHALL use a structured seed derived from `docs/实验目录_整理版.md` as the authoritative default experiment catalog tree.

#### Scenario: Catalog seed is validated
- **WHEN** the catalog seed validation runs
- **THEN** it MUST confirm the seed represents 569 catalog nodes under existing chapter contexts
- **AND** it MUST confirm those nodes contain 176 directory nodes and 393 point nodes.

#### Scenario: Chapter section heading is imported
- **WHEN** a `##` heading appears under a chapter in the canonical outline
- **THEN** the seed MUST represent that heading as a directory node
- **AND** child bullet nodes MUST be nested below that directory in source order.

#### Scenario: Bullet node has children
- **WHEN** a bullet item in the canonical outline has child bullet items
- **THEN** the seed MUST represent that item as a directory node
- **AND** it MUST preserve its full parent path and display order.

#### Scenario: Bullet node has no children
- **WHEN** a bullet item in the canonical outline has no child bullet items
- **THEN** the seed MUST represent that item as a point node
- **AND** no seeded point node MUST have child nodes.

#### Scenario: Chapter 21 placeholder is encountered
- **WHEN** the canonical outline contains `暂无对应实验内容` for chapter 21
- **THEN** the seed MUST treat chapter 21 as empty
- **AND** it MUST NOT create a directory node, point node, or placeholder point for that text.

#### Scenario: Point marker text is absent
- **WHEN** the seed is generated or validated
- **THEN** it MUST NOT require `(点位)` annotations
- **AND** point classification MUST be derived from leaf structure.

### Requirement: Corrected hypochlorite branch entries
The catalog seed SHALL preserve the corrected chapter 13 hypochlorite entries as distinct point nodes.

#### Scenario: Hypochlorite points are validated
- **WHEN** the catalog seed validation checks chapter 13 `五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性`
- **THEN** it MUST find a point node titled `NaClO + MnSO₄`
- **AND** it MUST find a separate sibling point node titled `NaClO + 品红溶液`.

### Requirement: Seeded point content examples
The system SHALL seed the 30 point-content examples from `docs/30点位例子.txt` by explicit mapping to catalog point nodes.

#### Scenario: Example content seed is validated
- **WHEN** the point-content example seed is validated
- **THEN** every example MUST resolve to exactly one catalog point node
- **AND** the 30 examples MUST resolve to 30 unique point nodes.

#### Scenario: Example content is imported
- **WHEN** a mapped example is imported
- **THEN** its `实验原理` MUST be stored as text-mode principle content for the mapped point node
- **AND** its `现象解释` MUST be stored as the phenomenon explanation
- **AND** its `安全提示` MUST be stored as the safety note.

#### Scenario: ES smoke content is indexed
- **WHEN** the 30 mapped example points are imported in an indexable status
- **THEN** the student search document builder MUST index their student-facing principle, phenomenon, and safety content
- **AND** it MUST NOT require legacy experiment video point evidence to index those fields.

### Requirement: Hybrid and shortcut live semantics are removed
The system SHALL remove live hybrid and shortcut semantics from catalog tree behavior.

#### Scenario: Existing hybrid data is migrated
- **WHEN** a migration encounters an existing hybrid node
- **THEN** it MUST normalize the record to directory and/or point semantics using deterministic rules
- **AND** it MUST preserve migration metadata for audit or data repair.

#### Scenario: Existing shortcut data is migrated
- **WHEN** a migration encounters an existing shortcut node
- **THEN** it MUST remove shortcut behavior from live student and teacher APIs
- **AND** it MUST either materialize an allowed directory/point placement or archive the shortcut with audit metadata.

#### Scenario: Shortcut route is requested
- **WHEN** a client attempts to use shortcut target behavior after this change
- **THEN** the system MUST return a controlled rejection or unavailable response
- **AND** it MUST NOT resolve point detail through a shortcut node.

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
- **THEN** the read model MUST derive title from point/catalog title, derive optional summary from point learning content when available, and MAY derive visual media from the active ready bound video thumbnail
- **AND** it MUST NOT depend on stored point-card override fields.

#### Scenario: Search documents are built
- **WHEN** student search or video-library documents are built
- **THEN** searchable student-facing text MUST come from directory titles/path, point title, point learning content, and related experiment titles
- **AND** searchable text MUST NOT include removed manual student-card description, presentation fields, video resource titles, original file names, media asset titles, or other teacher-only video labels.

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

### Requirement: Catalog point video binding is a single active reference
The catalog tree service SHALL model a point's experiment video as at most one active media binding per canonical point.

#### Scenario: Teacher binds a video to a point
- **WHEN** a teacher binds an eligible media asset to a catalog point
- **THEN** the service MUST make that media asset the only active non-archived video binding for the point's canonical point identity
- **AND** any previous active video binding for that canonical point MUST be replaced in the same transaction.

#### Scenario: Teacher replaces a point video
- **WHEN** a teacher selects a different media asset for a point that already has an active video binding
- **THEN** the new media asset MUST replace the previous active binding
- **AND** subsequent point detail reads MUST return only the replacement video as the current point video.

#### Scenario: Teacher binds the existing current video again
- **WHEN** a teacher binds the same media asset that is already active for the point
- **THEN** the service MUST keep a single active binding
- **AND** it MUST update safe binding metadata without creating duplicate active rows.

#### Scenario: Existing data contains duplicate active binding rows
- **WHEN** the migration for this change runs on data with duplicate non-archived video binding rows for one canonical point
- **THEN** the migration MUST keep one deterministic active binding per canonical point
- **AND** it MUST hard-delete all other active bindings for that canonical point.

### Requirement: Catalog point video binding has no teacher-facing publish state
The catalog tree service SHALL stop treating point video bindings as independently published authoring objects.

#### Scenario: New video binding is created
- **WHEN** a teacher binds a media asset to a point
- **THEN** the request MUST NOT require a binding-level `draft` or `published` choice
- **AND** the resulting binding MUST be active unless it is explicitly removed.

#### Scenario: Stale client sends binding status
- **WHEN** a stale client sends `status`, `binding_status`, `published_by`, or `published_at` for a catalog point video binding
- **THEN** the service MUST ignore, strip, or reject those values according to the API compatibility policy
- **AND** stale status values MUST NOT create a hidden draft binding that prevents a ready video from appearing to students.

#### Scenario: Teacher removes a video binding
- **WHEN** a teacher removes the current point video
- **THEN** the service MUST archive or delete the active binding
- **AND** subsequent point detail reads MUST show no current video for that point.

#### Scenario: Video asset is not ready
- **WHEN** the active binding points at a media asset whose upload or processing status is not ready
- **THEN** teacher detail MAY show the binding with a processing/unready state
- **AND** student-facing reads MUST NOT expose a playable video until the asset is ready.

### Requirement: Video readiness counts reflect active ready bindings
Catalog tree node summaries SHALL report video readiness from active non-archived bindings and ready media assets rather than binding publication state.

#### Scenario: Point has an active ready video
- **WHEN** a catalog point has one active non-archived binding to a ready media asset
- **THEN** node summaries and validation MUST count the point as having a student-visible video
- **AND** they MUST NOT require `binding_status = published`.

#### Scenario: Point has only archived or unready videos
- **WHEN** a catalog point has no active binding to a ready media asset
- **THEN** node summaries and validation MUST count the point as missing a student-visible video
- **AND** status labels MUST remain accurate for teacher repair workflows.

### Requirement: Catalog point bindings respond to archived media assets
The catalog tree service SHALL archive point video bindings that reference an archived media asset without deleting point content.

#### Scenario: Archived asset has active point bindings
- **WHEN** the catalog domain handles a `media_asset_archived` lifecycle event for a media asset with active point video bindings
- **THEN** it MUST archive every non-archived `experiment_catalog_point_media_bindings` row for that asset
- **AND** it MUST record archive reason metadata including the media asset id and lifecycle event id.

#### Scenario: Binding cleanup affects published points
- **WHEN** archived bindings belonged to published point placements
- **THEN** the affected points MUST remain published if their point content is still published
- **AND** their video readiness MUST be recomputed as missing unless another active ready video binding exists.

#### Scenario: Binding cleanup completes
- **WHEN** catalog point bindings are archived due to media asset archive
- **THEN** the service MUST queue or update derived search/evidence jobs for affected active point placements
- **AND** student detail reads MUST no longer expose the archived media asset for playback.

#### Scenario: Asset archive event is repeated
- **WHEN** the same media asset archive event is handled more than once
- **THEN** binding cleanup MUST be idempotent
- **AND** it MUST NOT create duplicate jobs or corrupt archived binding metadata.

### Requirement: Workbench status filters reveal counted descendants
The teacher catalog workbench SHALL keep chapter status counts, directory descendant aggregates, and tree filter matching aligned for every filterable point state.

#### Scenario: Published filter has counted descendants
- **WHEN** the chapter summary reports one or more `published` points and the teacher activates the `已发布` filter
- **THEN** the tree MUST show matching published points when loaded or their ancestor directories when descendants are not yet loaded
- **AND** it MUST NOT render an empty tree solely because published descendants are hidden under directories.

#### Scenario: Ready or draft filter has counted descendants
- **WHEN** the chapter summary reports one or more ready or draft points and the teacher activates the `待发布` filter
- **THEN** the tree MUST show matching ready or draft points when loaded or their ancestor directories when descendants are not yet loaded
- **AND** the filter result MUST use the same ready/draft definition as the chapter summary count.

#### Scenario: Coarse actionable filter is selected
- **WHEN** the teacher activates a coarse filter such as `待处理`, `缺内容`, `缺视频`, `待发布`, `已发布`, or `同步异常`
- **THEN** the filter MUST be based on structured node status buckets rather than localized text matching
- **AND** directory rows MUST remain visible when they contain matching descendant points.

#### Scenario: Text search and status filters are combined
- **WHEN** the teacher enters at least two search characters and also selects a status filter
- **THEN** text search MUST find nodes using the documented searchable text fields
- **AND** the status filter MUST narrow those search results using the same node status matcher used by the tree.

### Requirement: Student-visible point content has three required peer fields
The point content editor SHALL present student-visible learning content as three required peer fields: experiment principle, phenomenon explanation, and safety note.

#### Scenario: Teacher edits point learning content
- **WHEN** a teacher opens a point's content editor
- **THEN** `教学备注` MUST be presented as teacher-only content outside the student-visible field group
- **AND** `学生可见内容` MUST contain `实验原理`, `现象解释`, and `安全提示` as the required student-facing learning fields.

#### Scenario: Equation mode is used for principle content
- **WHEN** the teacher chooses `化学方程式` mode for `实验原理`
- **THEN** the reaction equation input and preview MUST appear as controls inside the `实验原理` field group
- **AND** `输入反应式` MUST be treated as the equation-mode input label rather than a top-level content category.

#### Scenario: Text mode is used for principle content
- **WHEN** the teacher chooses `文字描述` mode for `实验原理`
- **THEN** the text principle input MUST appear in the same `实验原理` field group
- **AND** `现象解释` and `安全提示` MUST remain peer fields in `学生可见内容`.

### Requirement: Missing-content filters support field facets
The teacher catalog workbench SHALL keep `缺内容` as a coarse workflow filter and additionally offer focused missing-field filters for the required student-visible learning fields.

#### Scenario: Missing principle filter is selected
- **WHEN** the teacher selects `缺内容：实验原理`
- **THEN** the tree or result surface MUST include points missing experiment principle content
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Missing phenomenon filter is selected
- **WHEN** the teacher selects `缺内容：现象解释`
- **THEN** the tree or result surface MUST include points missing phenomenon explanation
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Missing safety filter is selected
- **WHEN** the teacher selects `缺内容：安全提示`
- **THEN** the tree or result surface MUST include points missing safety note
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Coarse missing-content filter is selected
- **WHEN** the teacher selects `缺内容`
- **THEN** the tree or result surface MUST include points missing at least one required student-visible learning field
- **AND** it MUST not require the teacher to pick a specific missing field first.
