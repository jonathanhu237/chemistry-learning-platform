## ADDED Requirements

### Requirement: Compact bottom navigation preserves root route identity
The authenticated student H5 route stack SHALL preserve the existing five root destinations and route ownership while allowing the centered Atom destination to use a visually elevated branded treatment.

#### Scenario: Root order and route targets remain unchanged
- **WHEN** the authenticated student bottom navigation renders after this redesign
- **THEN** it MUST expose root entries in the order `home`, `learn`, `ai`, `assessment`, and `profile`
- **AND** tapping each entry MUST navigate to the same root route as before the redesign
- **AND** the active root destination MUST continue to be derived from the current route.

#### Scenario: Atom is visual emphasis, not a new action route
- **WHEN** the centered Atom control is tapped
- **THEN** it MUST navigate to the existing `ai` root route
- **AND** it MUST NOT create a new publish/action route, overlay-only action, or contextual `/ai/chat` session by default
- **AND** contextual `/ai/chat` sessions opened from other pages MUST keep their existing detail-route behavior.

#### Scenario: Detail route hidden-navigation contract remains unchanged
- **WHEN** the current route is any non-tab task, collection, or detail route
- **THEN** the compact bottom navigation MUST remain hidden
- **AND** visual changes to root navigation MUST NOT promote any detail route into a root tab or introduce a new intermediate route category.
