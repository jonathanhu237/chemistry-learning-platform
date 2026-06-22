## MODIFIED Requirements

### Requirement: Student experiment point detail
The student H5 app SHALL provide a point detail experience that keeps video learning primary while showing published teacher-authored learning content in a fixed structure.

#### Scenario: Student opens a point detail
- **WHEN** a student opens a related experiment point
- **THEN** the page MUST show the point title, parent experiment context, available video, experiment principle, phenomenon explanation, safety note, related experiment links, go-test action, and learning completion affordance
- **AND** the experiment principle MUST render from the point's published principle mode as either a chemical equation or a text description
- **AND** the app MUST preserve student learning event recording for post-learning behavior.

#### Scenario: Student opens point detail before video is ready
- **WHEN** the point has published learning content but no published playable video
- **THEN** the page MUST keep the point content visible where allowed
- **AND** it MUST render a graceful empty video state instead of failing navigation.

#### Scenario: Student opens point detail with missing published content
- **WHEN** the point has no published teacher-authored content
- **THEN** the page MUST avoid displaying draft content, AI-generated point evidence, or search index snippets as body copy
- **AND** it MUST render a controlled unavailable or partial-content state.

#### Scenario: Related experiment link is selected
- **WHEN** a student selects a related experiment link from point detail
- **THEN** the app MUST navigate to the target point detail route with the target experiment id and point key
- **AND** returning MUST preserve route-stack behavior without switching root tab identity.

#### Scenario: Go-test action is selected
- **WHEN** a student taps the go-test action on point detail
- **THEN** the app MUST start the existing assessment flow for the point's experiment chapter or knowledge context
- **AND** the action MUST NOT depend on an admin-authored per-point test URL or label.

#### Scenario: Point detail chat context is created
- **WHEN** a point detail page is open and AI assistant is enabled
- **THEN** the H5 app MUST pass chapter, experiment, point key or point title, and compact page context to student chat requests
- **AND** the assistant backend MUST continue to resolve its own point evidence package separately from the teacher-authored student page body content.
