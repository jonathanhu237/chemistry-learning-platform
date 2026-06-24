## ADDED Requirements

### Requirement: Home feed navigation preserves source context
The student H5 route stack SHALL preserve home source context when students navigate from the home video feed to detail, search, or AI destinations.

#### Scenario: Feed item opens point detail
- **WHEN** a student opens an experiment point from the home feed
- **THEN** the route MUST include home source context such as `from=home`
- **AND** the point detail page MUST remain a second-level learning destination reachable from multiple sources

#### Scenario: Student returns from point detail
- **WHEN** the student returns from a point detail opened from home feed
- **THEN** the app MUST return to the home root
- **AND** the home root MUST still be the active bottom-tab identity

#### Scenario: Feed item opens AI chat
- **WHEN** a student opens AI chat from a feed item
- **THEN** the route MUST include the feed item's learning context
- **AND** returning from AI chat MUST preserve normal route-stack behavior without switching the active root tab unexpectedly

