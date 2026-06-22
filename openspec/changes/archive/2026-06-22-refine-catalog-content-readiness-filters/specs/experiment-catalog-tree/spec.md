## ADDED Requirements

### Requirement: Workbench status filters reveal counted descendants
The teacher catalog workbench SHALL keep chapter status counts, directory descendant aggregates, and tree filter matching aligned for every filterable point state.

#### Scenario: Published filter has counted descendants
- **WHEN** the chapter summary reports one or more `published` points and the teacher activates the `已发布` filter
- **THEN** the tree MUST show matching published points when loaded or their ancestor directories when descendants are not yet loaded
- **AND** it MUST NOT render an empty tree solely because published descendants are hidden under directories.

#### Scenario: Ready or draft filter has counted descendants
- **WHEN** the chapter summary reports one or more ready or draft points and the teacher activates the `待发布` filter
- **THEN** the tree MUST show matching ready or draft points when loaded or their ancestor directories when descendants are not yet loaded
- **AND** the filter result MUST use the same ready/draft definition as the chapter summary count.

#### Scenario: Coarse actionable filter is selected
- **WHEN** the teacher activates a coarse filter such as `待处理`, `缺内容`, `缺视频`, `待发布`, `已发布`, or `同步异常`
- **THEN** the filter MUST be based on structured node status buckets rather than localized text matching
- **AND** directory rows MUST remain visible when they contain matching descendant points.

#### Scenario: Text search and status filters are combined
- **WHEN** the teacher enters at least two search characters and also selects a status filter
- **THEN** text search MUST find nodes using the documented searchable text fields
- **AND** the status filter MUST narrow those search results using the same node status matcher used by the tree.

### Requirement: Student-visible point content has three required peer fields
The point content editor SHALL present student-visible learning content as three required peer fields: experiment principle, phenomenon explanation, and safety note.

#### Scenario: Teacher edits point learning content
- **WHEN** a teacher opens a point's content editor
- **THEN** `教学备注` MUST be presented as teacher-only content outside the student-visible field group
- **AND** `学生可见内容` MUST contain `实验原理`, `现象解释`, and `安全提示` as the required student-facing learning fields.

#### Scenario: Equation mode is used for principle content
- **WHEN** the teacher chooses `化学方程式` mode for `实验原理`
- **THEN** the reaction equation input and preview MUST appear as controls inside the `实验原理` field group
- **AND** `输入反应式` MUST be treated as the equation-mode input label rather than a top-level content category.

#### Scenario: Text mode is used for principle content
- **WHEN** the teacher chooses `文字描述` mode for `实验原理`
- **THEN** the text principle input MUST appear in the same `实验原理` field group
- **AND** `现象解释` and `安全提示` MUST remain peer fields in `学生可见内容`.

### Requirement: Missing-content filters support field facets
The teacher catalog workbench SHALL keep `缺内容` as a coarse workflow filter and additionally offer focused missing-field filters for the required student-visible learning fields.

#### Scenario: Missing principle filter is selected
- **WHEN** the teacher selects `缺内容：实验原理`
- **THEN** the tree or result surface MUST include points missing experiment principle content
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Missing phenomenon filter is selected
- **WHEN** the teacher selects `缺内容：现象解释`
- **THEN** the tree or result surface MUST include points missing phenomenon explanation
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Missing safety filter is selected
- **WHEN** the teacher selects `缺内容：安全提示`
- **THEN** the tree or result surface MUST include points missing safety note
- **AND** it MUST include ancestor directories that contain such points.

#### Scenario: Coarse missing-content filter is selected
- **WHEN** the teacher selects `缺内容`
- **THEN** the tree or result surface MUST include points missing at least one required student-visible learning field
- **AND** it MUST not require the teacher to pick a specific missing field first.
