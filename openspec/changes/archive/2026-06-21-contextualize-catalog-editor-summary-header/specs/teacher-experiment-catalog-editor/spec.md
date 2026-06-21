## ADDED Requirements

### Requirement: Selected-node summary adapts to catalog node purpose
The teacher catalog editor SHALL adapt the selected-node summary header to the selected node's purpose instead of rendering the same fixed metric blocks for directories and point nodes.

#### Scenario: Teacher selects a directory node
- **WHEN** a teacher selects a directory node
- **THEN** the summary header MUST identify it with a directory icon or equivalent visual cue
- **AND** it MUST emphasize structure and subtree readiness, such as child composition and publication-check state, rather than a large textual `目录` metric.

#### Scenario: Teacher selects a point node
- **WHEN** a teacher selects a point-capable node
- **THEN** the summary header MUST identify it with an experiment or point icon or equivalent visual cue
- **AND** it MUST emphasize learning-content, video, student-card, related-experiment, and publication-check readiness rather than generic structure metrics.

### Requirement: Summary header avoids low-value filler fields
The teacher catalog editor SHALL avoid promoting redundant or low-actionability metadata to first-class summary tiles.

#### Scenario: Counts overlap for a directory
- **WHEN** direct child count and descendant point count do not provide meaningfully separate decisions
- **THEN** the header MUST merge, suppress, or subordinate one of the counts
- **AND** it MUST not render duplicate-looking count blocks solely to fill a fixed grid.

#### Scenario: A selected node has no blocking issues
- **WHEN** publication checks pass and required resources are complete
- **THEN** the header MUST keep the healthy state visible but visually calm
- **AND** it MUST reserve stronger emphasis for missing or blocking states.

#### Scenario: A selected node has missing content or resources
- **WHEN** learning content, video binding, student card setup, or publication checks are incomplete
- **THEN** the header MUST make the incomplete area easy to spot before the teacher opens deeper editor panels.
