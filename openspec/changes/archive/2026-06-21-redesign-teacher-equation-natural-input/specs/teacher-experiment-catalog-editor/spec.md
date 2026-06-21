## ADDED Requirements

### Requirement: Natural equation editor in point content form
The teacher catalog editor SHALL use a natural multiline equation editor as the default UI for point content whose principle mode is chemical equation.

#### Scenario: Teacher opens equation principle mode
- **WHEN** a teacher selects chemical equation principle mode
- **THEN** the editor MUST show one primary multiline input for reaction equations
- **AND** the editor MUST explain in Chinese that each non-empty line is treated as one reaction.

#### Scenario: Teacher types naturally
- **WHEN** a teacher types or pastes reaction text such as `CL2+H2=HCL` or `Cl2 + 2KBr -> 2KCl + Br2`
- **THEN** the editor MUST keep focus in the text input
- **AND** it MUST show backend preview feedback without requiring the teacher to click common-symbol controls.

#### Scenario: Teacher has multiple reactions
- **WHEN** the point requires multiple reaction equations
- **THEN** the teacher MUST be able to enter them as separate lines in the same input
- **AND** the UI MUST show corresponding preview results in the same line order.

#### Scenario: Preview results are shown
- **WHEN** backend preview returns normalized or suggested equations
- **THEN** the editor MUST show a compact "系统理解为" preview area below the text input
- **AND** it MUST include correction warnings, balance suggestions, and invalid-line explanations in Chinese.

#### Scenario: Teacher accepts a suggestion
- **WHEN** the preview presents a corrected or balanced candidate
- **THEN** the editor MUST provide an explicit "采用" action
- **AND** accepting the suggestion MUST update the multiline input so the teacher remains in control of the saved raw text.

#### Scenario: Common symbols are available
- **WHEN** the editor offers chemistry symbols or snippets
- **THEN** those controls MUST be secondary to keyboard input
- **AND** they MUST NOT appear as the main interaction model for authoring equations.

#### Scenario: AI assistance is available
- **WHEN** AI equation assistance is configured and healthy
- **THEN** the editor MAY show explicit actions such as "AI 修正" or "AI 生成反应式"
- **AND** AI candidates MUST be shown as drafts requiring teacher acceptance before insertion.

#### Scenario: AI assistance is unavailable
- **WHEN** AI equation assistance is unavailable
- **THEN** the editor MUST still support natural input, deterministic preview, save, and publication validation
- **AND** it MUST NOT make AI a required step for equation authoring.

#### Scenario: Existing saved equations are loaded
- **WHEN** a point with existing reaction equation rows is opened
- **THEN** the editor MUST hydrate the multiline input from stored raw equation rows in display order
- **AND** the backend-normalized records MUST remain available for preview, save, AI, ES, and RAG consumers.
