## ADDED Requirements

### Requirement: Home root header uses quick-return chrome
The authenticated student H5 shell SHALL treat the home root logo/search row and its below-header recommendation rail as one quick-return header unit controlled by root scroll direction.

#### Scenario: Home root opens with full header
- **WHEN** an authenticated student opens the home root
- **THEN** the shell MUST render the full home header unit before the video feed
- **AND** the home header unit MUST include the main home row and any header-attached below content such as the recommendation rail.

#### Scenario: Downward feed scroll compresses home header
- **WHEN** the student scrolls downward in the home video feed past the configured root-scroll threshold
- **THEN** the shell MUST be allowed to enter the same compressed chrome state family used by root navigation quick-return behavior
- **AND** the visible home header unit MUST compress or move away as one unit without changing the active home root tab.

#### Scenario: Reverse scroll restores home header
- **WHEN** the student scrolls upward after the home header has compressed
- **THEN** the shell MUST restore the home header unit through the quick-return state
- **AND** returning near the top of the document MUST leave the home header fully visible.

#### Scenario: Detail routes do not inherit home header compression
- **WHEN** the current route is a second-level route such as video-library search, point video detail, AI chat detail, assessment session, assessment report, feedback, chapter, catalog, or element detail
- **THEN** the home header quick-return behavior MUST NOT be applied
- **AND** detail-route top chrome and bottom-navigation visibility MUST continue to follow route-stack rules.
