## ADDED Requirements

### Requirement: Principle mode switching is autosave-safe
The point content editor SHALL keep experiment-principle mode switching stable while autosave and detail refreshes are in flight.

#### Scenario: Teacher switches to an empty equation mode
- **WHEN** the teacher switches `实验原理` from text mode to `化学方程式` mode and the new equation input is empty
- **THEN** the editor MUST keep `化学方程式` selected immediately
- **AND** autosave MUST be allowed to persist the selected mode as draft content
- **AND** a stale detail refresh MUST NOT revert the editor back to text mode.

#### Scenario: Teacher switches to an empty text mode
- **WHEN** the teacher switches `实验原理` from equation mode to `文字描述` mode and the new text input is empty
- **THEN** the editor MUST keep `文字描述` selected immediately
- **AND** autosave MUST be allowed to persist the selected mode as draft content
- **AND** node status MUST report missing experiment principle rather than reverting the selected mode.

#### Scenario: Existing mode has content
- **WHEN** the teacher attempts to switch away from a non-empty principle mode
- **THEN** the editor MUST ask for explicit confirmation before discarding the inactive-mode content
- **AND** cancelling the confirmation MUST preserve the current mode and content.

#### Scenario: Autosave response arrives out of order
- **WHEN** an older autosave response or invalidation-triggered detail payload returns after a newer principle mode switch
- **THEN** the editor MUST ignore or defer the stale mode value for the active node
- **AND** it MUST not overwrite the teacher's current selected mode.

#### Scenario: Teacher selects a different node
- **WHEN** the selected catalog node changes
- **THEN** pending principle-mode guards MUST reset for the previous node
- **AND** the newly selected node MUST hydrate from its own saved detail normally.

### Requirement: Principle mode remains an input mode under experiment principle
Equation and text principle authoring SHALL remain two input modes for the same required experiment-principle field.

#### Scenario: Equation mode saves
- **WHEN** the teacher saves point content in `化学方程式` mode
- **THEN** the save payload MUST keep equation rows as the active experiment-principle source
- **AND** text-mode principle prose MUST not be required for that save.

#### Scenario: Text mode saves
- **WHEN** the teacher saves point content in `文字描述` mode
- **THEN** the save payload MUST keep principle prose as the active experiment-principle source
- **AND** equation rows MUST not be required for that save.

#### Scenario: Active principle source is empty
- **WHEN** the active principle source for the selected mode is empty
- **THEN** draft save MUST remain possible
- **AND** publication readiness MUST report `缺少实验原理`.
