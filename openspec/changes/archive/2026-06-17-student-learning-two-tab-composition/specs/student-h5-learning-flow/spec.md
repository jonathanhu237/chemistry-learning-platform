## ADDED Requirements

### Requirement: Chapter-local facts and experiments flow
The student H5 learning flow SHALL keep facts/common-property viewing and experiment-point video learning within the same selected family/chapter context.

#### Scenario: Student enters chapter from periodic table
- **WHEN** a student selects a family/chapter from the periodic-table learning entry
- **THEN** the H5 app MUST open that family/chapter as the current learning context
- **AND** it MUST provide local switching between facts/common properties and experiment-point videos without returning to the periodic-table entry

#### Scenario: Student switches views before opening a point
- **WHEN** a student changes between facts and experiments on the chapter page
- **THEN** the selected chapter MUST remain unchanged
- **AND** the selected element SHOULD remain unchanged when the profile contains that element

#### Scenario: Student opens a point from experiments view
- **WHEN** a student selects a point card from the experiment-point video view
- **THEN** the app MUST open the existing point detail route with profile, chapter, experiment, point, active view, and selected element context where available
- **AND** returning from point detail MUST restore the chapter page in a sensible experiments-view context

#### Scenario: Student completes learning
- **WHEN** a student completes learning from the chapter page or point detail
- **THEN** the app MUST continue into the existing post-learning assessment flow
- **AND** the A/B view split MUST NOT bypass learning event recording or assessment eligibility behavior

### Requirement: Local chapter view state
The student H5 app SHALL preserve local chapter view state across A/B switches where feasible.

#### Scenario: Active view is preserved during local interaction
- **WHEN** a student switches to the experiments view and opens or closes local overlays
- **THEN** the app MUST keep the experiments view active unless the student explicitly switches views or leaves the chapter

#### Scenario: Scroll position is restored where feasible
- **WHEN** a student scrolls within the facts view or experiments view and then switches away and back
- **THEN** the app SHOULD restore the prior scroll position for that view where feasible
- **AND** if independent scroll restoration is not reliable, the app MUST at least preserve the active view and selected chapter context
