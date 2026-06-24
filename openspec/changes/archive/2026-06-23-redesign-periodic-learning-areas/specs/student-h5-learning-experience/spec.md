## ADDED Requirements

### Requirement: Learning root separates periodic selection from smart recommendation
The student H5 learning root SHALL present the periodic table as the primary chapter-selection tool and show recommendation guidance as a separate smart card below it.

#### Scenario: Student opens learning root
- **WHEN** a student opens the `学习` root
- **THEN** the upper learning area MUST render a periodic-table selection card focused on area and element selection
- **AND** the lower learning area MUST render a smart recommendation or continue-learning card when a recommended profile exists
- **AND** the lower card MUST provide a clear action to enter the recommended chapter or area.
- **AND** the periodic-table selector MUST NOT default to a selected area, selected element, or recommendation-derived focus state.

#### Scenario: Recommendation does not decorate the periodic table
- **WHEN** the learning root has a recommended profile
- **THEN** the periodic-table legend MUST NOT show yellow recommendation badges
- **AND** periodic-table element cells MUST NOT show gold recommendation outlines
- **AND** recommendation text such as `推荐学习` MUST live in the separate smart recommendation card rather than inside the periodic-table selector.

## MODIFIED Requirements

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, separate recommended guidance, selected-area route navigation, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as separate guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the recommendation MUST be shown through a separate smart recommendation card on the learning root
- **AND** the periodic-table area controls and element cells MUST remain pure selection affordances
- **AND** the recommendation MUST NOT render as a selected, active, current chapter, inline chapter list, area badge, or element-cell gold outline before the student opens a detail route.

#### Scenario: Student opens a selected area
- **WHEN** the student taps an area control or an element cell from the periodic-table learning root
- **THEN** the H5 app MUST navigate to a selected-area second-level route for that area
- **AND** the learning root MUST NOT render the selected area's chapter list inline
- **AND** the selected area MAY be visually distinguishable as navigation feedback without turning the root into a list page or recommendation surface.

#### Scenario: Student views selected-area chapter list
- **WHEN** the selected-area route is open
- **THEN** the page title MUST be the selected area label such as `p区元素`
- **AND** the page body MUST show only the chapter list filtered to that area
- **AND** the page body MUST NOT repeat a `当前选区` header, count badge, recommendation badge, or separate recommendation card
- **AND** the bottom navigation MUST remain hidden because the selected-area route is a detail route.

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card from the selected-area route
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page.

#### Scenario: Learning root periodic table is pure navigation
- **WHEN** the learning root periodic-table entry is rendered
- **THEN** all visible element cells MUST show their element symbol without requiring a selected area or matching profile symbol
- **AND** area legend buttons and element cells MUST NOT render a default selected, muted, learnable, or focused visual state
- **AND** tapping an area legend button or element cell MUST navigate to the corresponding area route.

#### Scenario: Hydrogen is its own student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** the hydrogen cell MUST map to a dedicated `氢元素` learning area route
- **AND** the selected-area page MUST show matching learning profiles such as CH22 where hydrogen is taught
- **AND** the student entry MUST NOT expose `氢和稀有气体` as a combined area.

#### Scenario: Noble gases are shown through p area
- **WHEN** the student uses the periodic-table entry
- **THEN** group 18 noble-gas cells MUST map to `p区元素`
- **AND** selecting a noble-gas cell MUST open the p-area selected-area route
- **AND** the CH22 learning profile MUST include He, Ne, Ar, Kr, Xe, Rn, and Og so the p-area noble-gas column does not render blank cells
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to p or hydrogen.

#### Scenario: f area is open to students
- **WHEN** the student uses the periodic-table entry
- **THEN** the `f区元素` area MUST be available when the CH21 student learning profile exists
- **AND** selecting an f-block cell MUST open the f selected-area route
- **AND** the selected-area page MUST show the CH21 f-block chapter entry.
