## MODIFIED Requirements

### Requirement: Periodic-table to chapter handoff
The student H5 learning flow SHALL support a periodic-table learning root that hands off to one current family or chapter learning detail page.

#### Scenario: Student chooses a family from the periodic table
- **WHEN** a student selects a family, group, or chapter from the periodic-table learning entry
- **THEN** the H5 app MUST open the corresponding current family or chapter as a second-level chapter learning route
- **AND** the page MUST use the selected profile as the current learning context
- **AND** the bottom navigation MUST be hidden while the chapter learning detail route is visible
- **AND** returning from the detail route MUST restore the learning root and its chapter selection context where feasible.

#### Scenario: Existing recommendation is used as fallback
- **WHEN** a student reaches learning without choosing a family or chapter explicitly
- **THEN** the backend MAY resolve an existing recommendation or default profile
- **AND** the H5 app MUST render that resolved profile as a current chapter detail page only when a detail route is opened
- **AND** the learning root MUST remain an entry, search, and selection surface rather than a sibling-family selector or a hidden default detail page.

### Requirement: Chapter learning to assessment handoff
The student H5 learning flow SHALL preserve the existing completion-to-assessment path from the current family or chapter page and from experiment point detail by opening assessment detail routes instead of switching the assessment root tab.

#### Scenario: Student completes chapter learning
- **WHEN** a student completes learning from the current family or chapter detail page
- **THEN** the H5 app MUST start the existing post-learning assessment flow
- **AND** the assessment context MUST remain compatible with the current experiment-point and question-bank behavior
- **AND** the app MUST navigate to a second-level assessment session route with the bottom navigation hidden
- **AND** the app MUST NOT switch the active root tab to the assessment root as a side effect.

#### Scenario: Student completes point detail learning
- **WHEN** a student opens a point detail from the current family or chapter page and then completes learning
- **THEN** the H5 app MUST preserve the point, experiment, and chapter context needed for learning events, AI context, feedback context, and the existing assessment handoff
- **AND** the app MUST navigate to a second-level assessment session route with the bottom navigation hidden
- **AND** returning through history MUST restore the previous detail or root route rather than forcing the assessment root.

### Requirement: Chapter-local facts and experiments flow
The student H5 learning flow SHALL keep facts/common-property viewing and experiment-point video learning within the same selected family/chapter detail route.

#### Scenario: Student enters chapter from periodic table
- **WHEN** a student selects a family/chapter from the periodic-table learning root
- **THEN** the H5 app MUST open that family/chapter as the current learning detail route
- **AND** it MUST provide local switching between facts/common properties and experiment-point videos without returning to the periodic-table entry
- **AND** the local switch MUST NOT alter the active root tab.

#### Scenario: Student switches views before opening a point
- **WHEN** a student changes between facts and experiments on the chapter detail page
- **THEN** the selected chapter MUST remain unchanged
- **AND** the selected element SHOULD remain unchanged when the profile contains that element
- **AND** the bottom navigation MUST remain hidden because the student is still on a detail route.

#### Scenario: Student opens a point from experiments view
- **WHEN** a student selects a point card from the experiment-point video view
- **THEN** the app MUST open the existing point detail experience as a second-level point detail route with profile, chapter, experiment, point, active view, and selected element context where available
- **AND** returning from point detail MUST restore the chapter page in a sensible experiments-view context
- **AND** the app MUST NOT switch to a separate experiment root tab.

#### Scenario: Student completes learning
- **WHEN** a student completes learning from the chapter page or point detail
- **THEN** the app MUST continue into the existing post-learning assessment flow through a second-level assessment session route
- **AND** the A/B view split MUST NOT bypass learning event recording or assessment eligibility behavior
- **AND** root tab identity MUST remain controlled by bottom navigation, not by the completion action.

## ADDED Requirements

### Requirement: Contextual AI opens shared chat detail
The student H5 learning flow SHALL open contextual AI as the shared AI chat detail page without changing the active root tab.

#### Scenario: Student asks from chapter detail
- **WHEN** a student taps a contextual AI action from a chapter learning detail page
- **THEN** the app MUST open the shared AI chat detail page with chapter context
- **AND** the bottom navigation MUST remain hidden
- **AND** returning MUST restore the chapter learning detail route.

#### Scenario: Student asks from point detail
- **WHEN** a student taps a contextual AI action from an experiment point detail page
- **THEN** the app MUST open the shared AI chat detail page with experiment and point context
- **AND** the bottom navigation MUST remain hidden
- **AND** returning MUST restore the point detail route.
