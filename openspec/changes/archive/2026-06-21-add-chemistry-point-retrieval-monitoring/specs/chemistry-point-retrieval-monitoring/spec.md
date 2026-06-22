## ADDED Requirements

### Requirement: Intelligent monitoring page covers AI, RAG, ES, and chemistry retrieval
The teacher console SHALL provide a monitoring surface that summarizes AI provider health, RAG/BGE health, Elasticsearch search health, dictionary asset health, and chemistry retrieval readiness.

#### Scenario: Teacher opens global monitoring
- **WHEN** an authenticated teacher opens the intelligent monitoring page
- **THEN** the page MUST show separate status sections for AI provider connectivity, RAG/BGE runtime, ES index health, and chemistry dictionary assets
- **AND** it MUST show the effective backend configuration such as whether search is using Elasticsearch, local fallback, disabled mode, or an unavailable service.

#### Scenario: Monitoring data is partially unavailable
- **WHEN** one monitored subsystem cannot be reached
- **THEN** the page MUST show the failed subsystem and teacher-readable reason
- **AND** it MUST continue rendering the available AI, RAG, ES, and dictionary sections.

#### Scenario: Student accesses monitoring data
- **WHEN** a student calls student-facing APIs or opens student H5 pages
- **THEN** the system MUST NOT expose raw monitoring data, ES internals, dictionary file hashes, generated query diagnostics, job payloads, rerank traces, or analyzer tokens.

### Requirement: Chemistry dictionaries are categorized and inspectable
The monitoring surface SHALL distinguish strict chemical synonyms from reagent/formulation aliases, condition terms, phenomenon terms, property terms, IK custom dictionaries, and stopwords.

#### Scenario: Teacher reviews dictionary assets
- **WHEN** a teacher opens the dictionary monitoring section
- **THEN** the system MUST show each dictionary category, asset path or logical source, line count, missing-file state, and version/hash when available
- **AND** it MUST distinguish application-level dictionaries from ES/IK analyzer assets.

#### Scenario: Strict chemical synonym is displayed
- **WHEN** the system shows a strict chemical synonym group
- **THEN** every term in the group MUST represent the same chemical entity, such as formula notation, Chinese name, common name, English name, or normalized variant
- **AND** observation terms such as `黄色沉淀`, `刺激性气体`, `褪色`, or `分层` MUST NOT be presented as strict synonyms.

#### Scenario: Non-entity chemistry terms are displayed
- **WHEN** the system shows reagent, condition, phenomenon, or property dictionaries
- **THEN** the UI MUST label them as recall or feature terms rather than chemical synonyms
- **AND** query diagnostics MUST show their contribution separately from strict chemical-entity expansion.

### Requirement: Query diagnostics explain normalization and recall routes
The monitoring surface SHALL allow teachers or operators to run a test query and inspect how the system normalizes, expands, recalls, merges, and ranks chemistry point candidates.

#### Scenario: Teacher runs a chemistry query diagnostic
- **WHEN** a teacher submits a diagnostic query such as `H2O2 KMnO4`, `双氧水 高锰酸钾`, `卤素 氧化性`, or `黄色沉淀`
- **THEN** the response MUST show the normalized query, extracted formulae, strict chemical synonym expansion, non-synonym feature terms, and analyzer/token output where available
- **AND** it MUST show candidate counts for each supported recall route.

#### Scenario: Multi-route recall runs
- **WHEN** query diagnostics run against published search content
- **THEN** the system MUST identify candidates from supported routes such as title/text, strict synonyms, formulae, equation rows, conditions, phenomena/properties, directory context, and search-text fallback
- **AND** it MUST show which routes contributed to each final result.

#### Scenario: Final ranking is shown
- **WHEN** query diagnostics return ranked results
- **THEN** each result MUST include placement node id, canonical point id, title, catalog path, rank, score or rank explanation, and matched route reasons
- **AND** equation-aware matches MUST indicate whether query chemical entities co-occurred in the same reaction equation row.

### Requirement: Search results are point placements with canonical grouping
Chemistry retrieval diagnostics SHALL treat the student-searchable result object as a catalog point placement while preserving canonical point identity for grouping and deduplication.

#### Scenario: A point appears in multiple catalog directories
- **WHEN** the same canonical point has multiple active point placements
- **THEN** retrieval diagnostics MUST show the placement-specific catalog path for each indexed document
- **AND** they MUST expose the shared canonical point id so teachers can understand duplicate or grouped results.

#### Scenario: Canonical deduplication is requested
- **WHEN** a diagnostic or search mode requests canonical grouping
- **THEN** the system MUST group results by canonical point id and retain the best-ranked placement as the primary display item
- **AND** it MUST preserve alternate placement paths for inspection rather than discarding them silently.

#### Scenario: Directory context matches a query
- **WHEN** a query primarily matches a directory title or catalog path
- **THEN** the system MAY recall descendant point placements under that directory context
- **AND** final results MUST still be point placements unless a separate directory-navigation result mode is explicitly requested.

### Requirement: Equation-aware retrieval is first class
The search and diagnostic contract SHALL treat reaction-equation content as structured chemistry data rather than only flattened text.

#### Scenario: Equation-mode point is indexed
- **WHEN** a published point uses equation-mode principle content
- **THEN** the search document MUST include normalized equation display text and structured chemistry fields such as formulae, reactants, products, participants, equation-row text, reaction features, annotation terms, and condition tags when available
- **AND** the original teacher-entered raw equation text MUST remain available for authoring diagnostics.

#### Scenario: Query names multiple chemicals
- **WHEN** a query contains or expands to multiple chemical entities
- **THEN** equation-aware recall MUST prefer candidates where those entities appear in the same equation row or participant set over candidates that only match them across unrelated fields
- **AND** diagnostics MUST identify this co-occurrence route.

#### Scenario: Equation parsing is partial
- **WHEN** an equation row cannot be fully parsed or balanced
- **THEN** the system MUST preserve raw text and parser warnings
- **AND** it SHOULD still expose deterministic extracted formulae or fallback text matching where safe.

### Requirement: Monitoring respects outbox and publication semantics
The monitoring surface SHALL describe ES and RAG state as eventually consistent, job-backed state rather than immediate synchronous persistence.

#### Scenario: Draft point content is saved
- **WHEN** a teacher saves point content as draft or edits student-searchable content before publication
- **THEN** monitoring MUST show that student ES search is expected to delete or hide the affected active placements
- **AND** it MUST NOT present draft content as synced student-searchable ES content.

#### Scenario: Point content is published
- **WHEN** a teacher publishes valid point content
- **THEN** monitoring MUST show pending, running, synced, failed, disabled, or unavailable ES state for each affected placement
- **AND** it MUST provide retry or refresh affordances only through controlled job actions.

#### Scenario: Directory context changes
- **WHEN** a directory title, path, movement, or subtree publication state changes
- **THEN** monitoring MUST account for affected descendant point placements because catalog path contributes to point search documents
- **AND** it MUST show that reindexing is driven by queued point jobs.

### Requirement: Monitoring preserves teacher-only boundaries
Raw retrieval diagnostics SHALL remain teacher/operator-only and SHALL not alter student-facing result contracts.

#### Scenario: Student searches the video library
- **WHEN** a student performs experiment-video search
- **THEN** the response MUST return typed, actionable learning results and allowed display metadata
- **AND** it MUST NOT include ES DSL, analyzer output, route internals, raw dictionary asset data, or rerank/debug traces.

#### Scenario: Teacher copies diagnostic data
- **WHEN** a teacher inspects or copies monitoring diagnostics
- **THEN** the UI MUST label the data as operational or authoring diagnostics
- **AND** it MUST distinguish student-visible point content from teacher-only notes, search internals, and evidence internals.
