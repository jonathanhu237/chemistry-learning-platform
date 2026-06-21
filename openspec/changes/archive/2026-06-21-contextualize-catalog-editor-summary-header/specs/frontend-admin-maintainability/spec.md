## ADDED Requirements

### Requirement: Contextual catalog summaries remain feature-local
The admin frontend SHALL implement contextual selected-node summaries inside catalog-tree owned modules and styles using existing catalog detail data.

#### Scenario: Developer changes directory or point summary items
- **WHEN** a developer updates the selected-node summary header for directories or point nodes
- **THEN** the change MUST remain localized to catalog editor components and catalog-tree styles
- **AND** it MUST derive values from existing `CatalogNodeDetail` fields without introducing new API calls.

#### Scenario: Developer verifies contextual summaries
- **WHEN** contextual summary rendering is implemented
- **THEN** focused verification MUST cover at least one directory node and one point node
- **AND** it MUST include automated typecheck, focused tests, or equivalent catalog editor behavior checks.
