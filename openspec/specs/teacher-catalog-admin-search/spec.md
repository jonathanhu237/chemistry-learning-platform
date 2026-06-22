# teacher-catalog-admin-search Specification

## Purpose
TBD - created by archiving change add-teacher-catalog-es-search-overlay. Update Purpose after archive.
## Requirements
### Requirement: Teacher catalog search uses a separate admin Elasticsearch projection
The system SHALL maintain teacher catalog search as an admin-only Elasticsearch projection separate from the student video-library search index.

#### Scenario: Teacher search index is built
- **WHEN** the teacher catalog search projection is bootstrapped or rebuilt
- **THEN** it MUST create or update a teacher/admin index with its own index name and mapping version
- **AND** it MUST NOT write teacher search documents into the student video-library index.

#### Scenario: Student search index is built
- **WHEN** the student video-library search projection is bootstrapped or rebuilt
- **THEN** student documents MUST remain limited to published student-visible placement documents
- **AND** they MUST NOT include teacher-only notes, draft-only content, unpublished content, legacy admin identifiers, or admin status diagnostics introduced for teacher search.

#### Scenario: Teacher and student query the same chemical term
- **WHEN** a teacher and a student search for the same reagent, formula, or alias
- **THEN** the teacher query MAY return draft, unpublished, directory, teacher-note, or legacy-id matches from the teacher index
- **AND** the student query MUST continue to return only student-visible learning results from the student index.

### Requirement: Teacher search documents cover admin catalog authoring context
The teacher catalog search index SHALL represent the searchable authoring context for both directory nodes and point placements.

#### Scenario: Directory node is indexed for teacher search
- **WHEN** an active directory node is indexed for teacher search
- **THEN** the document MUST include the directory node id, node kind, chapter id, parent id, title, breadcrumb/path context, teacher note where present, publication/archive flags, and directory status facets needed by teacher filters
- **AND** the document MUST NOT pretend the directory owns point-only learning content, video binding, related links, AI evidence, or canonical point identity.

#### Scenario: Point placement is indexed for teacher search
- **WHEN** an active point placement is indexed for teacher search
- **THEN** the document MUST include placement node id, canonical point id, node kind, chapter id, breadcrumb/path context, point title, teacher-only note, draft or published learning content, legacy identifiers, publication/archive flags, status facets, and chemistry-derived recall fields
- **AND** it MUST preserve placement context separately from shared canonical point identity.

#### Scenario: Chemical equation content is indexed
- **WHEN** a point has chemical-equation principle content
- **THEN** the teacher search document MUST include searchable raw and normalized equation text
- **AND** it MUST include structured fields for formulae, formula pairs, reactants, products, participants, aliases, strict aliases, and row-level annotation text when available.

#### Scenario: Text principle content is indexed
- **WHEN** a point uses text principle mode
- **THEN** the teacher search document MUST include the text principle as teacher-searchable content
- **AND** it MUST NOT synthesize formula fields that are not derived by the backend chemistry extraction pipeline.

### Requirement: Teacher search query is chemistry-aware and status-filtered
Teacher catalog search SHALL combine Elasticsearch text analysis, chemistry synonym recall, formula-aware routes, and catalog status filtering.

#### Scenario: Query contains a chemical alias
- **WHEN** a teacher searches with a reviewed chemical alias, common name, formula spelling, or synonym
- **THEN** the Elasticsearch query MUST use the chemistry search analyzer and synonym graph behavior where configured
- **AND** it MUST be able to recall matching title, content, equation, alias, or path documents from the teacher index.

#### Scenario: Query contains a formula
- **WHEN** a teacher searches for a formula-like term such as `Na2S2O3`, `SO3^2-`, `HCl`, or `FeCl3`
- **THEN** the backend MUST normalize query formulae for structured keyword routes
- **AND** it SHOULD rank same-row or same-participant matches above broad text-only matches when the structured fields are available.

#### Scenario: Status filter is active
- **WHEN** the teacher searches while a catalog status filter such as missing content, missing video, draft, published, or sync attention is active
- **THEN** the backend search request MUST apply the filter before returning top results
- **AND** the result set MUST follow the same status model used by tree rows and chapter counts.

#### Scenario: Chapter filter is active
- **WHEN** the teacher searches inside a selected chapter
- **THEN** search results MUST be constrained to that chapter's catalog nodes
- **AND** the backend MUST NOT return same-title nodes from other chapters unless a future explicit cross-chapter search mode is requested.

### Requirement: Teacher search sync is independent from student search sync
Catalog changes SHALL fan out to independent teacher and student search projection jobs instead of using one coupled job that writes both indexes.

#### Scenario: Point content is saved as draft
- **WHEN** a teacher saves draft point content
- **THEN** the system MAY enqueue or update a teacher search projection job for that point placement or canonical point context
- **AND** it MUST NOT upsert that draft content into the student video-library index.

#### Scenario: Point content is published
- **WHEN** a point placement becomes student-visible with published content
- **THEN** the system MAY enqueue both a student search projection job and a teacher search projection job
- **AND** each projection target MUST have independent retry state, error state, and diagnostics.

#### Scenario: Teacher search indexing fails
- **WHEN** a teacher search projection job fails after a catalog change
- **THEN** the failure MUST be recorded for teacher search diagnostics or retry
- **AND** it MUST NOT mark the corresponding student video-library projection as failed when the student projection succeeded or was not applicable.

#### Scenario: Student search indexing fails
- **WHEN** a student video-library projection job fails after a catalog change
- **THEN** the failure MUST remain in student-search projection state
- **AND** it MUST NOT prevent the teacher catalog search document from being indexed or queried when the teacher projection is healthy.

#### Scenario: Directory title changes
- **WHEN** a directory title, path position, archive state, or publication state changes
- **THEN** the system MUST enqueue teacher search refresh work for the directory document and affected descendant teacher-search path context
- **AND** it MUST enqueue student search refresh work only for affected published student-visible descendant placements.

### Requirement: Teacher search exposes explicit backend and fallback metadata
The admin catalog search API SHALL report whether Elasticsearch or a fallback search path answered the query.

#### Scenario: Elasticsearch answers the query
- **WHEN** teacher catalog search successfully queries the teacher Elasticsearch index
- **THEN** the response MUST identify the backend as Elasticsearch or equivalent
- **AND** it MUST indicate that configured synonym and chemistry ES recall were available.

#### Scenario: Elasticsearch is unavailable
- **WHEN** the teacher Elasticsearch index is disabled, unreachable, unhealthy, or query execution fails
- **THEN** the backend MAY use the existing deterministic Postgres search fallback
- **AND** the response MUST identify the backend as a degraded Postgres fallback.

#### Scenario: Fallback search is used
- **WHEN** the frontend receives a fallback teacher search response
- **THEN** it MUST NOT claim that ES synonyms, IK tokenization, or structured ES ranking were used for those results
- **AND** it MAY show restrained copy indicating that limited search is active.

### Requirement: Teacher search results are navigation candidates
Teacher catalog search results SHALL be used to reveal and select catalog nodes, not to replace the authoritative tree.

#### Scenario: Teacher selects a search result
- **WHEN** a teacher selects a search result row
- **THEN** the frontend MUST reveal the result node through the catalog tree state
- **AND** it MUST select the node and open the existing directory or point editor.

#### Scenario: Search result is stale
- **WHEN** a selected search result no longer exists, is archived outside the current view, or is no longer in the selected chapter
- **THEN** the frontend MUST show a controlled stale-result state or refresh prompt
- **AND** it MUST NOT render ES hit data as an editable catalog node.

#### Scenario: Search result row is rendered
- **WHEN** a teacher search result appears in the overlay
- **THEN** the row MUST show the node type, title, breadcrumb path, matched-field label when available, and teacher status marker
- **AND** it MUST NOT expose raw ES DSL, raw analyzer tokens, index internals, or stack traces in the normal row UI.

