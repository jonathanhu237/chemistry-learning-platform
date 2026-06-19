## MODIFIED Requirements

### Requirement: Chapter learning to assessment handoff
The student H5 learning flow SHALL preserve the existing completion-to-assessment path from experiment point detail by opening assessment detail routes instead of switching the assessment root tab.

#### Scenario: Chapter page does not show completion action
- **WHEN** a student opens the current family or chapter detail page
- **THEN** the page MUST NOT show a generic finish-learning or start-assessment action
- **AND** the page MUST focus on element summary and experiment entry content.

#### Scenario: Student completes point detail learning
- **WHEN** a student opens a point detail from the current family or chapter page and then completes learning
- **THEN** the H5 app MUST preserve the point, experiment, and chapter context needed for learning events, AI context, feedback context, and the existing assessment handoff
- **AND** the app MUST navigate to a second-level assessment session route with the bottom navigation hidden
- **AND** returning through history MUST restore the previous detail or root route rather than forcing the assessment root.

### Requirement: Chapter-local facts and experiments flow
The student H5 learning flow SHALL make the selected family or chapter detail page a lightweight entry surface that shows a simple selected-element summary and real experiment entries, while moving full element-model learning into a dedicated detail route.

#### Scenario: Student enters chapter from periodic table
- **WHEN** a student selects a family/chapter from the periodic-table learning root
- **THEN** the H5 app MUST open that family/chapter as the current learning detail route
- **AND** it MUST show a compact current-element summary rather than the full atom model
- **AND** it MUST show real experiment card entries for the selected chapter/profile below the element summary
- **AND** it MUST NOT show a local `性质通识 / 实验视频` capsule switch
- **AND** the bottom navigation MUST remain hidden because the student is on a detail route.

#### Scenario: Student changes selected element on the chapter page
- **WHEN** a student selects another element within the current chapter/family page
- **THEN** the page MUST update the compact selected-element summary
- **AND** the selected chapter/profile MUST remain unchanged
- **AND** the page MUST NOT navigate to another first-level root tab.

#### Scenario: Student opens element detail
- **WHEN** a student taps the element-detail entry from the compact selected-element summary
- **THEN** the app MUST open a dedicated element detail route for the selected profile and element
- **AND** the element detail page MUST render the full element model and detailed atom/fact controls
- **AND** returning MUST restore the chapter detail page.

#### Scenario: Student opens a point from chapter experiments
- **WHEN** a student selects a real experiment card from the chapter detail page
- **THEN** the app MUST open the existing point detail experience as a second-level point detail route with profile, chapter, experiment, point, and selected element context where available
- **AND** returning from point detail MUST restore the chapter page
- **AND** the app MUST NOT switch to a separate experiment root tab.

#### Scenario: Student views removed property sections
- **WHEN** a student is on the refocused chapter detail page
- **THEN** the page MUST NOT render whole-family/common-property cards such as `全族通性`
- **AND** the page MUST NOT render typical property-section blocks such as `族元素的典型性质`.

## REMOVED Requirements

### Requirement: Local chapter view state
**Reason**: The chapter detail page no longer has a local facts/experiments A/B switch, so preserving per-view local state and scroll positions is obsolete.

**Migration**: Render element summary and experiment entries together on the chapter detail page. Route full element-model interaction to the dedicated element detail page, and route experiment cards to the existing point detail page.
