## ADDED Requirements

### Requirement: Point-aware weak experiment point display
The admin analytics console SHALL display point-aware weak experiment points when point-aware question attempts are available.

#### Scenario: Teacher opens weak-point analytics
- **WHEN** point-aware attempt data exists for a class
- **THEN** the console SHALL show weak experiment video points with experiment identity, attempt count, incorrect count, and incorrect rate
- **AND** it SHALL keep legacy question/KP weak-point rows available as secondary context.

#### Scenario: Teacher reviews a weak experiment point
- **WHEN** selected wrong-option diagnostic links are available
- **THEN** the console SHALL show teacher-readable option diagnostic roles and representative question stems
- **AND** it SHALL not overstate a specific misconception for unrelated distractors.

### Requirement: Readable student learning path
The student report section in analytics SHALL present point-aware attempts and weak video points as structured UI instead of raw JSON.

#### Scenario: Teacher selects a student
- **WHEN** the selected student's report loads
- **THEN** the console SHALL show the student's weak experiment video points, recent attempts, and timeline in readable cards or tables
- **AND** it SHALL include point titles and correctness where available.
