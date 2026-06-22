## ADDED Requirements

### Requirement: Point content autosaves like an online document
The teacher catalog editor SHALL autosave routine point and directory content edits while clearly separating save state from downstream ES/RAG sync state.

#### Scenario: Teacher edits point content
- **WHEN** a teacher changes point title, teaching note, principle mode, reaction equations, text principle, phenomenon explanation, or safety note
- **THEN** the editor MUST autosave the changed content without requiring a persistent `保存点位内容` button
- **AND** the visible save indicator MUST describe backend persistence using states such as `正在保存`, `已保存`, and `保存失败`.

#### Scenario: Teacher edits directory content
- **WHEN** a teacher changes a directory title or teaching note
- **THEN** the editor MUST autosave the changed directory content without requiring a persistent `保存目录内容` button
- **AND** the directory title editing interaction MUST keep the teacher in context rather than opening a separate title-edit window for routine inline edits.

#### Scenario: Autosave succeeds before downstream sync completes
- **WHEN** content is saved to the backend but ES or RAG has not yet consumed the change
- **THEN** the editor MUST still show the content save state as saved
- **AND** ES/RAG status MUST remain in diagnostics or secondary status surfaces rather than being represented as an unsaved content state.

#### Scenario: Autosave fails
- **WHEN** an autosave request fails validation or network persistence
- **THEN** the editor MUST show a save failure state near the edited content
- **AND** it MUST keep the teacher's current unsaved input available for correction or retry.

### Requirement: Autosave copy explains delayed search consumption
The teacher catalog editor SHALL explain that autosaved content and student search consumption are separate lifecycle states.

#### Scenario: Teacher views autosave help or sync diagnostics
- **WHEN** the editor shows helper copy, status details, or diagnostics for autosaved point content
- **THEN** the copy MUST say that routine edits are saved first and then consumed by ES/RAG asynchronously
- **AND** it MUST state the expected ES timing policy: normally after about 30 seconds without further edits, and at least once within about 3 minutes during continuous editing.

#### Scenario: Teacher views a published point after editing
- **WHEN** a published point has saved content changes that have not yet been consumed by ES/RAG
- **THEN** the editor MUST keep the point's publication status visually separate from sync status
- **AND** it MUST NOT imply that the point is unpublished, draft-only, missing video, or missing learning content merely because downstream sync is pending.

#### Scenario: Teacher opens retrieval diagnostics
- **WHEN** the teacher opens point diagnostics from the editor
- **THEN** the diagnostics surface MUST show ES and RAG states as downstream consumption states such as `已同步`, `待同步`, `同步中`, or `失败`
- **AND** it MUST not reuse the content autosave labels as if they were ES/RAG execution results.
