## MODIFIED Requirements

### Requirement: Teacher-authored point content form
The editor SHALL let teachers maintain point content without requiring AI generation, and chemical equation mode SHALL review adoptable reaction candidates inline as rendered equations.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits a point-capable node
- **THEN** the form MUST provide fields for point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related point links, bound videos, and publication state.
- **AND** the teacher-only note MUST be visually and technically separated from student-facing point knowledge.

#### Scenario: Teacher edits chemical equation principle
- **WHEN** a teacher uses chemical equation mode for point principle content
- **THEN** the editor MUST keep natural multiline input as the editing surface
- **AND** parser and AI review feedback MUST be shown as row-attached rendered reaction candidates rather than separate text-heavy suggestion sections.

#### Scenario: Teacher adopts a rendered equation candidate
- **WHEN** a teacher adopts a system or AI candidate from the chemical equation review
- **THEN** the editor MUST update the relevant multiline input row or append a new row
- **AND** it MUST re-run backend preview before the content can be saved.

#### Scenario: Teacher edits teacher-only note
- **WHEN** a teacher enters remarks, non-experiment knowledge, operational comments, or authoring hints in the teacher-only note field
- **THEN** the editor MUST save the note for teacher/admin reuse
- **AND** the editor MUST indicate that this note is not shown to students and is not part of student video-library search.

#### Scenario: Teacher saves draft content
- **WHEN** required publish fields are incomplete
- **THEN** the system MUST allow draft save
- **AND** it MUST show validation messages explaining what is missing before publication.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes point content
- **THEN** the system MUST validate required fields, update student visibility, and queue search indexing.
- **AND** queued search indexing MUST use student-facing point title and point knowledge rather than the teacher-only note.
