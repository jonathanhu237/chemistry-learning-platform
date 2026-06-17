## ADDED Requirements

### Requirement: Mobile learning-entry state cues
The student H5 mobile design system SHALL use distinct visual cues for selected area state, recommended guidance, and chapter navigation entries on the periodic-table learning entry.

#### Scenario: Selected periodic-table area is highlighted
- **WHEN** an area is selected on the periodic-table entry
- **THEN** the selected area's element cells MUST be visually emphasized without relying on heavy dark per-cell borders
- **AND** non-selected area cells MUST remain visible but visually secondary

#### Scenario: Recommended area is visible
- **WHEN** the selected or unselected area matches the recommended profile's area
- **THEN** the periodic-table entry MUST show a compact recommendation cue that names the recommended area
- **AND** the cue MUST NOT replace or obscure the selected-state affordance

#### Scenario: Chapter entry cards remain tappable rows
- **WHEN** chapter cards are shown on a phone viewport
- **THEN** each card MUST read as a tappable navigation row
- **AND** recommendation styling MUST be limited to a label or similarly compact cue
- **AND** the label MUST NOT consume a standalone row that pushes the chapter title down
- **AND** recommendation styling MUST NOT use the same visual treatment as selected cards, active tabs, or pressed controls
