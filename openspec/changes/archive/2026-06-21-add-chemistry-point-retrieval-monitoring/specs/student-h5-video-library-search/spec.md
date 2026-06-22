## ADDED Requirements

### Requirement: Chemistry-aware search indexes point placements
The student experiment-video search index SHALL represent published catalog point placements, not only canonical experiment points or generic text snippets.

#### Scenario: Published point placement is indexed
- **WHEN** a catalog point placement is active and its point content is published
- **THEN** the search document MUST include the placement node id, canonical point id, chapter id, catalog path, student-visible title, principle, phenomenon explanation, safety note, related point titles, bound videos, aliases, formulae, reaction features, and searchable text
- **AND** the placement node id MUST be usable as the ES document identity.

#### Scenario: Same experiment appears in multiple directories
- **WHEN** one canonical experiment point has multiple active placements
- **THEN** each searchable placement MUST keep its own catalog path and placement node id
- **AND** the canonical point id MUST allow grouping or deduplication without losing placement-specific context.

#### Scenario: Unpublished or hidden point content exists
- **WHEN** a point placement has draft-only content, unpublished content, archived state, or hidden state
- **THEN** student experiment-video search MUST NOT expose that placement as a searchable result
- **AND** any previously indexed document for that placement MUST be deleted or treated as unavailable through the ES sync job contract.

### Requirement: Directory context can recall point placements
The student experiment-video search SHALL use catalog directories as context, filters, and weak recall evidence for point placements, without making directories the default final result object.

#### Scenario: Query matches a directory title
- **WHEN** a student searches for a chapter, section, or directory phrase
- **THEN** the search system MAY recall point placements under that matching directory context
- **AND** the returned learning results MUST remain point or video actions unless a separate directory-navigation mode is explicitly requested.

#### Scenario: Directory context contributes to ranking
- **WHEN** a point placement matches a query through its catalog path or ancestor directory
- **THEN** ranking MAY use that path match as supporting evidence
- **AND** the path match MUST be weaker than a direct title, strict chemical synonym, formula, or same-equation-row match.

#### Scenario: Chapter filter is applied
- **WHEN** the search request includes a chapter filter
- **THEN** the search system MUST constrain or boost results according to indexed chapter or path metadata
- **AND** it MUST keep canonical grouping semantics intact when the same point exists in more than one chapter.

### Requirement: Multi-route chemistry recall improves ranking
The student experiment-video search SHALL support chemistry-aware recall routes for text, strict synonyms, formulae, equation rows, conditions, phenomena, properties, directory context, and fallback search text.

#### Scenario: Query contains chemical formulae
- **WHEN** a query contains formula-like terms such as `KMnO4`, `H2O2`, `SO2`, or `FeCl3`
- **THEN** the search system MUST normalize the formula terms for exact keyword matching
- **AND** it SHOULD combine those exact matches with text/analyzer matches rather than relying only on generic tokenized search.

#### Scenario: Query contains strict chemical synonyms
- **WHEN** a query contains a reviewed alias such as a Chinese name, English name, common name, Unicode subscript formula, or ASCII formula for the same chemical entity
- **THEN** strict synonym expansion MAY contribute to text search and query normalization
- **AND** title or principle matches from the expanded entity SHOULD rank above broad phenomenon-only matches.

#### Scenario: Query contains multiple chemical entities
- **WHEN** a query contains multiple chemical entities
- **THEN** candidates where the entities appear in the same normalized equation row or participant set SHOULD rank above candidates where the terms only appear separately across unrelated fields
- **AND** the implementation MUST preserve a deterministic fallback when structured equation matching is unavailable.

### Requirement: Student responses hide retrieval internals
Student-facing video-library search SHALL keep result payloads actionable and safe while diagnostics remain teacher-only.

#### Scenario: Student receives search results
- **WHEN** a student search request returns experiment-video results
- **THEN** each result MUST expose only allowed learning metadata such as title, snippet, catalog path, matched videos, and allowed point metadata
- **AND** it MUST NOT expose raw ES DSL, analyzer tokens, dictionary file state, route traces, sync-job payloads, or rank-debug internals.

#### Scenario: Teacher and student query the same term
- **WHEN** a teacher diagnostic and a student search use the same query
- **THEN** the diagnostic MAY show route reasons, scores, analyzer terms, and canonical/placement grouping
- **AND** the student response MUST remain stable and product-facing even if the same backend route contributed to the result.
