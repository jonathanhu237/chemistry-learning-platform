## MODIFIED Requirements

### Requirement: Left tree and right editor workspace
The teacher admin console SHALL provide a catalog authoring workspace with a navigable tree on the left and the selected node editor on the right.

#### Scenario: Teacher opens catalog management
- **WHEN** a teacher opens experiment catalog management
- **THEN** the page MUST show chapter selection and a tree of catalog nodes for the selected chapter
- **AND** selecting a node MUST open its editor without leaving the workspace.

#### Scenario: Teacher searches the tree
- **WHEN** a teacher searches by node title, alias, reagent, point text, teacher note, or legacy code
- **THEN** the workspace MUST show matching nodes in a search overlay anchored to the tree search input
- **AND** the overlay MUST provide enough breadcrumb or ancestor context for each result
- **AND** the overlay MUST NOT push the catalog tree downward or become a second in-flow tree.

#### Scenario: Teacher selects a search result
- **WHEN** a teacher selects a result from the search overlay
- **THEN** the workspace MUST reveal the matching node in the existing catalog tree with enough ancestors expanded to preserve context
- **AND** selecting the result MUST focus the matching node in the editor.

#### Scenario: Search overlay is dismissed
- **WHEN** the teacher clears the query, changes chapter, presses Escape, clicks outside the overlay, or selects a result
- **THEN** the search overlay MUST close or reset appropriately
- **AND** the underlying tree layout, scroll container, and selected editor state MUST remain stable.
