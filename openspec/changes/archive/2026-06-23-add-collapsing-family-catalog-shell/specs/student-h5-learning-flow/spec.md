## ADDED Requirements

### Requirement: Family catalog navigation keeps context
The student H5 learning flow SHALL keep the selected family/chapter context while navigating catalog directories within that chapter.

#### Scenario: Student opens a root catalog directory
- **WHEN** a student opens a directory from a selected family/chapter page
- **THEN** the app MUST navigate to the directory content while preserving selected profile and chapter context
- **AND** the visible page MUST remain a family catalog shell with the same compact element context header
- **AND** the catalog body MUST update to the selected directory's child entries.

#### Scenario: Student navigates deeper directories
- **WHEN** a student opens a nested directory from another directory inside the family catalog shell
- **THEN** the app MUST preserve the same selected profile context
- **AND** the header MUST continue to represent the original family/chapter rather than the current directory title alone
- **AND** breadcrumbs or path text MAY appear in the catalog body to show the current directory position.

#### Scenario: Student returns through history
- **WHEN** the student returns from a nested directory route
- **THEN** browser or WebView history MUST restore the previous catalog level where possible
- **AND** the selected family context and selected element state SHOULD remain stable when route state allows.
