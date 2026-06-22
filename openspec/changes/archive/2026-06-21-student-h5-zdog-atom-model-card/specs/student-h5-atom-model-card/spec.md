## ADDED Requirements

### Requirement: Selected element atom model card
The student H5 facts view SHALL render the selected element as a model-led atom card instead of a static database-style fact grid.

#### Scenario: Selected element model card appears
- **WHEN** a student opens the facts view for a profile that has a selected element
- **THEN** the view MUST show a selected-element atom model card
- **AND** the card MUST preserve the existing element tile identity with atomic number, element symbol, and English element name
- **AND** the card MUST show the selected element's Chinese name or teaching name near the model context
- **AND** the previous primary 2x3 selected-element fact grid MUST NOT remain the main presentation for the selected element

#### Scenario: Student switches selected element
- **WHEN** the student taps another within-family element chip such as `Cl`, `Br`, or `I`
- **THEN** the atom model card MUST update to that element
- **AND** the model card's tile, compact facts, electron configuration, and teaching cues MUST reflect the newly selected element
- **AND** the current family/chapter and facts/experiments switcher state MUST remain unchanged

#### Scenario: Selected element lacks model data
- **WHEN** the selected element is missing required data for the atom visualization
- **THEN** the card MUST still show the element tile and available compact facts
- **AND** the model region MUST show a clear unavailable state instead of crashing, rendering a blank broken canvas, or blocking the facts view

### Requirement: Zdog atom visualization integration
The student H5 atom model card SHALL use the Zdog atom viewer as an internal feature module rather than embedding the standalone prototype app.

#### Scenario: Student web builds with internal viewer
- **WHEN** the student web app is built
- **THEN** the Zdog atom viewer MUST be imported through student-web source modules
- **AND** the implementation MUST NOT require the standalone `C:\Users\38122\Documents\zdog` dev server
- **AND** it MUST NOT iframe `http://127.0.0.1:5199/`, `http://222.200.189.249:5199/`, or any other external prototype URL

#### Scenario: Electron layer mode renders
- **WHEN** the selected element has parseable electron configuration or atomic-number fallback data
- **THEN** the card MUST render an electron-layer model using Zdog canvas rendering
- **AND** the model MUST provide a touch-friendly way to rotate the atom on the canvas
- **AND** the page MUST still allow vertical scrolling outside the canvas region

#### Scenario: Orbital mode renders
- **WHEN** the selected element has parseable valence subshell data
- **THEN** the card MUST provide a `轨道` view or equivalent orbital mode
- **AND** the orbital mode MUST show the selected subshell or automatic valence subshell choice
- **AND** the orbital mode MUST keep orbital controls and spin-box information within the phone viewport width

#### Scenario: Animation lifecycle is controlled
- **WHEN** the model is playing, paused, hidden by browser visibility changes, unmounted, or resized
- **THEN** animation frames, resize observers, and pointer handlers MUST be started and cleaned up predictably
- **AND** hidden or unmounted models MUST NOT continue unnecessary animation loops

### Requirement: Student learning atom data adapter
The student H5 frontend SHALL adapt maintained learning-profile element data into the atom viewer model without relying on prototype `testElements` records.

#### Scenario: Adapter builds viewer element
- **WHEN** a selected `StudentLearningElementBadge` is provided to the atom model card
- **THEN** the adapter MUST build a viewer element using the profile element, periodic metadata, English element name mapping, area color, atomic number, and electron configuration
- **AND** it MUST NOT require a matching element in the standalone prototype's `testElements.ts`

#### Scenario: Adapter derives electron shells
- **WHEN** electron configuration includes noble-gas shorthand or explicit subshells
- **THEN** the adapter MUST derive Bohr shell electron counts from the electron configuration or an explicit fallback
- **AND** it MUST handle common shorthand cores such as `[He]`, `[Ne]`, `[Ar]`, `[Kr]`, and `[Xe]`

#### Scenario: Adapter handles irregular configurations
- **WHEN** an element has an irregular d-block or f-block electron configuration such as `Cr`, `Cu`, or `Fe`
- **THEN** the adapter MUST use the explicit provided electron configuration rather than forcing a naive Aufbau-only distribution
- **AND** the resulting model MUST still render or degrade gracefully

### Requirement: RSC-backed physical fact fields
The student learning profile seed SHALL store curated RSC-style physical facts for active learning elements used by the atom model card.

#### Scenario: Profile element includes physical facts
- **WHEN** an active learning profile element is maintained for the atom model card scope
- **THEN** the seed SHOULD include relative atomic mass, group, period, block, 20°C state, density, electron configuration, and source URL where RSC provides those facts
- **AND** the backend response MUST expose available fields to the student frontend without requiring client-side scraping

#### Scenario: Physical facts are source-attributed
- **WHEN** RSC physical fact data is used for an element
- **THEN** the maintained data MUST include source attribution such as `RSC Periodic Table` and an element-specific RSC URL
- **AND** the UI MAY show a compact source link or source note without making the card read like a citation page

#### Scenario: Teaching facts remain separate
- **WHEN** the card shows common valence, redox tendency, or profile-specific notes
- **THEN** those fields MUST continue to come from maintained teaching profile data
- **AND** the UI MUST NOT imply that RSC authored curriculum-specific simplifications such as common valence sequences

### Requirement: Chinese student visual presentation
The atom model card SHALL use Chinese labels and the student H5 visual system rather than the standalone English dark demo presentation.

#### Scenario: Card labels are localized
- **WHEN** the atom model card is rendered
- **THEN** controls and labels MUST use Chinese text such as `电子层`, `轨道`, `重置视角`, `暂停`, and `播放` where those controls exist
- **AND** scientific notation such as element symbols, electron configurations, orbital labels, and units MAY remain compact scientific notation

#### Scenario: Card matches student H5 styling
- **WHEN** the atom model card is shown inside the facts view
- **THEN** it MUST align with the existing student H5 green paper/card visual language
- **AND** it MUST NOT display the standalone prototype's full dark app shell, test element picker, English title block, or demo-only fact strip

#### Scenario: Compact fact strip replaces large grid
- **WHEN** the card shows physical and teaching facts
- **THEN** it MUST use compact rows, chips, or strips that fit phone viewports
- **AND** it MUST avoid recreating six large selected-element fact cards before the family common-property and experiment task content

### Requirement: Atom model verification
The atom model card SHALL be covered by automated and mobile viewport verification before implementation is considered complete.

#### Scenario: Core student-web checks pass
- **WHEN** implementation is complete
- **THEN** `npm run typecheck --prefix apps/student-web` MUST pass
- **AND** `npm run build --prefix apps/student-web` MUST pass
- **AND** `npm run test:e2e --prefix apps/student-web` MUST pass

#### Scenario: Mobile QA covers model behavior
- **WHEN** mobile viewport QA runs for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST verify the atom model card is visible without horizontal overflow
- **AND** it MUST verify element switching updates the selected element area
- **AND** it MUST verify model mode controls are reachable by touch
- **AND** it SHOULD verify the canvas has nonzero dimensions and is not blank where automation can reasonably inspect it

#### Scenario: OpenSpec validation passes
- **WHEN** the change is ready for review
- **THEN** `openspec validate student-h5-zdog-atom-model-card --strict` MUST pass
