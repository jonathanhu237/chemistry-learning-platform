## ADDED Requirements

### Requirement: Video library results hand off to learning flow
The student H5 learning flow SHALL allow video-library search and browse results to open existing learning detail pages without changing root tab identity. Normal learning-page tags and cards SHALL continue to navigate directly to their matching learning targets rather than opening the video library.

#### Scenario: Learning page tag opens direct target
- **WHEN** a student selects a tag, chapter card, experiment card, or point card from the learning root or chapter learning page
- **THEN** the app MUST navigate directly to the matching chapter, experiment, or point detail route
- **AND** it MUST NOT open the video library as an intermediate page.

#### Scenario: Student opens point result from video library
- **WHEN** a student selects a video point or experiment-video result from the video library
- **THEN** the app MUST open the existing experiment point/video detail route
- **AND** the route MUST include available experiment, point, profile, chapter, element, property, or knowledge context from the result.

#### Scenario: Student opens chapter experiment result from video library
- **WHEN** a student selects a chapter, element-family, or chapter-experiment result from the video library
- **THEN** the app MUST open the related chapter learning detail route
- **AND** the route MUST preserve source context so back navigation can return to the video library search page.

#### Scenario: Student asks AI from a video-library result
- **WHEN** a student opens AI explanation for a video-library result
- **THEN** the app MUST open the shared AI chat detail page with video, phenomenon, reagent, experiment, or knowledge-point context
- **AND** returning MUST restore the video library page or the detail page that opened AI.

#### Scenario: Student returns from a result detail
- **WHEN** a student returns from a point detail, chapter detail, or AI chat opened from the video library
- **THEN** the app MUST restore the video library route where browser history allows
- **AND** it MUST NOT force the assessment root, learning root, or any experiment root tab.

#### Scenario: Student completes point learning opened from video library
- **WHEN** a student completes learning from a point detail that was opened through the video library
- **THEN** the existing supported completion-to-assessment behavior MAY start an assessment session detail route
- **AND** the completion action MUST NOT change the active root tab identity as a side effect.
