## ADDED Requirements

### Requirement: Experiments page is a route-level orchestrator
The admin experiments route SHALL keep `ExperimentsPage.tsx` as a route composition owner rather than a monolithic feature implementation.

#### Scenario: Experiments page is inspected
- **WHEN** reviewers inspect `apps/admin-web/src/features/experiments/ExperimentsPage.tsx`
- **THEN** the file MUST primarily compose feature-owned hooks and components
- **AND** experiment list tables, point-content modal internals, video binding modal internals, preview modal internals, and pure request mappers MUST live in explicit child modules.

#### Scenario: Experiments route is opened
- **WHEN** an authenticated admin opens `/experiments`
- **THEN** the route MUST render the same teacher experiment management workflow as before the refactor
- **AND** it MUST preserve existing route semantics, auth guard behavior, and lazy route loading.

### Requirement: Experiment data hooks own query and mutation orchestration
The experiments feature SHALL place React Query calls, mutation functions, and query invalidation behavior in feature-owned hooks.

#### Scenario: Experiment list data is loaded
- **WHEN** the experiments route needs experiment list data
- **THEN** a feature-owned hook MUST request experiment list data through the experiments domain API client
- **AND** query keys and filter-to-query-string behavior MUST remain compatible with the existing page behavior.

#### Scenario: Experiment mutation succeeds
- **WHEN** an experiment create, edit, point-content save, related-link save, video bind, publish, unpublish, delete, or publication mutation succeeds
- **THEN** the feature-owned hook MUST invalidate or refresh the same affected data that the monolithic page refreshed before the refactor
- **AND** user-visible success/error feedback MUST remain compatible.

### Requirement: Point-content editor owns experiment-point learning content workflow
The experiments feature SHALL isolate point learning content editing into a point-content owner.

#### Scenario: Teacher edits point content
- **WHEN** a teacher opens the point-content editor for an experiment video point
- **THEN** the editor MUST show and submit point title, principle mode, chemical equation or text principle, phenomenon explanation, safety note, and related experiment links
- **AND** it MUST preserve the existing validation rule that principle equation and principle text are mutually selected by principle mode.

#### Scenario: Point-content request is built
- **WHEN** point-content form values are submitted
- **THEN** a pure mapper MUST build the API request payload
- **AND** tests MUST cover equation mode, text mode, empty optional fields, related-link targets, relation type, sort order, and hidden related links.

#### Scenario: Point publication state changes
- **WHEN** a teacher publishes, unpublishes, or otherwise changes point-content publication state
- **THEN** the point-content owner or hook MUST call the canonical experiments API client
- **AND** the updated experiment video point data MUST be refreshed without requiring a page reload.

### Requirement: Video binding and preview workflow has explicit ownership
The experiments feature SHALL isolate video resource binding and preview behavior into video-binding owners.

#### Scenario: Teacher binds media to a point
- **WHEN** a teacher selects one or more media assets for a video point
- **THEN** the video-binding owner MUST submit the same binding payload semantics used before the refactor
- **AND** it MUST preserve current publish, unpublish, and delete binding behavior.

#### Scenario: Teacher previews a video resource
- **WHEN** a teacher opens a media preview from the experiments page
- **THEN** the preview owner MUST construct authenticated media file, stream, and thumbnail URLs through canonical media API helpers
- **AND** preview loading and error states MUST remain visible and recoverable.

### Requirement: Experiment list and detail UI owners are separated
The experiments feature SHALL separate list filtering/table display from experiment detail editing.

#### Scenario: Teacher filters experiment list
- **WHEN** the teacher changes keyword, chapter, or status filters
- **THEN** a list/filter owner MUST compute visible rows or query parameters
- **AND** the teacher-visible table columns and edit entry behavior MUST remain compatible.

#### Scenario: Teacher edits experiment basics
- **WHEN** the experiment detail drawer opens
- **THEN** basic information, summary, status, and chapter bindings MUST be edited through a detail owner
- **AND** database identifiers and internal fields MUST remain hidden from the teacher UI.

### Requirement: Experiments split preserves existing tests and adds focused mapper tests
The experiments feature split SHALL be behavior-preserving and test-backed.

#### Scenario: Focused tests run
- **WHEN** admin frontend tests run after the experiments split
- **THEN** tests MUST cover point-content request mapping and related-link request mapping
- **AND** existing experiment filter tests MUST continue to pass or be migrated to the new owner module.

#### Scenario: Admin e2e smoke runs
- **WHEN** `npm run e2e:smoke` runs against the admin frontend root origin
- **THEN** `/experiments` MUST render without login redirection, console errors, failed network requests, or missing route chunks.
