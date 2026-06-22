## ADDED Requirements

### Requirement: Teacher preview displays inline equation annotations as part of the same row
The teacher catalog editor SHALL render inline annotation text returned by backend preview/save responses as visibly attached to its reaction equation row.

#### Scenario: Preview returns an annotated equation
- **WHEN** backend preview returns a normalized reaction record with both an equation core and annotation text
- **THEN** the editor MUST show the normalized equation and the annotation in the same equation card or row
- **AND** it MUST NOT show the annotation as a separate failed reaction candidate.

#### Scenario: Teacher edits annotated multiline input
- **WHEN** the teacher edits a multiline equation input containing `//` annotations
- **THEN** preview state, validation warnings, and accepted suggestions MUST remain aligned by source line order
- **AND** annotation display MUST update with the same row as its equation core.

### Requirement: Teacher authoring preserves annotation suffixes non-destructively
The teacher catalog editor SHALL preserve raw annotated reaction lines during hydration, editing, preview, save, and AI suggestion application.

#### Scenario: Existing annotated equations are loaded
- **WHEN** a point with saved annotated reaction rows is opened
- **THEN** the editor MUST hydrate the authoring input from stored raw rows including the `//` annotation suffix
- **AND** the teacher MUST be able to save without losing the annotation text.

#### Scenario: AI correction is applied to one equation
- **WHEN** the teacher applies an AI correction that changes only the equation core
- **THEN** the editor MUST keep the existing `//` annotation suffix on that line
- **AND** the resulting line MUST remain one saved reaction row.

#### Scenario: Teacher intentionally edits annotation text
- **WHEN** the teacher edits text after `//`
- **THEN** the editor MUST send the full raw line to backend preview/save
- **AND** backend-derived annotation fields MUST reflect the edited suffix after preview or save.
