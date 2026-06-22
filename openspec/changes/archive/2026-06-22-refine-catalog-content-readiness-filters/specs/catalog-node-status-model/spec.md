## ADDED Requirements

### Requirement: Missing learning fields are structured
The node status model SHALL expose missing learning fields with stable identifiers and teacher-readable labels.

#### Scenario: Point is missing experiment principle only
- **WHEN** a point lacks active experiment principle content but has phenomenon explanation and safety note
- **THEN** `core_readiness.content_fields` MUST be `missing`
- **AND** the status payload MUST identify the missing field with a stable key for experiment principle
- **AND** teacher-facing copy MUST say `缺少实验原理` rather than listing fields that are already complete.

#### Scenario: Point is missing two learning fields
- **WHEN** a point is missing experiment principle and phenomenon explanation but has safety note
- **THEN** the status payload MUST identify only those two missing fields
- **AND** teacher-facing copy MUST say `缺少实验原理、现象解释`.

#### Scenario: Point has no saved learning content
- **WHEN** a point has no saved shared learning content
- **THEN** the status payload MUST identify experiment principle, phenomenon explanation, and safety note as missing
- **AND** the primary state MUST remain `needs_content`.

#### Scenario: Missing-field copy is localized
- **WHEN** the frontend renders node status, tooltips, filter chips, or inline editor guidance
- **THEN** it MUST use the teacher-readable labels from the status contract or an equivalent stable label map
- **AND** it MUST NOT parse localized status sentences to decide which field is missing.

### Requirement: Directory aggregates include filterable state and missing-field counts
Directory node status SHALL expose descendant aggregates that cover every status filter and every missing-content field facet.

#### Scenario: Directory contains published descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `published`
- **THEN** `core_readiness.descendant_status_counts.published` MUST reflect that count
- **AND** the `已发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains ready descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `ready`
- **THEN** `core_readiness.descendant_status_counts.ready` MUST reflect that count
- **AND** the `待发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains draft descendants
- **WHEN** a directory contains one or more descendant points whose primary state is `draft`
- **THEN** `core_readiness.descendant_status_counts.draft` MUST reflect that count
- **AND** the `待发布` filter MUST be able to keep the directory visible.

#### Scenario: Directory contains missing-field descendants
- **WHEN** a directory contains descendant points missing experiment principle, phenomenon explanation, or safety note
- **THEN** directory status MUST expose descendant missing-field counts for each missing field key
- **AND** focused missing-field filters MUST be able to keep the directory visible.

#### Scenario: Directory action count is computed
- **WHEN** a directory has descendant status counts for blocked, needs content, needs video, ready, draft, or sync attention
- **THEN** its descendant action count MUST remain a compact workflow count
- **AND** published descendants MUST NOT increase the action count solely because they are published.

### Requirement: Chapter summary exposes missing-field counts
The chapter tree summary SHALL expose missing-field counts for the required student-visible learning fields.

#### Scenario: Chapter has missing content details
- **WHEN** the chapter summary is requested
- **THEN** it MUST include the existing coarse point status counts
- **AND** it MUST include counts for missing experiment principle, missing phenomenon explanation, and missing safety note.

#### Scenario: Missing-field filter chips are rendered
- **WHEN** the teacher frontend renders focused missing-field filter chips
- **THEN** each chip count MUST come from chapter-level missing-field counts
- **AND** zero-count chips MAY remain visible in a low-emphasis disabled or inactive state but MUST NOT show misleading non-zero values.

### Requirement: Incomplete content guidance is inline and targetable
The teacher content editor SHALL surface missing-content guidance inline with the affected student-visible fields.

#### Scenario: Selected point is missing fields
- **WHEN** the selected point status reports one or more missing learning fields
- **THEN** the content editor MUST show a compact inline warning summary near `学生可见内容`
- **AND** the summary MUST name only the missing fields.

#### Scenario: Teacher activates a missing-field link
- **WHEN** the teacher clicks or keyboard-activates a missing-field name in the inline summary
- **THEN** the editor MUST move focus to the corresponding field or field group
- **AND** it MUST NOT navigate away from the selected point.

#### Scenario: Teacher is typing incomplete content
- **WHEN** the teacher is editing a point with missing content
- **THEN** the inline guidance MUST not block typing, autosave, preview, or mode switching
- **AND** publication validation remains responsible for blocking publish attempts that require complete content.
