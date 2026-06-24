## ADDED Requirements

### Requirement: Home is experiment-video discovery while learning remains catalog map
The student H5 learning experience SHALL separate home discovery from catalog learning: home is the experiment video discovery stream, while the learning tab remains the textbook/catalog map.

#### Scenario: Student opens home
- **WHEN** an authenticated student opens the home root
- **THEN** the page MUST prioritize experiment video discovery through the home video feed
- **AND** it MUST NOT use the old generic recommended-learning hero and multi-action grid as the primary home experience

#### Scenario: Student wants to locate a known experiment
- **WHEN** the student wants to browse by chapter, element, family, or catalog directory
- **THEN** the app MUST keep that behavior under the learning/catalog surfaces
- **AND** the home feed MUST route into those learning contexts through point detail or explicit search/navigation actions rather than replacing the catalog map

#### Scenario: Assessment recommends weak content later
- **WHEN** assessment logic identifies weak chapters or point nodes
- **THEN** recommendation MAY influence home feed ranking or reasons
- **AND** the catalog tree itself MUST remain a neutral classification model rather than being rewritten as a fixed guided-learning path

