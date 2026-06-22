## ADDED Requirements

### Requirement: Modern catalog tree drag movement
The teacher catalog editor SHALL make node movement behave like a modern file-directory tree, with continuous drag feedback, navigable drop targets, immediate visible updates, and reliable reconciliation after persistence.

#### Scenario: Teacher starts dragging a catalog node
- **WHEN** a teacher starts dragging a directory or point node in the left catalog tree
- **THEN** the dragged source row MUST enter a visible dragging state
- **AND** a drag preview MUST follow the pointer
- **AND** the preview MUST identify the moved item using the node icon and title when a single node is dragged.

#### Scenario: Teacher drags over reorder positions
- **WHEN** a teacher drags a node over a valid same-level or cross-level reorder position
- **THEN** the tree MUST show a visible insertion indicator at the exact before-or-after position that will be used on drop
- **AND** the indicator MUST be visually distinct from normal hover and selection states.

#### Scenario: Teacher drags over a directory target
- **WHEN** a teacher drags a node over a valid directory target for moving into that directory
- **THEN** the directory row MUST show a visible drop-target state that communicates the node will be placed inside that directory
- **AND** point rows MUST NOT appear as valid parent drop targets.

#### Scenario: Collapsed directory expands while dragging
- **WHEN** a teacher holds a dragged node over a valid collapsed directory drop target for approximately 500 milliseconds
- **THEN** the directory MUST expand without requiring the teacher to release the mouse
- **AND** unloaded directory children MUST be loaded so the teacher can continue navigating into the destination before dropping
- **AND** the directory MUST remain expanded after the drag completes.

#### Scenario: Teacher drops a valid reorder
- **WHEN** a teacher drops a node into a valid position within the same parent
- **THEN** the visible tree order MUST update immediately without requiring manual refresh
- **AND** the system MUST persist sibling display order
- **AND** the refreshed server order MUST keep the same result after reconciliation.

#### Scenario: Teacher drops a valid move into another parent
- **WHEN** a teacher drops a node into another valid directory parent or the chapter root
- **THEN** the node MUST immediately disappear from the visible source list when the source is loaded
- **AND** the node MUST appear in the visible destination list when the destination is loaded or opened
- **AND** the selected node and editor context MUST remain on the moved node where practical
- **AND** source and destination branches MUST refresh after persistence so stale lazy-loaded children are not shown.

#### Scenario: Move persistence fails
- **WHEN** the server rejects or fails a move or reorder after the tree performed an optimistic update
- **THEN** the tree MUST restore the previous visible ordering and parent placement
- **AND** the teacher MUST see a controlled error message
- **AND** the selected node MUST NOT be lost.

#### Scenario: Teacher attempts an invalid drop
- **WHEN** a teacher drags a node over a point node, a descendant of itself, or an unsupported cross-chapter target
- **THEN** the tree MUST prevent the drop from persisting
- **AND** the visual feedback MUST NOT imply that the target is valid
- **AND** a controlled warning MUST explain why the drop is unavailable when the teacher releases the node.
