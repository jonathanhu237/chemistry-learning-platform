## ADDED Requirements

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

## MODIFIED Requirements

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
