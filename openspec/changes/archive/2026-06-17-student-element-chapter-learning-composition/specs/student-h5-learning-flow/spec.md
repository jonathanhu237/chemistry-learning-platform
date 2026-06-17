## ADDED Requirements

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning entry that hands off to one current family or chapter learning page.

#### Scenario: Student chooses a family from the periodic table
- **WHEN** a student selects a family, group, or chapter from the periodic-table learning entry
- **THEN** the H5 app MUST open the corresponding current family or chapter learning page
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the student MUST be able to return to the periodic-table entry or switch chapter through a secondary navigation affordance.

#### Scenario: Existing recommendation is used as fallback
- **WHEN** a student reaches learning without choosing a family or chapter explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as a current chapter page, not as a sibling-family selector.

### Requirement: Chapter learning to assessment handoff
The student H5 learning flow SHALL preserve the existing completion-to-assessment path from the current family or chapter page and from experiment point detail.

#### Scenario: Student completes chapter learning
- **WHEN** a student completes learning from the current family or chapter page
- **THEN** the H5 app MUST start the existing post-learning assessment flow
- **AND** the assessment context MUST remain compatible with the current experiment-point and question-bank behavior.

#### Scenario: Student completes point detail learning
- **WHEN** a student opens a point detail from the current family or chapter page and then completes learning
- **THEN** the H5 app MUST preserve the point, experiment, and chapter context needed for learning events, AI context, feedback context, and the existing assessment handoff.
