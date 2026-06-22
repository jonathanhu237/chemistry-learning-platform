## ADDED Requirements

### Requirement: Video resource labels are excluded from search semantics
The student experiment-video search SHALL treat the index as a published point library, not as a video resource library.

#### Scenario: Bound video has teacher-only labels
- **WHEN** a published point has a bound ready video with a media asset title, binding title, or original file name
- **THEN** those labels MUST NOT be included in ES searchable fields, local fallback searchable text, diagnostics route matching, or student search snippets
- **AND** queries matching only those labels MUST NOT recall the point.

#### Scenario: Point has a playable video
- **WHEN** a published point has an active ready video binding
- **THEN** the search document MAY include `has_video` and `video_count`
- **AND** those fields MUST be treated only as point readiness/filter signals, not as video semantic content.

#### Scenario: Search hit is rendered
- **WHEN** a student search result is rendered
- **THEN** the result MUST use point title, point snippet, catalog path, and route target from point data
- **AND** it MUST NOT display or depend on video resource title, media asset id, thumbnail path, stream path, or original file name from ES.

## MODIFIED Requirements

### Requirement: Searchable document scope
The video library index SHALL represent student-visible experiment point learning material and searchable chemistry context.

#### Scenario: Experiment video document is indexed
- **WHEN** a student-visible catalog point placement is indexed
- **THEN** the searchable document MUST include stable identifiers needed for routing
- **AND** it MUST include student-facing catalog path, point title, principle, phenomenon explanation, safety note, related point titles, reagents, phenomena, chapter identifiers, element symbols, equations, formula text, and chemistry-derived recall fields when available.
- **AND** it MUST NOT include video resource titles, media asset titles, binding titles, original file names, media asset ids, playback paths, thumbnail paths, upload status, processing status, duplicate-candidate data, or other video resource metadata.

#### Scenario: Hidden content exists
- **WHEN** an experiment point, media resource, learning resource, or catalog placement is draft-only, archived, unpublished, unready, or not visible to students
- **THEN** the index and search response MUST NOT expose it to student H5 search.

#### Scenario: Later transcript data exists
- **WHEN** transcript or ASR segments become available for a published video
- **THEN** the index MUST NOT include those transcript segments unless a future spec explicitly promotes transcripts to student-facing point content
- **AND** transcript hits MUST not be introduced as an implicit side effect of media asset upload.

### Requirement: Chemistry-aware search indexes point placements
The student experiment-video search index SHALL represent published catalog point placements, not raw video resources, generic media rows, canonical-only points, or generic text snippets.

#### Scenario: Published point placement is indexed
- **WHEN** a catalog point placement is active and its point content is published
- **THEN** the search document MUST include the placement node id, canonical point id, chapter id, catalog path, student-visible title, principle, phenomenon explanation, safety note, related point titles, aliases, formulae, reaction features, searchable text, and non-semantic video readiness signals
- **AND** the placement node id MUST be usable as the ES document identity.
- **AND** the document MUST NOT include video resource titles, original file names, media ids, thumbnail paths, stream paths, or video metadata in searchable text or ES source.

#### Scenario: Same experiment appears in multiple directories
- **WHEN** one canonical experiment point has multiple active placements
- **THEN** each searchable placement MUST keep its own catalog path and placement node id
- **AND** the canonical point id MUST allow grouping or deduplication without losing placement-specific context.

#### Scenario: Unpublished or hidden point content exists
- **WHEN** a point placement has draft-only content, unpublished content, archived state, hidden state, or only archived media bindings
- **THEN** student experiment-video search MUST NOT expose hidden point content or archived media resource data as a searchable result
- **AND** any previously indexed document for that placement MUST be deleted or rebuilt through the ES sync job contract.

### Requirement: Student responses hide retrieval internals
Student-facing video-library search SHALL keep result payloads actionable and safe while diagnostics remain teacher-only.

#### Scenario: Student receives search results
- **WHEN** a student search request returns experiment-video results
- **THEN** each result MUST expose only allowed learning metadata such as point title, snippet, catalog path, and allowed point route metadata
- **AND** it MUST NOT expose raw ES DSL, analyzer tokens, dictionary file state, route traces, sync-job payloads, rank-debug internals, media asset ids, video resource titles, original file names, thumbnail paths, or stream paths from ES.

#### Scenario: Teacher and student query the same term
- **WHEN** a teacher diagnostic and a student search use the same query
- **THEN** the diagnostic MAY show route reasons, scores, analyzer terms, and canonical/placement grouping
- **AND** the student response MUST remain stable and product-facing even if the same backend route contributed to the result.
