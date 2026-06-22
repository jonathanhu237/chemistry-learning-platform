## MODIFIED Requirements

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

#### Scenario: Student uses point detail go-test action
- **WHEN** a student taps the fixed go-test action from an experiment point detail page
- **THEN** the H5 app MUST use the same existing assessment handoff semantics for the point's experiment chapter or knowledge context
- **AND** the app MUST NOT require a manually edited point-level test destination.
