## ADDED Requirements

### Requirement: Elasticsearch IK service for video-library search
The platform SHALL provide Elasticsearch or an Elasticsearch-compatible service with IK analyzer support as the required production search backend for student experiment video-library search.

#### Scenario: Production-like stack starts
- **WHEN** the application stack is started in production-like mode
- **THEN** an Elasticsearch-compatible search service with IK analysis support MUST be configured and health-checked
- **AND** the video-library search backend MUST use that service rather than the deterministic local fallback.

#### Scenario: Search service is missing in production
- **WHEN** production readiness validation runs without a healthy configured ES/IK service
- **THEN** validation MUST fail with an actionable message
- **AND** the failure MUST identify the missing service, index, or analyzer condition.

#### Scenario: Local test fallback is configured
- **WHEN** tests or explicit local development configuration enable deterministic fallback
- **THEN** the backend MAY use local metadata search for isolated tests
- **AND** that fallback MUST be documented as non-production behavior.

### Requirement: Point-centered search document projection
The video-library search index SHALL represent published student-visible experiment points as searchable documents.

#### Scenario: Point content is published
- **WHEN** teacher-authored point learning content is published for a student-visible point
- **THEN** the system MUST create or update a search document for that point
- **AND** the document MUST include stable route target fields such as experiment id, point key, point title, chapter context, and result type.

#### Scenario: Point content is unpublished or archived
- **WHEN** point content is unpublished, archived, deleted, or its parent experiment becomes unavailable
- **THEN** the system MUST remove or deactivate the corresponding search document
- **AND** student video-library search MUST NOT return that point as an active result.

#### Scenario: Video availability changes
- **WHEN** a point's published video binding is added, unpublished, removed, or becomes unready
- **THEN** the search document MUST update video availability fields
- **AND** search results MUST avoid exposing unready or unpublished media as playable resources.

### Requirement: Chemistry-aware index fields
The search projection SHALL include chemistry-specific fields derived from teacher-authored point content.

#### Scenario: Equation-mode principle is indexed
- **WHEN** a published point has an equation-mode principle
- **THEN** the index builder MUST preserve the original equation for display/search snippets
- **AND** it MUST derive normalized formula chemicals, chemical aliases, and reaction feature tags where deterministic extraction is available.

#### Scenario: Text-mode principle is indexed
- **WHEN** a published point has a text-mode principle
- **THEN** the index builder MUST index the text principle with IK-compatible Chinese analysis
- **AND** it MUST still derive formula, alias, or reaction feature fields from any deterministic chemistry tokens found in the content.

#### Scenario: Reaction symbols are present
- **WHEN** the principle equation contains symbols such as `↑`, `↓`, `Δ`, or heat words
- **THEN** the index builder MUST derive matching reaction feature tags such as gas generation, precipitation, or heating
- **AND** these tags MUST be searchable with higher weight than generic body text.

#### Scenario: Chemical aliases are known
- **WHEN** a point contains a formula or alias present in the chemical dictionary
- **THEN** the search document MUST include the normalized formula and aliases
- **AND** searches for either the formula or common name MUST be able to retrieve the point.

### Requirement: IK mapping, synonyms, and stopwords
The search backend SHALL define and apply analyzer configuration suited for Chinese chemistry search.

#### Scenario: Index is bootstrapped
- **WHEN** the video-library search index is created or rebuilt
- **THEN** the backend MUST apply an ES mapping with IK analyzer support for Chinese text fields
- **AND** it MUST include chemistry normalization for common Unicode subscript/superscript forms where supported by the index settings or preprocessing pipeline.

#### Scenario: Domain stopwords are configured
- **WHEN** text is indexed or queried
- **THEN** high-frequency chemistry workflow words such as experiment, reaction, phenomenon, generate, observe, add, and drip MUST have reduced retrieval impact
- **AND** content-bearing chemistry terms, formulas, colors, gases, precipitates, and reagents MUST remain searchable.

#### Scenario: Formula fields are searched
- **WHEN** the user searches for formula-like input such as `hcl`, `HCl`, `Na2S2O3`, or `S₂O₃²⁻`
- **THEN** the query processing MUST normalize the input enough to match indexed formula fields
- **AND** it MUST not depend solely on Chinese word segmentation.

### Requirement: Search synchronization after admin edits
The system SHALL synchronize video-library search documents from PostgreSQL point content changes.

#### Scenario: Teacher publishes an edit
- **WHEN** a teacher publishes new or updated point learning content
- **THEN** the backend MUST write PostgreSQL as the fact source
- **AND** it MUST update, or reliably queue an update for, the corresponding search document after the database commit.

#### Scenario: Index update fails
- **WHEN** PostgreSQL save succeeds but ES indexing fails
- **THEN** the system MUST retain the saved content
- **AND** it MUST record a retryable index status that admin or maintenance tooling can inspect and recover.

#### Scenario: Rebuild command runs
- **WHEN** a maintainer runs the video-library search index rebuild command
- **THEN** the system MUST rebuild the index from published PostgreSQL point content and student-visible video bindings
- **AND** it MUST not read AI point evidence rows as body content for search documents.

### Requirement: Video-library query uses point projection
Student video-library search SHALL query the point-centered search projection and return typed actionable results.

#### Scenario: Student searches by phenomenon
- **WHEN** a student searches for a phenomenon such as gas generation, precipitate, color change, layer color, or fading
- **THEN** the backend MUST search published point documents and return matching result groups
- **AND** each result MUST include a supported route target or be omitted.

#### Scenario: Student searches by reagent or formula alias
- **WHEN** a student searches by reagent formula, common name, or alias
- **THEN** the backend MUST match normalized chemistry fields where available
- **AND** results MUST prioritize point documents whose principle, phenomenon explanation, or title contains the matching chemistry context.

#### Scenario: Hidden content exists
- **WHEN** draft point content, unpublished videos, archived experiments, teacher-only metadata, or AI evidence-only point bindings exist
- **THEN** the video-library search response MUST NOT expose them as active student results.
